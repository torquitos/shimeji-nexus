import os
import time
import tkinter as tk

import customtkinter as ctk
from PIL import Image, ImageTk

from shimeji_nexus.core import characters
from shimeji_nexus.core import image_utils
from shimeji_nexus.core.paths import base_dir
from shimeji_nexus.ui import theme
from shimeji_nexus.ui.launcher.registro import debug_log



class SidebarMixin:
    """Barra lateral: logo, tarjetas de personajes y botones de agregar/ajustes."""

    def _build_sidebar(self):
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
        ctk.CTkLabel(col, text="Shimeji Nexus", font=theme.FONT_SECTION, text_color=theme.TEXT, anchor="w").pack(anchor="w")
        self.lbl_contador = ctk.CTkLabel(col, text="Personajes", font=theme.FONT_CAPTION, text_color=theme.TEXT_DIM, anchor="w")
        self.lbl_contador.pack(anchor="w")

        self.frame_cards = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent", scrollbar_fg_color=theme.PANEL,
            scrollbar_button_color=theme.PANEL, scrollbar_button_hover_color=theme.BORDER)
        self.frame_cards.pack(fill="both", expand=True, padx=(14, 8))

        fila = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        fila.pack(fill="x", padx=22, pady=(6, 0))
        self._punto = ctk.CTkLabel(fila, text="●", font=("Segoe UI", 10), text_color=theme.TEXT_FAINT, width=14)
        self._punto.pack(side="left")
        self.lbl_activas = ctk.CTkLabel(fila, text="", font=theme.FONT_CAPTION, text_color=theme.TEXT_DIM)
        self.lbl_activas.pack(side="left", padx=(6, 0))
        self._btn_todas = ctk.CTkButton(
            fila, text="Invocar a todas", width=96, height=24, command=self.lanzar_todas, fg_color="transparent", hover_color=theme.SURFACE,
            text_color=theme.ACCENT_BRAND, font=theme.FONT_CAPTION_BOLD, corner_radius=8)
        self._btn_todas.pack(side="right")

        sidebar_footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        sidebar_footer.pack(fill="x", padx=18, pady=18)
        ctk.CTkButton(
            sidebar_footer, text="\u2699", width=40, height=40, command=self.abrir_settings, fg_color=theme.SURFACE_SELECTED,
            hover_color=theme.TRACK, text_color=theme.TEXT_SOFT, corner_radius=8, font=theme.FONT_BODY_LARGE,
        ).pack(side="right", padx=(8, 0))
        self._btn_agregar_personaje = ctk.CTkButton(
            sidebar_footer, text="+  Agregar personaje", command=self.abrir_agregar, fg_color=theme.SURFACE_SELECTED,
            hover_color=theme.TRACK, text_color=theme.TEXT_SOFT, corner_radius=8, font=theme.FONT_ROW, height=40,
        )
        self._btn_agregar_personaje.pack(side="left", fill="x", expand=True)

    def _cargar_logo(self):
        ruta = os.path.join(base_dir(), "assets", "logo.png")
        if not os.path.exists(ruta):
            return None
        return ctk.CTkImage(Image.open(ruta), size=(34, 34))

    def _crear_card(self, parent, nombre, thumb, color_acento, color_acento_soft):
        card = ctk.CTkFrame(parent, fg_color=theme.PANEL, corner_radius=10, border_width=0, height=76)
        card.pack(fill="x", pady=4)
        card.pack_propagate(False)

        barra = ctk.CTkFrame(card, fg_color=color_acento, width=4, corner_radius=2)
        barra.place(x=8, rely=0.2, relheight=0.6)

        holder = ctk.CTkFrame(card, fg_color=color_acento_soft, corner_radius=12, width=58, height=58,
                          border_width=1, border_color=theme.blend_color(color_acento, theme.PANEL, 0.3))
        holder.place(x=22, rely=0.5, anchor="w")
        if thumb is not None:
            thumb_label = tk.Label(holder, image=thumb, bg=color_acento_soft, bd=0)
            thumb_label.image = thumb
        else:
            thumb_label = ctk.CTkLabel(holder, text="?", font=theme.FONT_BODY, text_color=theme.TEXT_FAINT)
        thumb_label.place(relx=0.5, rely=0.5, anchor="center")

        lbl = ctk.CTkLabel(card, text=nombre, font=theme.FONT_SECTION, text_color=theme.TEXT, anchor="w")
        lbl.place(x=92, rely=0.36, anchor="w")
        estado = ctk.CTkLabel(card, text="", font=theme.FONT_CAPTION, text_color=theme.TEXT_DIM, anchor="w")
        estado.place(x=92, rely=0.68, anchor="w")

        def entrar(_e, n=nombre):
            if n != self.personaje_seleccionado:
                card.configure(fg_color=theme.SURFACE)

        def salir(e, n=nombre):
            bajo = self.root.winfo_containing(e.x_root, e.y_root)
            if bajo is not None and str(bajo).startswith(str(card)):
                return
            if n != self.personaje_seleccionado:
                card.configure(fg_color=theme.PANEL)

        for widget in (card, barra, holder, thumb_label, lbl, estado):
            widget.bind("<Button-1>", lambda e, n=nombre: self.seleccionar_personaje(n))
            widget.bind("<Enter>", entrar)
            widget.bind("<Leave>", salir)
            try:
                widget.configure(cursor="hand2")
            except Exception:
                pass
        return card, estado

    def escanear_personajes(self):
        inicio = time.time()
        debug_log("DEBUG: Iniciando escaneo de personajes...")
        for w in self.frame_cards.winfo_children():
            w.destroy()
        self.cards.clear()
        self.card_thumbs.clear()
        self._sprites.clear()
        self._fondos.clear()
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

    def actualizar_estados(self):
        for nombre, c in self.cards.items():
            if nombre in self.mascotas_activas:
                c["estado"].configure(text="\u25cf  En pantalla", text_color=theme.SUCCESS)
            else:
                c["estado"].configure(text=self.personajes_datos[nombre]["serie"] or "Disponible", text_color=theme.TEXT_DIM)
        self._actualizar_franja()

    def _actualizar_franja(self):
        n, total = len(self.mascotas_activas), len(self.personajes_datos)
        self._punto.configure(text_color=theme.SUCCESS if n else theme.TEXT_FAINT)
        self.lbl_activas.configure(text=f"{n} en pantalla" if n else "Ninguna en pantalla")
        todas = n == total and total > 0
        self._btn_todas.configure(text="Cerrar todas" if todas else "Invocar a todas", command=self.matar_todos if todas else self.lanzar_todas)
        self._btn_todas.pack(side="right")
