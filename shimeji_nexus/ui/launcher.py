import json
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image

from shimeji_nexus.audio import sound_manager
from shimeji_nexus.core import characters
from shimeji_nexus.core import image_utils
from shimeji_nexus.core import settings as settings_manager
from shimeji_nexus.core.logging_setup import get_logger
from shimeji_nexus.core.paths import base_dir
from shimeji_nexus.ui import theme
from shimeji_nexus.ui.add_character_window import AddCharacterWindow
from shimeji_nexus.ui.settings_window import SettingsWindow

_logger = get_logger("launcher")

ctk.set_appearance_mode("dark")


def debug_log(msg):
    _logger.debug(msg)


class LauncherPremiumAnime:
    def __init__(self):
        self.mascotas_activas = {}
        self.personajes_datos = {}
        self.personaje_seleccionado = None
        self.cards = {}
        self.card_thumbs = {}
        self.preview_photo = None

        self.root = ctk.CTk()
        self.root.title("SHIMEJI NEXUS - MULTI-AGENT HUB")
        self.root.geometry("980x660")
        self.root.configure(fg_color=theme.BG)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_cerrar)

        try:
            ruta_icono = os.path.join(base_dir(), "app_icon.ico")
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
        self.root.after(100, self._iniciar_tray)
        self.root.mainloop()

    def _iniciar_tray(self):
        try:
            self.iniciar_tray_icon()
        except Exception as e:
            debug_log(f"Error tray icon: {e}")

    def _build_ui(self):
        # SIDEBAR - Lista de personajes con tarjetas
        self.sidebar = ctk.CTkFrame(self.root, width=280, fg_color=theme.PANEL, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(24, 16))
        ctk.CTkLabel(header_frame, text="SHIMEJI NEXUS", font=(theme.FONT_FAMILY_SEMIBOLD, 14), text_color=theme.TEXT, anchor="w").pack(anchor="w")
        self.lbl_contador = ctk.CTkLabel(header_frame, text="Personajes", font=theme.FONT_CAPTION, text_color=theme.TEXT_FAINT, anchor="w")
        self.lbl_contador.pack(anchor="w", pady=(2, 0))

        self.frame_cards = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.frame_cards.pack(fill="both", expand=True, padx=12)

        sidebar_footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        sidebar_footer.pack(fill="x", padx=16, pady=14)
        self._btn_agregar_personaje = ctk.CTkButton(
            sidebar_footer, text="+  Agregar personaje", command=self.abrir_agregar,
            fg_color="transparent", hover_color=theme.CARD, text_color=theme.TEXT_DIM,
            border_width=1, border_color=theme.BORDER, corner_radius=10,
            font=theme.FONT_CAPTION_BOLD, height=36,
        )
        self._btn_agregar_personaje.pack(fill="x")

        # PANEL PRINCIPAL
        self.main = ctk.CTkFrame(self.root, fg_color=theme.BG, corner_radius=0)
        self.main.pack(side="right", fill="both", expand=True)

        top_bar = ctk.CTkFrame(self.main, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(16, 0))
        ctk.CTkButton(
            top_bar, text="⚙", width=32, height=32, command=self.abrir_settings,
            fg_color=theme.CARD, hover_color=theme.CARD_HOVER, text_color=theme.TEXT_DIM,
            border_width=1, border_color=theme.BORDER, corner_radius=10, font=theme.FONT_BODY,
        ).pack(side="right")

        # Preview con marco decorativo
        self.preview_frame = ctk.CTkFrame(self.main, fg_color=theme.PANEL, corner_radius=18, border_width=1, border_color=theme.BORDER, height=280)
        self.preview_frame.pack(fill="x", padx=32, pady=(8, 0))
        self.preview_frame.pack_propagate(False)

        self.lbl_estado_badge = ctk.CTkLabel(
            self.preview_frame, text="●  En pantalla", font=theme.FONT_CAPTION_BOLD,
            text_color=theme.SUCCESS, fg_color=theme.CARD, corner_radius=100,
        )
        self.canvas_preview = tk.Canvas(self.preview_frame, bg=theme.PANEL, bd=0, highlightthickness=0, width=900, height=280)
        self.canvas_preview.place(relx=0.5, rely=0.5, anchor="center")

        # Info del personaje
        info_zone = ctk.CTkFrame(self.main, fg_color="transparent")
        info_zone.pack(fill="x", padx=32, pady=(18, 0))
        self.lbl_nombre_personaje = ctk.CTkLabel(info_zone, text="SELECCIONA UN PERSONAJE", font=theme.FONT_DISPLAY, text_color=theme.TEXT, anchor="w")
        self.lbl_nombre_personaje.pack(anchor="w")
        self.lbl_tagline = ctk.CTkLabel(info_zone, text="", font=theme.FONT_BODY_MEDIUM, anchor="w")
        self.lbl_tagline.pack(anchor="w", pady=(2, 10))
        self.txt_desc = ctk.CTkLabel(
            info_zone, text="Toca un personaje de la lista para ver sus detalles.",
            font=theme.FONT_BODY, text_color=theme.TEXT_DIM, anchor="w", justify="left",
            wraplength=560,
        )
        self.txt_desc.pack(anchor="w", fill="x")

        # BOTONES
        self.frame_botones = ctk.CTkFrame(self.main, fg_color="transparent")
        self.frame_botones.pack(fill="x", padx=32, pady=(24, 0))

        self._btn_invocar_en_pantalla = ctk.CTkButton(
            self.frame_botones, text="▶  Invocar en pantalla", command=self.lanzar,
            fg_color=theme.ACCENT_DEFAULT, hover_color=theme.blend_color("#ffffff", theme.ACCENT_DEFAULT, 0.15), text_color=theme.BG,
            font=theme.FONT_BODY_MEDIUM, corner_radius=14, height=44, state="disabled",
        )
        self._btn_invocar_en_pantalla.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self._btn_cerrar_esta_mascota = ctk.CTkButton(
            self.frame_botones, text="✕", width=44, command=self.cerrar_mascota_seleccionada,
            fg_color=theme.CARD, hover_color=theme.CARD_HOVER, text_color=theme.TEXT_DIM,
            border_width=1, border_color=theme.BORDER, corner_radius=14, height=44,
            font=theme.FONT_BODY, state="disabled",
        )
        self._btn_cerrar_esta_mascota.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            self.frame_botones, text="Cerrar todas", command=self.matar_todos,
            fg_color="transparent", hover_color=theme.CARD, text_color=theme.TEXT_FAINT,
            border_width=1, border_color=theme.BORDER, corner_radius=14, height=44,
            font=theme.FONT_CAPTION_BOLD,
        ).pack(side="left")

        # Footer con icono de configuracion, para llenar el espacio inferior
        footer = ctk.CTkFrame(self.main, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=32, pady=(0, 20))
        ctk.CTkLabel(footer, text="Shimeji Nexus", font=theme.FONT_CAPTION, text_color=theme.TEXT_FAINT).pack(side="left")

    def _crear_card(self, parent, nombre, thumb, color_acento, color_acento_soft):
        card = ctk.CTkFrame(parent, fg_color=theme.CARD, corner_radius=12, border_width=1, border_color=theme.BORDER_SOFT, height=64)
        card.pack(fill="x", pady=3)
        card.pack_propagate(False)

        accent_bar = ctk.CTkFrame(card, fg_color=color_acento, width=3, corner_radius=2)
        accent_bar.place(x=6, rely=0.18, relheight=0.64)

        thumb_holder = ctk.CTkFrame(card, fg_color=color_acento_soft, corner_radius=10, width=44, height=44)
        thumb_holder.place(x=16, rely=0.5, anchor="w")
        if thumb is not None:
            thumb_label = tk.Label(thumb_holder, image=thumb, bg=color_acento_soft, bd=0)
            thumb_label.image = thumb
            thumb_label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            thumb_label = ctk.CTkLabel(thumb_holder, text="🎭", font=theme.FONT_BODY, text_color=theme.TEXT_FAINT)
            thumb_label.place(relx=0.5, rely=0.5, anchor="center")

        lbl = ctk.CTkLabel(card, text=nombre, font=theme.FONT_BODY_MEDIUM, text_color=theme.TEXT, anchor="w")
        lbl.place(x=72, rely=0.5, anchor="w")

        dot = tk.Canvas(card, width=8, height=8, bg=theme.CARD, bd=0, highlightthickness=0)
        dot.place(relx=1.0, x=-16, rely=0.5, anchor="e")
        dot.create_oval(1, 1, 7, 7, fill=theme.TEXT_FAINT, outline="")

        for widget in (card, thumb_holder, thumb_label, lbl):
            widget.bind("<Button-1>", lambda e, n=nombre: self.seleccionar_personaje(n))
        return card, dot

    def escanear_personajes(self):
        debug_log("DEBUG: Iniciando escaneo de personajes...")
        for w in self.frame_cards.winfo_children():
            w.destroy()
        self.cards.clear()
        self.card_thumbs.clear()
        ruta = os.path.join(base_dir(), "personajes")
        self.personajes_datos = characters.escanear(ruta, on_carpeta=lambda c: debug_log(f"DEBUG: Procesando {c}..."))
        debug_log(f"DEBUG: Carpetas encontradas = {sorted(os.listdir(ruta))}")
        self.lbl_contador.configure(text=f"Personajes · {len(self.personajes_datos)}")
        for nombre, info in self.personajes_datos.items():
            debug_log(f"DEBUG: Nombre = {nombre}")
            img_path = os.path.join(ruta, info["folder"], info["imagen"])
            debug_log(f"DEBUG: Cargando thumbnail desde {img_path}")
            thumb = self._cargar_thumbnail(img_path)
            self.card_thumbs[nombre] = thumb
            card, dot = self._crear_card(self.frame_cards, nombre, thumb, info["color_acento"], info["color_acento_soft"])
            self.cards[nombre] = {"frame": card, "dot": dot}
            debug_log(f"DEBUG: Tarjeta creada para {nombre}")
        debug_log(f"DEBUG: Total de personajes cargados = {len(self.cards)}")
        if len(self.personajes_datos) > 0:
            primer_nombre = list(self.personajes_datos.keys())[0]
            debug_log(f"DEBUG: Seleccionando automáticamente el primer personaje: {primer_nombre}")
            self.root.after(100, lambda: self.seleccionar_personaje(primer_nombre))

    def _cargar_thumbnail(self, ruta_img, size=44):
        try:
            if os.path.exists(ruta_img):
                img = image_utils.cargar_con_transparencia(ruta_img, size)
                return self._to_photoimage(img)
        except Exception as e:
            debug_log(f"Error cargando thumbnail {ruta_img}: {e}")
        return None

    def _to_photoimage(self, img):
        from PIL import ImageTk
        return ImageTk.PhotoImage(img)

    def seleccionar_personaje(self, nombre):
        debug_log(f"DEBUG: seleccionar_personaje llamado con {nombre}")
        self.personaje_seleccionado = nombre
        info = self.personajes_datos[nombre]
        color_acento = info["color_acento"]

        for n, c in self.cards.items():
            seleccionada = n == nombre
            c["frame"].configure(
                fg_color=theme.CARD_HOVER if seleccionada else theme.CARD,
                border_color=self.personajes_datos[n]["color_acento"] if seleccionada else theme.BORDER_SOFT,
            )

        self.lbl_nombre_personaje.configure(text=info["nombre"])
        self.lbl_tagline.configure(text=info["folder"].upper(), text_color=color_acento)
        self.txt_desc.configure(text=info["personalidad"])
        self._btn_invocar_en_pantalla.configure(
            state="normal", fg_color=color_acento,
            hover_color=theme.blend_color("#ffffff", color_acento, 0.15),
        )

        activa = nombre in self.mascotas_activas
        self._btn_cerrar_esta_mascota.configure(state="normal" if activa else "disabled")
        if activa:
            self.lbl_estado_badge.place(x=16, y=16)
        else:
            self.lbl_estado_badge.place_forget()

        self._dibujar_fondo_preview(color_acento)

        ruta_img = os.path.join(base_dir(), "personajes", info["folder"], info["imagen"])
        if os.path.exists(ruta_img):
            try:
                img = image_utils.cargar_con_transparencia(ruta_img, 240)
                self.preview_photo = self._to_photoimage(img)
                self.canvas_preview.create_image(450, 140, image=self.preview_photo)
            except Exception as e:
                debug_log(f"Error en preview: {e}")
        self.actualizar_estados()

    def _dibujar_fondo_preview(self, color_acento):
        """Dibuja un gradiente radial sutil (con anillos concentricos) sobre
        el color base del panel, tintado con el acento del personaje."""
        c = self.canvas_preview
        c.delete("all")
        cx, cy = 450, 140
        max_r = 340
        pasos = 14
        for i in range(pasos, 0, -1):
            frac = i / pasos
            r = max_r * frac
            porcentaje = 0.22 * (1 - frac) ** 2
            color = theme.blend_color(color_acento, theme.PANEL, porcentaje)
            c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="")

    def actualizar_estados(self):
        for nombre, c in self.cards.items():
            activa = nombre in self.mascotas_activas
            color = theme.SUCCESS if activa else theme.TEXT_FAINT
            c["dot"].delete("all")
            c["dot"].create_oval(1, 1, 7, 7, fill=color, outline="")

    def lanzar(self):
        if not self.personaje_seleccionado:
            return
        item = self.personaje_seleccionado
        info = self.personajes_datos[item]

        if item in self.mascotas_activas:
            messagebox.showinfo("Ya activa", f"{item} ya está en pantalla.")
            return

        folder = info["folder"]
        ruta_envio = os.path.join(base_dir(), "personajes", folder)
        sound_manager.reproducir("invoke")

        pos_cache = os.path.join(base_dir(), "pos_cache", f"{info['nombre']}.json")
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
            args.append(os.path.join(base_dir(), "mascota_motor.py"))
        args.extend([ruta_envio, json.dumps(pos_data) if pos_data else "null", json.dumps(extra_args)])
        self.root.update_idletasks()
        try:
            proc = subprocess.Popen(args)
            self.mascotas_activas[item] = {"proceso": proc, "folder": folder}
            self.seleccionar_personaje(item)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo invocar a {item}:\n{e}")

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
            self.seleccionar_personaje(nombre)

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

            img_tray = Image.open(os.path.join(base_dir(), "app_icon.ico")).resize((64, 64))
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
