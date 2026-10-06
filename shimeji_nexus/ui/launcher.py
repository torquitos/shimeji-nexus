import json
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image, ImageTk

from shimeji_nexus.audio import sound_manager
from shimeji_nexus.core import characters
from shimeji_nexus.core import image_utils
from shimeji_nexus.core import settings as settings_manager
from shimeji_nexus.core.logging_setup import get_logger
from shimeji_nexus.core.paths import base_dir
from shimeji_nexus.ui import preview, theme
from shimeji_nexus.ui.add_character_window import AddCharacterWindow
from shimeji_nexus.ui.settings_window import SettingsWindow

_logger = get_logger("launcher")

ctk.set_appearance_mode("dark")

HERO_W = 690
HERO_H = 620
MARGEN = 36
TEXTO_W = 290
SPRITE_ALTO = 470


def debug_log(msg):
    _logger.debug(msg)


class LauncherPremiumAnime:
    def __init__(self):
        self.mascotas_activas = {}
        self.personajes_datos = {}
        self.personaje_seleccionado = None
        self.cards = {}
        self.card_thumbs = {}
        self.hero_photo = None
        self._sprites = {}

        self.root = ctk.CTk()
        self.root.title("SHIMEJI NEXUS - MULTI-AGENT HUB")
        self.root.geometry("980x720")
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
        # SIDEBAR
        self.sidebar = ctk.CTkFrame(self.root, width=290, fg_color=theme.PANEL, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header.pack(fill="x", padx=22, pady=(26, 20))
        logo = self._cargar_logo()
        if logo:
            ctk.CTkLabel(header, text="", image=logo).pack(side="left", padx=(0, 12))
        col = ctk.CTkFrame(header, fg_color="transparent")
        col.pack(side="left")
        ctk.CTkLabel(col, text="SHIMEJI NEXUS", font=theme.FONT_HEADING, text_color=theme.TEXT, anchor="w").pack(anchor="w")
        self.lbl_contador = ctk.CTkLabel(col, text="Personajes", font=theme.FONT_CAPTION, text_color=theme.TEXT_FAINT, anchor="w")
        self.lbl_contador.pack(anchor="w")

        self.frame_cards = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent", scrollbar_fg_color=theme.PANEL,
            scrollbar_button_color=theme.PANEL, scrollbar_button_hover_color=theme.BORDER)
        self.frame_cards.pack(fill="both", expand=True, padx=(14, 8))

        sidebar_footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        sidebar_footer.pack(fill="x", padx=18, pady=18)
        ctk.CTkButton(
            sidebar_footer, text="\u2699", width=44, height=44, command=self.abrir_settings,
            fg_color="transparent", hover_color=theme.CARD, text_color=theme.TEXT_DIM,
            border_width=1, border_color=theme.BORDER, corner_radius=12, font=theme.FONT_BODY_LARGE,
        ).pack(side="right", padx=(8, 0))
        self._btn_agregar_personaje = ctk.CTkButton(
            sidebar_footer, text="+  Agregar personaje", command=self.abrir_agregar,
            fg_color="transparent", hover_color=theme.CARD, text_color=theme.TEXT_DIM,
            border_width=1, border_color=theme.BORDER, corner_radius=12,
            font=theme.FONT_BODY_MEDIUM, height=44,
        )
        self._btn_agregar_personaje.pack(side="left", fill="x", expand=True)

        # PANEL PRINCIPAL: portada del personaje + botones
        self.main = ctk.CTkFrame(self.root, fg_color=theme.BG, corner_radius=0)
        self.main.pack(side="right", fill="both", expand=True)

        self.frame_botones = ctk.CTkFrame(self.main, fg_color="transparent")
        self.frame_botones.pack(side="bottom", fill="x", padx=36, pady=(14, 28))

        self._btn_invocar_en_pantalla = ctk.CTkButton(
            self.frame_botones, text="Invocar", command=self.lanzar,
            fg_color=theme.ACCENT_DEFAULT, hover_color=theme.blend_color("#ffffff", theme.ACCENT_DEFAULT, 0.15), text_color=theme.BG,
            font=theme.FONT_BUTTON, corner_radius=16, height=56, state="disabled",
        )
        self._btn_invocar_en_pantalla.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self._btn_cerrar_esta_mascota = ctk.CTkButton(
            self.frame_botones, text="Cerrar", width=104, command=self.cerrar_mascota_seleccionada,
            fg_color=theme.CARD, hover_color=theme.CARD_HOVER, text_color=theme.TEXT_SOFT,
            border_width=1, border_color=theme.BORDER, corner_radius=16, height=56,
            font=theme.FONT_BODY_MEDIUM, state="disabled",
        )
        self._btn_cerrar_esta_mascota.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            self.frame_botones, text="Cerrar todas", width=124, command=self.matar_todos,
            fg_color="transparent", hover_color=theme.CARD, text_color=theme.TEXT_DIM,
            border_width=1, border_color=theme.BORDER, corner_radius=16, height=56,
            font=theme.FONT_BODY_MEDIUM,
        ).pack(side="left")

        c = self.canvas_hero = tk.Canvas(self.main, width=HERO_W, height=HERO_H, bg=theme.BG, bd=0, highlightthickness=0)
        c.pack(side="top", anchor="nw")
        self._hero_item = c.create_image(0, 0, anchor="nw")
        self._h_estado = c.create_text(HERO_W - 32, 40, anchor="ne", text="", font=theme.FONT_CAPTION_BOLD, fill=theme.SUCCESS)
        self._h_serie = c.create_text(MARGEN, 44, anchor="nw", text="", font=theme.FONT_CAPTION_BOLD, fill=theme.TEXT_DIM)
        self._h_nombre = c.create_text(MARGEN, 68, anchor="nw", text="Elige un personaje", font=theme.FONT_TITLE, fill=theme.TEXT, width=TEXTO_W)
        self._h_tag = c.create_text(MARGEN, 130, anchor="nw", text="", font=theme.FONT_HEADING, fill=theme.TEXT_DIM, width=TEXTO_W)
        self._h_cap = c.create_text(MARGEN, 190, anchor="nw", text="", font=theme.FONT_CAPTION_BOLD, fill=theme.TEXT_FAINT)
        self._h_desc = c.create_text(MARGEN, 210, anchor="nw", text="", font=theme.FONT_BODY_LARGE, fill=theme.TEXT_SOFT, width=TEXTO_W)

    def _cargar_logo(self):
        ruta = os.path.join(base_dir(), "assets", "logo.png")
        if not os.path.exists(ruta):
            return None
        return ctk.CTkImage(Image.open(ruta), size=(34, 34))

    def _crear_card(self, parent, nombre, thumb, color_acento, color_acento_soft):
        card = ctk.CTkFrame(parent, fg_color=theme.CARD, corner_radius=14, border_width=1, border_color=theme.BORDER_SOFT, height=78)
        card.pack(fill="x", pady=4)
        card.pack_propagate(False)

        barra = ctk.CTkFrame(card, fg_color=color_acento, width=4, corner_radius=2)
        barra.place(x=8, rely=0.2, relheight=0.6)

        holder = ctk.CTkFrame(card, fg_color=color_acento_soft, corner_radius=12, width=58, height=58)
        holder.place(x=22, rely=0.5, anchor="w")
        if thumb is not None:
            thumb_label = tk.Label(holder, image=thumb, bg=color_acento_soft, bd=0)
            thumb_label.image = thumb
        else:
            thumb_label = ctk.CTkLabel(holder, text="?", font=theme.FONT_BODY, text_color=theme.TEXT_FAINT)
        thumb_label.place(relx=0.5, rely=0.5, anchor="center")

        lbl = ctk.CTkLabel(card, text=nombre, font=theme.FONT_BODY_LARGE, text_color=theme.TEXT, anchor="w")
        lbl.place(x=92, rely=0.36, anchor="w")
        estado = ctk.CTkLabel(card, text="", font=theme.FONT_CAPTION, text_color=theme.TEXT_DIM, anchor="w")
        estado.place(x=92, rely=0.68, anchor="w")

        def entrar(_e, n=nombre):
            if n != self.personaje_seleccionado:
                card.configure(fg_color=theme.CARD_HOVER)

        def salir(e, n=nombre):
            bajo = self.root.winfo_containing(e.x_root, e.y_root)
            if bajo is not None and str(bajo).startswith(str(card)):
                return
            if n != self.personaje_seleccionado:
                card.configure(fg_color=theme.CARD)

        for widget in (card, barra, holder, thumb_label, lbl, estado):
            widget.bind("<Button-1>", lambda e, n=nombre: self.seleccionar_personaje(n))
            widget.bind("<Enter>", entrar)
            widget.bind("<Leave>", salir)
        return card, estado

    def escanear_personajes(self):
        inicio = time.time()
        debug_log("DEBUG: Iniciando escaneo de personajes...")
        for w in self.frame_cards.winfo_children():
            w.destroy()
        self.cards.clear()
        self.card_thumbs.clear()
        self._sprites.clear()
        ruta = os.path.join(base_dir(), "personajes")
        self.personajes_datos = characters.escanear(ruta, on_carpeta=lambda c: debug_log(f"DEBUG: Procesando {c}..."))
        debug_log(f"DEBUG: Carpetas encontradas = {sorted(os.listdir(ruta))}")
        self.lbl_contador.configure(text=f"{len(self.personajes_datos)} personajes")
        for nombre, info in self.personajes_datos.items():
            img_path = os.path.join(ruta, info["folder"], info["imagen"])
            thumb = self._cargar_thumbnail(img_path)
            self.card_thumbs[nombre] = thumb
            card, estado = self._crear_card(self.frame_cards, nombre, thumb, info["color_acento"], info["color_acento_soft"])
            self.cards[nombre] = {"frame": card, "estado": estado}
            debug_log(f"DEBUG: Tarjeta creada para {nombre}")
        self.actualizar_estados()
        debug_log(f"DEBUG: Total de personajes cargados = {len(self.cards)} en {time.time() - inicio:.2f}s")
        if len(self.personajes_datos) > 0:
            primer_nombre = list(self.personajes_datos.keys())[0]
            self.root.after(50, lambda: self.seleccionar_personaje(primer_nombre))

    def _cargar_thumbnail(self, ruta_img, size=58):
        try:
            if os.path.exists(ruta_img):
                return ImageTk.PhotoImage(image_utils.cargar_avatar(ruta_img, size))
        except Exception as e:
            debug_log(f"Error cargando thumbnail {ruta_img}: {e}")
        return None

    def _sprite(self, nombre, info):
        if nombre not in self._sprites:
            ruta = os.path.join(base_dir(), "personajes", info["folder"], info["imagen"])
            try:
                self._sprites[nombre] = image_utils.cargar_sprite(ruta, SPRITE_ALTO) if os.path.exists(ruta) else None
            except Exception as e:
                debug_log(f"Error cargando sprite {ruta}: {e}")
                self._sprites[nombre] = None
        return self._sprites[nombre]

    def _acomodar_texto(self, hay_frase):
        c = self.canvas_hero
        y = c.bbox(self._h_nombre)[3] + 10
        c.coords(self._h_tag, MARGEN, y)
        if hay_frase:
            y = c.bbox(self._h_tag)[3]
        y += 26
        c.coords(self._h_cap, MARGEN, y)
        c.coords(self._h_desc, MARGEN, y + 22)

    def seleccionar_personaje(self, nombre):
        debug_log(f"DEBUG: seleccionar_personaje llamado con {nombre}")
        self.personaje_seleccionado = nombre
        info = self.personajes_datos[nombre]
        color_acento = info["color_acento"]
        primer_nombre = nombre.split()[0]

        for n, c in self.cards.items():
            seleccionada = n == nombre
            c["frame"].configure(
                fg_color=theme.CARD_HOVER if seleccionada else theme.CARD,
                border_color=self.personajes_datos[n]["color_acento"] if seleccionada else theme.BORDER_SOFT,
                border_width=2 if seleccionada else 1,
            )

        activa = nombre in self.mascotas_activas
        frase = info.get("saludo") or ""
        c = self.canvas_hero
        c.itemconfig(self._h_serie, text=info["serie"].upper(), fill=color_acento)
        c.itemconfig(self._h_nombre, text=info["nombre"])
        c.itemconfig(self._h_tag, text=f"\u201c{frase}\u201d" if frase else "", fill=color_acento)
        c.itemconfig(self._h_cap, text="PERSONALIDAD")
        c.itemconfig(self._h_desc, text=info["bio"])
        c.itemconfig(self._h_estado, text="\u25cf  EN PANTALLA" if activa else "")
        self._acomodar_texto(bool(frase))

        self._btn_invocar_en_pantalla.configure(
            state="normal", fg_color=color_acento,
            hover_color=theme.blend_color("#ffffff", color_acento, 0.15),
            text="\u2713  En pantalla" if activa else f"Invocar a {primer_nombre}",
        )
        self._btn_cerrar_esta_mascota.configure(state="normal" if activa else "disabled")

        self.hero_photo = ImageTk.PhotoImage(
            preview.componer_hero(self._sprite(nombre, info), color_acento, HERO_W, HERO_H, primer_nombre.upper()))
        c.itemconfig(self._hero_item, image=self.hero_photo)
        self.actualizar_estados()

    def actualizar_estados(self):
        for nombre, c in self.cards.items():
            if nombre in self.mascotas_activas:
                c["estado"].configure(text="\u25cf  En pantalla", text_color=theme.SUCCESS)
            else:
                c["estado"].configure(text=self.personajes_datos[nombre]["serie"] or "Disponible", text_color=theme.TEXT_DIM)

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
