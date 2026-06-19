import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import subprocess
import json
import threading
import re
import sys

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

        # Carga perezosa: sonidos en hilo, personajes + tray despues de mostrar ventana
        threading.Thread(target=sound_manager.asegurar_sonidos, daemon=True).start()
        self.root.after(200, self._carga_tardia)
        self.root.mainloop()

    def _carga_tardia(self):
        try:
            self.escanear_personajes()
        except Exception as e:
            print(f"Error escaneando personajes: {e}")
        try:
            self.iniciar_tray_icon()
        except Exception as e:
            print(f"Error tray icon: {e}")

    def _estilizar_boton(self, btn, color_normal, color_hover, color_text="#FFFFFF"):
        btn.bind("<Enter>", lambda e: btn.config(bg=color_hover, relief="raised"))
        btn.bind("<Leave>", lambda e: btn.config(bg=color_normal, relief="flat"))
        btn.bind("<ButtonPress-1>", lambda e: btn.config(relief="sunken"))
        btn.bind("<ButtonRelease-1>", lambda e: btn.config(relief="raised"))

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
        self.canvas_lista = tk.Canvas(self.panel_izq, bg="#16161D", bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.panel_izq, orient="vertical", command=self.canvas_lista.yview)
        self.frame_cards = tk.Frame(self.canvas_lista, bg="#16161D")
        self.frame_cards.bind("<Configure>", lambda e: self.canvas_lista.configure(scrollregion=self.canvas_lista.bbox("all")))
        self.canvas_lista.create_window((0, 0), window=self.frame_cards, anchor="nw", width=220)
        self.canvas_lista.configure(yscrollcommand=scrollbar.set)
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
        thumb_label = tk.Label(card, image=thumb, bg="#1E1E24")
        thumb_label.pack(side="left", padx=(0, 8))
        # Nombre
        lbl = tk.Label(card, text=nombre, fg="#E1E1E6", bg="#1E1E24", font=("Segoe UI", 10), anchor="w")
        lbl.pack(side="left", fill="x", expand=True, pady=10)
        # Flecha
        arrow = tk.Label(card, text=">", fg="#3A3A42", bg="#1E1E24", font=("Segoe UI", 10))
        arrow.pack(side="right", padx=(0, 10))
        # Eventos
        for widget in [card, lbl, arrow]:
            widget.bind("<Button-1>", lambda e, n=nombre: self.seleccionar_personaje(n))
            widget.bind("<Enter>", lambda e, c=card: c.config(bg="#25252E", highlightbackground="#FF3366"))
            widget.bind("<Leave>", lambda e, c=card: c.config(bg="#1E1E24", highlightbackground="#29292E"))
            widget.bind("<ButtonPress-1>", lambda e, c=card: c.config(highlightbackground="#E62E5C"))
            widget.bind("<ButtonRelease-1>", lambda e, c=card: c.config(highlightbackground="#FF3366"))
        return card, dot, lbl

    def escanear_personajes(self):
        for w in self.frame_cards.winfo_children():
            w.destroy()
        self.cards.clear()
        self.card_thumbs.clear()
        ruta = os.path.join(_base(), "personajes")
        if not os.path.exists(ruta):
            os.makedirs(ruta)
        for carpeta in sorted(os.listdir(ruta)):
            conf = os.path.join(ruta, carpeta, "config.json")
            if not os.path.isdir(os.path.join(ruta, carpeta)) or not os.path.exists(conf):
                continue
            with open(conf, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            nombre = data["nombre"]
            self.personajes_datos[nombre] = {
                "folder": carpeta, "nombre": nombre,
                "personalidad": data["personalidad"],
                "imagen": data.get("imagen", "rias.png"),
            }
            thumb = self._cargar_thumbnail(os.path.join(ruta, carpeta, self.personajes_datos[nombre]["imagen"]))
            self.card_thumbs[nombre] = thumb
            card, dot, _ = self._crear_card(self.frame_cards, nombre, thumb)
            self.cards[nombre] = {"frame": card, "dot": dot}

    def _cargar_thumbnail(self, ruta_img, size=32):
        try:
            if os.path.exists(ruta_img):
                img = Image.open(ruta_img).convert("RGBA")
                if not any(p[3] < 255 for p in img.getdata()):
                    datas = list(img.getdata())
                    newData = [(0, 0, 0, 0) if (p[0] > 240 and p[1] > 240 and p[2] > 240) else p for p in datas]
                    img.putdata(newData)
                img = img.resize((size, size), Image.Resampling.NEAREST)
                return ImageTk.PhotoImage(img)
        except Exception:
            pass
        return None

    def seleccionar_personaje(self, nombre):
        self.personaje_seleccionado = nombre
        info = self.personajes_datos[nombre]
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
        self.lbl_nombre_personaje.config(text=info["nombre"])
        self.txt_desc.config(state="normal")
        self.txt_desc.delete("1.0", tk.END)
        self.txt_desc.insert("1.0", info["personalidad"])
        self.txt_desc.config(state="disabled")
        btn_inv = getattr(self, "_btn_invocar_en_pantalla", None)
        if btn_inv:
            btn_inv.config(state="normal")
        activa = nombre in self.mascotas_activas
        btn_cerrar = getattr(self, "_btn_cerrar_esta_mascota", None)
        if btn_cerrar:
            btn_cerrar.config(state="normal" if activa else "disabled")
        self.lbl_estado.config(text="● EN PANTALLA" if activa else "", fg="#4CAF50" if activa else "#0F0F12")
        # Preview grande
        ruta_img = os.path.join(_base(), "personajes", info["folder"], info["imagen"])
        if os.path.exists(ruta_img):
            try:
                img = Image.open(ruta_img).convert("RGBA")
                if not any(p[3] < 255 for p in img.getdata()):
                    datas = list(img.getdata())
                    newData = [(0, 0, 0, 0) if (p[0] > 240 and p[1] > 240 and p[2] > 240) else p for p in datas]
                    img.putdata(newData)
                img = img.resize((160, 160), Image.Resampling.NEAREST)
                self.img_tk = ImageTk.PhotoImage(img)
                self.canvas_preview.delete("all")
                self.canvas_preview.create_image(90, 90, image=self.img_tk)
            except Exception as e:
                print(e)
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
        pos_args = ""
        if os.path.exists(pos_cache):
            try:
                with open(pos_cache, "r", encoding="utf-8") as f:
                    pos_data = json.load(f)
                    pos_args = f"{pos_data['x']},{pos_data['y']}"
            except Exception:
                pass

        settings = settings_manager.cargar()
        mon = str(settings.get("monitoreo_ia", True)).lower()
        par = str(settings.get("particulas", True)).lower()
        extra_args = f"{mon},{par}"

        args = [sys.executable]
        if not getattr(sys, 'frozen', False):
            args.append(os.path.abspath(__file__))
        args.extend(["--mascota", ruta_envio, pos_args, extra_args])
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
            import pystray
            from pystray import MenuItem as Item

            img_tray = Image.open(os.path.join(_base(), "app_icon.ico")).resize((64, 64))
            icono = pystray.Icon("shimeji", img_tray, "Shimeji Nexus", menu=pystray.Menu(
                Item("Mostrar Ventana", lambda: self.root.after(0, self.root.deiconify)),
                Item("Salir", lambda: self.root.after(0, self.salir_completo)),
            ))

            def minimizar():
                self.root.withdraw()
                threading.Thread(target=icono.run, daemon=True).start()

            self.root.protocol("WM_DELETE_WINDOW", minimizar)
            self._tray_icon = icono
        except ImportError:
            pass

    def on_cerrar(self):
        self.root.withdraw()

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
