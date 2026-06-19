import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import subprocess
import json
import threading
import re
import sys
import time

# Archivo de debug
DEBUG_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug.log")

def debug_log(msg):
    with open(DEBUG_LOG, "a") as f:
        f.write(f"[{time.time()}] {msg}\n")
    print(msg)

try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ShimejiNexus.MultiAgentHub.v3")
except Exception:
    pass

import sound_manager
import settings_manager
from dotenv import load_dotenv


def _base():
    return os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))


class LauncherPremiumAnime:
    def __init__(self):
        load_dotenv(dotenv_path=os.path.join(_base(), ".env"))
        self.mascotas_activas = {}
        self.personajes_datos = {}
        self.personaje_seleccionado = None
        self.cards = {}
        self.card_thumbs = {}

        self.root = tk.Tk()
        self.root.title("SHIMEJI NEXUS - MULTI-AGENT HUB")
        self.root.geometry("860x600")
        self.root.configure(bg="#0A0A0C")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_cerrar)

        try:
            ruta_icono = os.path.join(_base(), "app_icon.ico")
            if os.path.exists(ruta_icono):
                self.root.iconbitmap(ruta_icono)
        except Exception:
            pass

        self._build_ui()
        self.root.update()

        # Carga inmediata (no lazy)
        try:
            self.escanear_personajes()
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                messagebox.showerror("Error Personajes",
                    f"Error al cargar personajes:\n{e}\n\n"
                    f"Revisa que la carpeta 'personajes' exista\n"
                    f"con subcarpetas y config.json dentro")
            except Exception:
                pass

        threading.Thread(target=sound_manager.asegurar_sonidos, daemon=True).start()
        print(f"DEBUG: {len(self.cards)} personajes cargados")
        print(f"DEBUG: Nombres: {list(self.cards.keys())}")
        
        # Asegurar que la ventana sea visible
        self.root.deiconify()
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(500, lambda: self.root.attributes('-topmost', False))
        
        self.root.after(100, self._iniciar_tray)
        debug_log("DEBUG: Iniciando mainloop")
        self.root.mainloop()

    def _iniciar_tray(self):
        try:
            self.iniciar_tray_icon()
        except Exception as e:
            debug_log(f"Error tray icon: {e}")

    def _estilizar_boton(self, btn, color_normal, color_hover, color_text="#FFFFFF"):
        btn.bind("<Enter>", lambda e: btn.config(bg=color_hover, relief="raised"))
        btn.bind("<Leave>", lambda e: btn.config(bg=color_normal, relief="flat"))
        btn.bind("<ButtonPress-1>", lambda e: btn.config(relief="sunken"))
        btn.bind("<ButtonRelease-1>", lambda e: btn.config(relief="raised"))

    def _procesar_clic_canvas(self, event):
        """Redirigir clics del Canvas a los widgets dentro"""
        x = self.canvas_lista.canvasx(event.x)
        y = self.canvas_lista.canvasy(event.y)
        widget_id = self.canvas_lista.find_overlapping(x, y, x, y)
        if widget_id:
            return "break"
        return "continue"

    def _canvas_clic(self, event):
        """Procesar clic en el Canvas y determinar qué tarjeta fue clickeada"""
        debug_log(f"DEBUG: Canvas recibió clic en ({event.x}, {event.y})")
        
        # Convertir coordenadas del Canvas
        x = self.canvas_lista.canvasx(event.x)
        y = self.canvas_lista.canvasy(event.y)
        debug_log(f"DEBUG: Coordenadas en Canvas: ({x}, {y})")
        
        # Iterar sobre todas las tarjetas (cards)
        for nombre, card_info in self.cards.items():
            card_frame = card_info["frame"]
            
            # Obtener la posición de la tarjeta relativa al window del canvas
            try:
                # La tarjeta está en frame_cards
                card_relativo_y = card_frame.winfo_y() if card_frame.winfo_y() != -1 else 0
                card_relativo_x = card_frame.winfo_x() if card_frame.winfo_x() != -1 else 0
                card_height = card_frame.winfo_height()
                card_width = card_frame.winfo_width()
                
                # Las coordenadas en el canvas ya son relativas al frame_cards
                if (0 <= x <= card_width and 
                    card_relativo_y <= y <= card_relativo_y + card_height):
                    debug_log(f"DEBUG: Clic en tarjeta '{nombre}'")
                    self.seleccionar_personaje(nombre)
                    return "break"
            except Exception as e:
                debug_log(f"DEBUG: Error procesando tarjeta '{nombre}': {e}")
                continue
        
        debug_log(f"DEBUG: Clic no coincidió con ninguna tarjeta")
        return "continue"

    def _build_ui(self):
        # PANEL IZQUIERDO - Lista de personajes con tarjetas
        self.panel_izq = tk.Frame(self.root, bg="#16161D", width=240)
        self.panel_izq.pack(side="left", fill="y", padx=(12, 6), pady=12)
        self.panel_izq.pack_propagate(False)

        # Header con linea decorativa
        header_frame = tk.Frame(self.panel_izq, bg="#16161D")
        header_frame.pack(fill="x", padx=12, pady=(15, 5))
        tk.Label(header_frame, text="PERSONAJES", fg="#FF3366", bg="#16161D", font=("Segoe UI", 10, "bold")).pack()
        tk.Frame(header_frame, bg="#29292E", height=1).pack(fill="x", pady=(6, 0))

        # Canvas + Scrollbar para las tarjetas
        self.canvas_lista = tk.Canvas(self.panel_izq, bg="#16161D", bd=0, highlightthickness=0, cursor="arrow")
        scrollbar = tk.Scrollbar(self.panel_izq, orient="vertical", command=self.canvas_lista.yview)
        self.frame_cards = tk.Frame(self.canvas_lista, bg="#16161D")
        self.frame_cards.bind("<Configure>", lambda e: self.canvas_lista.configure(scrollregion=self.canvas_lista.bbox("all")))
        self.window_id = self.canvas_lista.create_window((0, 0), window=self.frame_cards, anchor="nw", width=220)
        self.canvas_lista.configure(yscrollcommand=scrollbar.set)
        # Propagar el evento de Button-1 del Canvas a los widgets dentro
        self.canvas_lista.bind("<Button-1>", self._canvas_clic)
        self.canvas_lista.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar.pack(side="right", fill="y", pady=8, padx=(0, 8))

        # PANEL DERECHO - Preview y controles
        self.panel_der = tk.Frame(self.root, bg="#0F0F12")
        self.panel_der.pack(side="right", fill="both", expand=True, padx=(6, 12), pady=12)

        # Header del panel derecho
        right_header = tk.Frame(self.panel_der, bg="#0F0F12")
        right_header.pack(fill="x", padx=15, pady=(15, 5))
        self.lbl_nombre_personaje = tk.Label(right_header, text="SELECCIONA UN PERSONAJE", fg="white", bg="#0F0F12", font=("Segoe UI", 15, "bold"))
        self.lbl_nombre_personaje.pack()
        self.lbl_estado = tk.Label(right_header, text="", fg="#4CAF50", bg="#0F0F12", font=("Segoe UI", 8, "bold"))
        self.lbl_estado.pack()

        # Preview con marco decorativo
        preview_frame = tk.Frame(self.panel_der, bg="#16161D", bd=0, highlightbackground="#FF3366", highlightthickness=1)
        preview_frame.pack(pady=(10, 5))
        self.canvas_preview = tk.Canvas(preview_frame, width=180, height=180, bg="#16161D", bd=0, highlightthickness=0)
        self.canvas_preview.pack(padx=4, pady=4)

        # Descripcion
        desc_frame = tk.Frame(self.panel_der, bg="#0F0F12")
        desc_frame.pack(fill="both", expand=True, padx=15, pady=(5, 0))
        self.txt_desc = tk.Text(desc_frame, bg="#16161D", fg="#8C8C9A", bd=0, font=("Segoe UI", 9), wrap="word", height=5, highlightthickness=0, padx=10, pady=8)
        self.txt_desc.insert("1.0", "Toca un personaje de la lista para ver sus detalles.")
        self.txt_desc.config(state="disabled")
        self.txt_desc.pack(fill="both", expand=True)

        # BOTONES
        self.frame_botones = tk.Frame(self.panel_der, bg="#0F0F12")
        self.frame_botones.pack(side="bottom", fill="x", padx=15, pady=(0, 12))

        btns = [
            ("INVOCAR EN PANTALLA", "#FF3366", "#E62E5C", self.lanzar, "disabled", True, 10),
            ("CERRAR ESTA MASCOTA", "#29292E", "#3A3A42", self.cerrar_mascota_seleccionada, "disabled", True, 5),
            ("CERRAR TODAS LAS MASCOTAS", "#29292E", "#3A3A42", self.matar_todos, "normal", False, 5),
            ("+ AGREGAR PERSONAJE", "#1A2E1A", "#2A4A2A", self.abrir_agregar, "normal", False, 5),
            ("CONFIGURACION", "#1E1E24", "#2E2E34", self.abrir_settings, "normal", False, 5),
        ]
        for texto, color, hover, cmd, estado, es_principal, ipady in btns:
            fg = "white" if es_principal else ("#4CAF50" if texto.startswith("+") else "#8C8C9A")
            btn = tk.Button(self.frame_botones, text=texto, bg=color, fg=fg, font=("Segoe UI", 10, "bold" if es_principal else "normal"), bd=0, command=cmd, state=estado, activebackground=hover, activeforeground="white", relief="flat", padx=10)
            btn.pack(fill="x", pady=2, ipady=ipady)
            self._estilizar_boton(btn, color, hover, fg)
            setattr(self, f"_btn_{texto.lower().replace(' ','_').replace('+','')}", btn)

    def _crear_card(self, parent, nombre, thumb):
        card = tk.Frame(parent, bg="#1E1E24", bd=0, highlightbackground="#29292E", highlightthickness=1)
        card.pack(fill="x", padx=4, pady=3)
        # Indicador de estado
        dot = tk.Canvas(card, width=10, height=10, bg="#1E1E24", bd=0, highlightthickness=0)
        dot.pack(side="left", padx=(10, 6), pady=10)
        dot.create_oval(1, 1, 9, 9, fill="#3A3A42", outline="")
        # Thumbnail
        if thumb is not None:
            thumb_label = tk.Label(card, image=thumb, bg="#1E1E24")
            thumb_label.pack(side="left", padx=(0, 8))
            thumb_label.image = thumb  # Mantener referencia
        else:
            # Fallback si no hay thumbnail
            placeholder = tk.Label(card, text="🎭", fg="#666", bg="#1E1E24", font=("Segoe UI", 16))
            placeholder.pack(side="left", padx=(0, 8))
        # Nombre
        lbl = tk.Label(card, text=nombre, fg="#E1E1E6", bg="#1E1E24", font=("Segoe UI", 10), anchor="w")
        lbl.pack(side="left", fill="x", expand=True, pady=10)
        # Flecha
        arrow = tk.Label(card, text=">", fg="#3A3A42", bg="#1E1E24", font=("Segoe UI", 10))
        arrow.pack(side="right", padx=(0, 10))
        # Eventos
        def on_click(e, n=nombre):
            debug_log(f"DEBUG: CLICK detectado en tarjeta de '{n}'")
            try:
                self.seleccionar_personaje(n)
                debug_log(f"DEBUG: seleccionar_personaje('{n}') ejecutado exitosamente")
            except Exception as ex:
                debug_log(f"DEBUG: ERROR en seleccionar_personaje('{n}'): {ex}")
                import traceback
                debug_log(f"Traceback: {traceback.format_exc()}")
        
        for widget in [card, lbl, arrow]:
            widget.bind("<Button-1>", on_click)
            widget.bind("<Enter>", lambda e, c=card: c.config(bg="#25252E", highlightbackground="#FF3366"))
            widget.bind("<Leave>", lambda e, c=card: c.config(bg="#1E1E24", highlightbackground="#29292E"))
            widget.bind("<ButtonPress-1>", lambda e, c=card: c.config(highlightbackground="#E62E5C"))
            widget.bind("<ButtonRelease-1>", lambda e, c=card: c.config(highlightbackground="#FF3366"))
        
        # Vincular también a los hijos que se crearon dentro de la card
        for child in card.winfo_children():
            child.bind("<Button-1>", on_click)
            child.bind("<Enter>", lambda e, c=card: c.config(bg="#25252E", highlightbackground="#FF3366"))
            child.bind("<Leave>", lambda e, c=card: c.config(bg="#1E1E24", highlightbackground="#29292E"))
        
        debug_log(f"DEBUG: Bindings creados para tarjeta '{nombre}'")
        return card, dot, lbl

    def escanear_personajes(self):
        debug_log("DEBUG: Iniciando escaneo de personajes...")
        for w in self.frame_cards.winfo_children():
            w.destroy()
        self.cards.clear()
        self.card_thumbs.clear()
        ruta = os.path.join(_base(), "personajes")
        if not os.path.exists(ruta):
            os.makedirs(ruta)
        debug_log(f"DEBUG: Ruta = {ruta}")
        carpetas = sorted(os.listdir(ruta))
        debug_log(f"DEBUG: Carpetas encontradas = {carpetas}")
        for carpeta in carpetas:
            conf = os.path.join(ruta, carpeta, "config.json")
            if not os.path.isdir(os.path.join(ruta, carpeta)) or not os.path.exists(conf):
                debug_log(f"DEBUG: Saltando {carpeta} (no es dir o no tiene config.json)")
                continue
            debug_log(f"DEBUG: Procesando {carpeta}...")
            with open(conf, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            nombre = data["nombre"]
            debug_log(f"DEBUG: Nombre = {nombre}")
            self.personajes_datos[nombre] = {
                "folder": carpeta, "nombre": nombre,
                "personalidad": data["personalidad"],
                "imagen": data.get("imagen", "rias.png"),
            }
            img_path = os.path.join(ruta, carpeta, self.personajes_datos[nombre]["imagen"])
            debug_log(f"DEBUG: Cargando thumbnail desde {img_path}")
            thumb = self._cargar_thumbnail(img_path)
            self.card_thumbs[nombre] = thumb
            card, dot, _ = self._crear_card(self.frame_cards, nombre, thumb)
            self.cards[nombre] = {"frame": card, "dot": dot}
            debug_log(f"DEBUG: Tarjeta creada para {nombre}")
        debug_log(f"DEBUG: Total de personajes cargados = {len(self.cards)}")
        # Forzar actualización del canvas
        self.frame_cards.update_idletasks()
        self.canvas_lista.configure(scrollregion=self.canvas_lista.bbox("all"))
        
        # Seleccionar el primer personaje automáticamente
        if len(self.personajes_datos) > 0:
            primer_nombre = list(self.personajes_datos.keys())[0]
            debug_log(f"DEBUG: Seleccionando automáticamente el primer personaje: {primer_nombre}")
            self.root.after(100, lambda: self.seleccionar_personaje(primer_nombre))

    def _cargar_thumbnail(self, ruta_img, size=32):
        try:
            if os.path.exists(ruta_img):
                img = Image.open(ruta_img).convert("RGBA")
                # Resize primero para mejorar rendimiento
                img = img.resize((size, size), Image.Resampling.LANCZOS)
                # Hacer blancos transparentes (solo si es necesario)
                if img.mode == "RGBA":
                    data = img.getdata()
                    newData = []
                    for p in data:
                        if p[0] > 240 and p[1] > 240 and p[2] > 240:
                            newData.append((0, 0, 0, 0))
                        else:
                            newData.append(p)
                    img.putdata(newData)
                return ImageTk.PhotoImage(img)
        except Exception as e:
            debug_log(f"Error cargando thumbnail {ruta_img}: {e}")
        return None

    def seleccionar_personaje(self, nombre):
        debug_log(f"DEBUG: seleccionar_personaje llamado con {nombre}")
        self.personaje_seleccionado = nombre
        info = self.personajes_datos[nombre]
        debug_log(f"DEBUG: Info personalidad = {info['personalidad'][:50]}...")
        
        # Resaltar card seleccionada
        for n, c in self.cards.items():
            bg = "#2A2A35" if n == nombre else "#1E1E24"
            hl = "#FF3366" if n == nombre else "#29292E"
            c["frame"].config(bg=bg, highlightbackground=hl)
            for w in c["frame"].winfo_children():
                try:
                    if isinstance(w, (tk.Label, tk.Canvas)):
                        w.config(bg=bg)
                except Exception:
                    pass
            if n == nombre:
                c["frame"].tkraise()
        
        # Actualizar panel derecho
        debug_log(f"DEBUG: Actualizando nombre a: {info['nombre']}")
        self.lbl_nombre_personaje.config(text=info["nombre"])
        
        debug_log(f"DEBUG: Actualizando descripción")
        self.txt_desc.config(state="normal")
        self.txt_desc.delete("1.0", tk.END)
        self.txt_desc.insert("1.0", info["personalidad"])
        self.txt_desc.config(state="disabled")
        
        debug_log(f"DEBUG: Habilitando botón INVOCAR")
        btn_inv = getattr(self, "_btn_invocar_en_pantalla", None)
        if btn_inv:
            debug_log(f"DEBUG: Botón INVOCAR encontrado, habilitando")
            btn_inv.config(state="normal")
        else:
            debug_log(f"DEBUG: ERROR: No se encontró botón INVOCAR")
        
        activa = nombre in self.mascotas_activas
        btn_cerrar = getattr(self, "_btn_cerrar_esta_mascota", None)
        if btn_cerrar:
            btn_cerrar.config(state="normal" if activa else "disabled")
        self.lbl_estado.config(text="● EN PANTALLA" if activa else "", fg="#4CAF50" if activa else "#0F0F12")
        
        # Preview grande
        debug_log(f"DEBUG: Cargando preview para {nombre}")
        ruta_img = os.path.join(_base(), "personajes", info["folder"], info["imagen"])
        debug_log(f"DEBUG: Ruta preview = {ruta_img}")
        if os.path.exists(ruta_img):
            try:
                debug_log(f"DEBUG: Abriendo imagen...")
                img = Image.open(ruta_img).convert("RGBA")
                debug_log(f"DEBUG: Redimensionando...")
                # Resize primero para mejor rendimiento
                img = img.resize((160, 160), Image.Resampling.LANCZOS)
                # Hacer blancos transparentes
                data = img.getdata()
                newData = []
                for p in data:
                    if p[0] > 240 and p[1] > 240 and p[2] > 240:
                        newData.append((0, 0, 0, 0))
                    else:
                        newData.append(p)
                img.putdata(newData)
                debug_log(f"DEBUG: Conviertiendo a PhotoImage...")
                self.img_tk = ImageTk.PhotoImage(img)
                debug_log(f"DEBUG: Dibujando preview en canvas...")
                self.canvas_preview.delete("all")
                self.canvas_preview.create_image(90, 90, image=self.img_tk)
                debug_log(f"DEBUG: Preview actualizado exitosamente")
            except Exception as e:
                debug_log(f"Error en preview: {e}")
                import traceback
                debug_log(f"Traceback: {traceback.format_exc()}")
        else:
            debug_log(f"DEBUG: Archivo no existe: {ruta_img}")
        
        debug_log(f"DEBUG: Llamando actualizar_estados")
        self.actualizar_estados()

    def actualizar_estados(self):
        for nombre, c in self.cards.items():
            activa = nombre in self.mascotas_activas
            color = "#4CAF50" if activa else "#3A3A42"
            c["dot"].delete("all")
            c["dot"].create_oval(1, 1, 9, 9, fill=color, outline="")

    def lanzar(self):
        if not self.personaje_seleccionado:
            return
        item = self.personaje_seleccionado
        info = self.personajes_datos[item]

        if item in self.mascotas_activas:
            messagebox.showinfo("Ya activa", f"{item} ya está en pantalla.")
            return

        folder = info["folder"]
        ruta_envio = os.path.join(_base(), "personajes", folder)
        sound_manager.reproducir("invoke")

        # Cargar posición guardada
        pos_cache = os.path.join(_base(), "pos_cache", f"{info['nombre']}.json")
        pos_data = None
        if os.path.exists(pos_cache):
            try:
                with open(pos_cache, "r", encoding="utf-8") as f:
                    pos_data = json.load(f)
            except Exception:
                pass

        settings = settings_manager.cargar()
        mon = settings.get("monitoreo_ia", True)
        par = settings.get("particulas", True)
        extra_args = {"monitoreo_ia": mon, "particulas": par}

        args = [sys.executable]
        if not getattr(sys, 'frozen', False):
            args.append(os.path.join(_base(), "mascota_motor.py"))
        args.extend([ruta_envio, json.dumps(pos_data) if pos_data else "null", json.dumps(extra_args)])
        self.lbl_estado.config(text="● INVOCANDO...", fg="#FF9800")
        self.root.update_idletasks()
        try:
            proc = subprocess.Popen(args)
            self.mascotas_activas[item] = {"proceso": proc, "folder": folder}
            self.seleccionar_personaje(item)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo invocar a {item}:\n{e}")
            self.lbl_estado.config(text="", fg="#0F0F12")

    def cerrar_mascota_seleccionada(self):
        if not self.personaje_seleccionado:
            return
        self.cerrar_por_nombre(self.personaje_seleccionado)

    def cerrar_por_nombre(self, nombre):
        if nombre not in self.mascotas_activas:
            return
        info = self.mascotas_activas[nombre]
        try:
            proc = info["proceso"]
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=3)
        except Exception:
            try:
                import psutil
                parent = psutil.Process(proc.pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
            except Exception:
                pass
        del self.mascotas_activas[nombre]
        if self.personaje_seleccionado == nombre:
            self.seleccionar_personaje(nombre)  # refresca

    def matar_todos(self):
        for nombre in list(self.mascotas_activas.keys()):
            self.cerrar_por_nombre(nombre)
        sound_manager.reproducir("close")
        messagebox.showinfo("Limpieza", "Todas las mascotas cerradas.")
        if self.personaje_seleccionado:
            self.seleccionar_personaje(self.personaje_seleccionado)

    def abrir_agregar(self):
        AddCharacterWindow(self.root, self)

    def abrir_settings(self):
        SettingsWindow(self.root)

    def iniciar_tray_icon(self):
        try:
            debug_log("DEBUG: Intentando iniciar tray icon...")
            import pystray
            from pystray import MenuItem as Item
            debug_log("DEBUG: pystray importado correctamente")

            img_tray = Image.open(os.path.join(_base(), "app_icon.ico")).resize((64, 64))
            icono = pystray.Icon("shimeji", img_tray, "Shimeji Nexus", menu=pystray.Menu(
                Item("Mostrar Ventana", lambda: self.root.after(0, self.root.deiconify)),
                Item("Salir", lambda: self.root.after(0, self.salir_completo)),
            ))

            def minimizar():
                debug_log("DEBUG: Minimizando a bandeja...")
                self.root.withdraw()
                threading.Thread(target=icono.run, daemon=True).start()

            self.root.protocol("WM_DELETE_WINDOW", minimizar)
            self._tray_icon = icono
            debug_log("DEBUG: Tray icon iniciado exitosamente")
        except ImportError as e:
            debug_log(f"DEBUG: ImportError en tray icon: {e}")
        except Exception as e:
            debug_log(f"DEBUG: Error en tray icon: {e}")
            import traceback
            debug_log(f"Traceback: {traceback.format_exc()}")

    def on_cerrar(self):
        debug_log("DEBUG: on_cerrar llamado")
        # No minimizar aquí - dejar que iniciar_tray lo maneje
        # Para cerrar completamente: self.salir_completo()

    def salir_completo(self):
        self.matar_todos()
        try:
            self._tray_icon.stop()
        except Exception:
            pass
        self.root.quit()
        self.root.destroy()
        os._exit(0)


class SettingsWindow:
    def __init__(self, parent):
        self.parent = parent
        self.win = tk.Toplevel(parent)
        self.win.title("Configuracion")
        self.win.geometry("400x350")
        self.win.configure(bg="#0F0F12")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        self.settings = settings_manager.cargar()

        main_frame = tk.Frame(self.win, bg="#0F0F12")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(main_frame, text="CONFIGURACION GENERAL", fg="#FF3366", bg="#0F0F12", font=("Segoe UI", 13, "bold")).pack(pady=(0, 15))

        self.var_monitoreo = tk.BooleanVar(value=self.settings.get("monitoreo_ia", True))
        self._crear_check(main_frame, "Monitoreo de ventana activa (IA cada 30s)", self.var_monitoreo)

        self.var_particulas = tk.BooleanVar(value=self.settings.get("particulas", True))
        self._crear_check(main_frame, "Efectos de particulas (Aura magica)", self.var_particulas)

        self.var_sonido = tk.BooleanVar(value=self.settings.get("sonido", True))
        self._crear_check(main_frame, "Sonidos de la aplicacion", self.var_sonido)

        # Transparencia
        tk.Label(main_frame, text="Transparencia de mascotas", fg="#E1E1E6", bg="#0F0F12", font=("Segoe UI", 10)).pack(anchor="w", pady=(15, 5))
        self.var_transparencia = tk.DoubleVar(value=self.settings.get("transparencia", 1.0))
        slider = tk.Scale(main_frame, from_=0.3, to=1.0, resolution=0.05, orient="horizontal", variable=self.var_transparencia, bg="#16161D", fg="#E1E1E6", activebackground="#FF3366", troughcolor="#29292E", bd=0, highlightthickness=0)
        slider.pack(fill="x")

        # Velocidad
        tk.Label(main_frame, text="Velocidad de animacion", fg="#E1E1E6", bg="#0F0F12", font=("Segoe UI", 10)).pack(anchor="w", pady=(10, 5))
        self.var_velocidad = tk.DoubleVar(value=self.settings.get("velocidad", 1.0))
        slider_v = tk.Scale(main_frame, from_=0.2, to=3.0, resolution=0.1, orient="horizontal", variable=self.var_velocidad, bg="#16161D", fg="#E1E1E6", activebackground="#FF3366", troughcolor="#29292E", bd=0, highlightthickness=0)
        slider_v.pack(fill="x")

        # Botón guardar
        tk.Button(main_frame, text="GUARDAR CONFIGURACION", bg="#FF3366", fg="white", font=("Segoe UI", 11, "bold"), bd=0, command=self.guardar, activebackground="#E62E5C", activeforeground="white", relief="flat").pack(pady=(20, 5), ipady=6, fill="x")

    def _crear_check(self, parent, texto, variable):
        frame = tk.Frame(parent, bg="#0F0F12")
        frame.pack(fill="x", pady=4)
        cb = tk.Checkbutton(frame, text=texto, variable=variable, bg="#0F0F12", fg="#E1E1E6", selectcolor="#16161D", activebackground="#0F0F12", activeforeground="white", font=("Segoe UI", 10), bd=0)
        cb.pack(anchor="w")

    def guardar(self):
        self.settings["monitoreo_ia"] = self.var_monitoreo.get()
        self.settings["particulas"] = self.var_particulas.get()
        self.settings["sonido"] = self.var_sonido.get()
        self.settings["transparencia"] = self.var_transparencia.get()
        self.settings["velocidad"] = self.var_velocidad.get()
        settings_manager.guardar(self.settings)
        self.win.destroy()


class AddCharacterWindow:
    def __init__(self, parent, launcher):
        self.parent = parent
        self.launcher = launcher
        self.win = tk.Toplevel(parent)
        self.win.title("Agregar Personaje")
        self.win.geometry("520x480")
        self.win.configure(bg="#0F0F12")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        self.rutas_img = {"quieto": "", "caminando": "", "saludo": ""}

        main = tk.Frame(self.win, bg="#0F0F12")
        main.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(main, text="NUEVO PERSONAJE", fg="#FF3366", bg="#0F0F12", font=("Segoe UI", 13, "bold")).pack(pady=(0, 15))

        # Nombre
        tk.Label(main, text="Nombre del personaje:", fg="#E1E1E6", bg="#0F0F12", font=("Segoe UI", 10)).pack(anchor="w")
        self.entry_nombre = tk.Entry(main, bg="#24242D", fg="white", bd=0, insertbackground="white", font=("Segoe UI", 10), highlightthickness=1, highlightbackground="#FF3366")
        self.entry_nombre.pack(fill="x", pady=(0, 10), ipady=4)

        # Anime
        tk.Label(main, text="Anime / Serie (opcional):", fg="#E1E1E6", bg="#0F0F12", font=("Segoe UI", 10)).pack(anchor="w")
        self.entry_anime = tk.Entry(main, bg="#24242D", fg="white", bd=0, insertbackground="white", font=("Segoe UI", 10), highlightthickness=1, highlightbackground="#29292E")
        self.entry_anime.pack(fill="x", pady=(0, 10), ipady=4)

        # Imagenes
        tk.Label(main, text="Imagenes del personaje:", fg="#E1E1E6", bg="#0F0F12", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 5))
        self._crear_selector_img(main, "Quieto (obligatorio)", "quieto")
        self._crear_selector_img(main, "Caminando (opcional)", "caminando")
        self._crear_selector_img(main, "Saludo (opcional)", "saludo")

        # Personalidad
        tk.Label(main, text="Personalidad (opcional):", fg="#E1E1E6", bg="#0F0F12", font=("Segoe UI", 10)).pack(anchor="w", pady=(10, 3))
        self.text_pers = tk.Text(main, height=4, bg="#24242D", fg="#E1E1E6", bd=0, insertbackground="white", font=("Segoe UI", 9), highlightthickness=1, highlightbackground="#29292E")
        self.text_pers.pack(fill="x", pady=(0, 12))
        self.text_pers.insert("1.0", "Actúa como [personaje] de [anime]. Eres un personaje amigable y carismático.")

        # Boton crear
        tk.Button(main, text="CREAR PERSONAJE", bg="#4CAF50", fg="white", font=("Segoe UI", 11, "bold"), bd=0, command=self.crear, activebackground="#3D9140", activeforeground="white", relief="flat").pack(ipady=6, fill="x")

    def _crear_selector_img(self, parent, texto, key):
        f = tk.Frame(parent, bg="#0F0F12")
        f.pack(fill="x", pady=3)
        tk.Label(f, text=texto, fg="#8C8C9A", bg="#0F0F12", font=("Segoe UI", 9), width=22, anchor="w").pack(side="left")
        self.rutas_img[key] = tk.StringVar()
        tk.Label(f, textvariable=self.rutas_img[key], fg="#E1E1E6", bg="#0F0F12", font=("Segoe UI", 8), width=30, anchor="w").pack(side="left", padx=5)
        tk.Button(f, text="...", bg="#29292E", fg="white", bd=0, font=("Segoe UI", 8), command=lambda k=key: self._seleccionar(k), relief="flat", padx=8).pack(side="right")

    def _seleccionar(self, key):
        from tkinter import filedialog
        ruta = filedialog.askopenfilename(title=f"Seleccionar imagen {key}", filetypes=[("PNG", "*.png"), ("Imagenes", "*.png *.jpg *.jpeg")])
        if ruta:
            self.rutas_img[key].set(ruta)

    def crear(self):
        from tkinter import messagebox
        import shutil
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Error", "El nombre es obligatorio.")
            return
        folder = re.sub(r"[^a-z0-9_]", "", nombre.lower().replace(" ", "_"))
        ruta_pj = os.path.join(_base(), "personajes", folder)
        if os.path.exists(ruta_pj):
            messagebox.showwarning("Error", "Ya existe un personaje con ese nombre.")
            return
        quieto_src = self.rutas_img["quieto"].get()
        if not quieto_src or not os.path.exists(quieto_src):
            messagebox.showwarning("Error", "La imagen Quieto es obligatoria.")
            return
        os.makedirs(ruta_pj, exist_ok=True)
        anime = self.entry_anime.get().strip()
        pers_text = self.text_pers.get("1.0", "end-1c").strip()
        if not pers_text or pers_text == "Actúa como [personaje] de [anime]. Eres un personaje amigable y carismático.":
            if anime:
                pers_text = f"Actúa como {nombre} de {anime}. Eres un personaje amigable, carismático y divertido. Hablas con energia y siempre animas al usuario."
            else:
                pers_text = f"Actúa como {nombre}. Eres un personaje amigable, carismático y divertido. Hablas con energia y siempre animas al usuario."
        # Copiar imagenes
        img_names = {}
        for estado, key in [("quieto", "quieto"), ("caminando", "caminando"), ("saludo", "saludo")]:
            src = self.rutas_img[key].get()
            if src and os.path.exists(src):
                ext = os.path.splitext(src)[1] or ".png"
                dst = os.path.join(ruta_pj, f"{estado}{ext}")
                shutil.copy2(src, dst)
                img_names[estado] = f"{estado}{ext}"
        # Crear config
        if "caminando" in img_names or "saludo" in img_names:
            config = {"nombre": nombre, "personalidad": pers_text,
                      "frames": {"quieto": img_names.get("quieto", "quieto.png"),
                                 "caminando": img_names.get("caminando", img_names.get("quieto", "quieto.png")),
                                 "saludo": img_names.get("saludo", img_names.get("quieto", "quieto.png"))},
                      "imagen": img_names.get("quieto", "quieto.png"),
                      "saludo": f"¡Hola! Soy {nombre}~",
                      "color_globo": "#E1E1E6", "color_texto": "#FF3366"}
        else:
            config = {"nombre": nombre, "personalidad": pers_text,
                      "imagen": img_names.get("quieto", "quieto.png"),
                      "saludo": f"¡Hola! Soy {nombre}~",
                      "color_globo": "#E1E1E6", "color_texto": "#FF3366"}
        with open(os.path.join(ruta_pj, "config.json"), "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        messagebox.showinfo("Creado", f"{nombre} agregado correctamente.")
        self.launcher.escanear_personajes()
        self.win.destroy()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--mascota":
        try:
            from mascota_motor import MascotaLogica
        except ImportError as e:
            print(f"Error importando mascota_motor: {e}")
            sys.exit(1)
        import sound_manager
        sound_manager.asegurar_sonidos()
        ruta = sys.argv[2] if len(sys.argv) > 2 else None
        pos = None
        if len(sys.argv) > 3 and sys.argv[3]:
            try:
                parts = sys.argv[3].split(",")
                pos = (int(parts[0]), int(parts[1]))
            except Exception:
                pos = None
        extra = {}
        if len(sys.argv) > 4 and sys.argv[4]:
            try:
                parts = sys.argv[4].split(",")
                extra = {"monitoreo_ia": parts[0] == "true", "particulas": parts[1] == "true"}
            except Exception:
                extra = {}
        if ruta:
            if not os.path.isdir(ruta):
                print(f"ERROR: Ruta no valida: {ruta}")
                sys.exit(1)
            try:
                MascotaLogica(ruta, pos, extra)
            except Exception as e:
                import traceback
                traceback.print_exc()
                try:
                    root = tk.Tk()
                    root.withdraw()
                    root.title("Error")
                    tk.messagebox.showerror("Error Mascota", f"Error al cargar personaje:\n{e}")
                    root.destroy()
                except Exception:
                    pass
                sys.exit(1)
    else:
        LauncherPremiumAnime()
