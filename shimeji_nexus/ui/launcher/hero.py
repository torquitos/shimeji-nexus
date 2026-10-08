import os
import tkinter as tk
import tkinter.font as tkfont

import customtkinter as ctk
from PIL import Image, ImageTk

from shimeji_nexus.core import image_utils
from shimeji_nexus.core.paths import base_dir
from shimeji_nexus.ui import preview, theme
from shimeji_nexus.ui.launcher.boton_invocar import BotonInvocar
from shimeji_nexus.ui.launcher.registro import debug_log

HERO_W = 690
HERO_H = 620
MARGEN = 36
TEXTO_W = 290
SPRITE_ALTO = 440
FUNDIDO_PASOS = 7


class HeroMixin:
    """Panel principal: portada del personaje seleccionado y botones de invocar/cerrar."""

    def _build_main(self):
        self.main = ctk.CTkFrame(self.root, fg_color=theme.BG, corner_radius=0)
        self.main.pack(side="right", fill="both", expand=True)

        self.frame_botones = ctk.CTkFrame(self.main, fg_color="transparent")
        self.frame_botones.pack(side="bottom", fill="x", padx=22, pady=(0, 14))

        self._btn_invocar_en_pantalla = BotonInvocar(self.frame_botones, self.lanzar)
        self._btn_invocar_en_pantalla.pack(side="left")

        self._btn_cerrar_esta_mascota = ctk.CTkButton(
            self.frame_botones, text="Cerrar", width=96, command=self.cerrar_mascota_seleccionada,
            fg_color="transparent", hover_color=theme.SURFACE, text_color=theme.TEXT_DIM,
            corner_radius=16, height=56, font=theme.FONT_BODY_MEDIUM, state="disabled",
        )
        self._btn_cerrar_esta_mascota.pack(side="left", padx=(4, 0))

        c = self.canvas_hero = tk.Canvas(self.main, width=HERO_W, height=HERO_H, bg=theme.BG, bd=0, highlightthickness=0)
        c.pack(side="top", anchor="nw")
        self._hero_item = c.create_image(0, 0, anchor="nw")
        self._hero_sprite = c.create_image(0, 0, anchor="nw")
        self._h_estado = c.create_text(HERO_W - 32, 40, anchor="ne", text="", font=theme.FONT_CAPTION_BOLD, fill=theme.SUCCESS)
        self._h_serie = c.create_text(MARGEN, 44, anchor="nw", text="", font=theme.FONT_CAPTION_BOLD, fill=theme.TEXT_DIM)
        self._h_nombre = c.create_text(MARGEN, 68, anchor="nw", text="Elige un personaje", font=theme.FONT_TITLE, fill=theme.TEXT, width=TEXTO_W + 12)
        self._h_tag = c.create_text(MARGEN, 130, anchor="nw", text="", font=theme.FONT_HEADING, fill=theme.TEXT_DIM, width=TEXTO_W)
        self._h_cap = c.create_text(MARGEN, 190, anchor="nw", text="", font=theme.FONT_ROW, fill=theme.TEXT_DIM)
        self._h_desc = c.create_text(MARGEN, 210, anchor="nw", text="", font=theme.FONT_BODY_LARGE, fill="#c8c8d4", width=TEXTO_W)
        self._crear_tarjeta()

    def _fuente_nombre(self, info):
        """Fuente propia del personaje para su nombre; si Windows no la tiene, la de la app."""
        if not hasattr(self, "_familias"):
            self._familias = set(tkfont.families(self.root))
        fam = info.get("fuente") or ""
        if fam not in self._familias:
            return theme.FONT_TITLE
        for tam in range(28, 17, -1):
            if tkfont.Font(family=fam, size=tam).measure(info["nombre"]) <= TEXTO_W + 12:
                break
        return (fam, tam)

    def _sprite(self, nombre, info):
        if nombre not in self._sprites:
            ruta = os.path.join(base_dir(), "personajes", info["folder"], info["imagen"])
            try:
                self._sprites[nombre] = image_utils.cargar_sprite(ruta, SPRITE_ALTO) if os.path.exists(ruta) else None
            except Exception as e:
                debug_log(f"Error cargando sprite {ruta}: {e}")
                self._sprites[nombre] = None
        return self._sprites[nombre]

    def _poner_fondo(self, imagen):
        self._fondo_visible = imagen
        self.hero_photo = ImageTk.PhotoImage(imagen)
        self.canvas_hero.itemconfig(self._hero_item, image=self.hero_photo)

    def _fundir_fondo(self, nuevo):
        """Al cambiar de personaje el fondo se funde con el anterior en vez de saltar."""
        anterior = getattr(self, "_fondo_visible", None)
        self._fundido = getattr(self, "_fundido", 0) + 1
        if anterior is None:
            self._poner_fondo(nuevo)
        else:
            self._fundir_paso(anterior, nuevo, 1, self._fundido)

    def _fundir_paso(self, anterior, nuevo, i, ident):
        if ident != self._fundido:
            return
        k = min(1.0, i / FUNDIDO_PASOS)
        self._poner_fondo(Image.blend(anterior, nuevo, 1 - (1 - k) ** 2))
        if k < 1:
            self.root.after(32, lambda: self._fundir_paso(anterior, nuevo, i + 1, ident))

    def _acomodar_texto(self, hay_frase):
        c = self.canvas_hero
        y = c.bbox(self._h_nombre)[3] + 10
        c.coords(self._h_tag, MARGEN, y)
        if hay_frase:
            y = c.bbox(self._h_tag)[3]
        y += 26
        c.coords(self._h_cap, MARGEN, y)
        c.coords(self._h_desc, MARGEN, y + 22)
        self._poner_tarjeta(self.personajes_datos[self.personaje_seleccionado], c.bbox(self._h_desc)[3] + 22)

    def seleccionar_personaje(self, nombre):
        debug_log(f"DEBUG: seleccionar_personaje llamado con {nombre}")
        self.personaje_seleccionado = nombre
        info = self.personajes_datos[nombre]
        color_acento = info["color_acento"]
        primer_nombre = nombre.split()[0]

        for n, c in self.cards.items():
            seleccionada = n == nombre
            c["frame"].configure(
                fg_color=theme.SURFACE_SELECTED if seleccionada else theme.PANEL,
                border_width=1 if seleccionada else 0,
                border_color=theme.blend_color(self.personajes_datos[n]["color_acento"], theme.PANEL, 0.7),
            )

        activa = nombre in self.mascotas_activas
        frase = info.get("saludo") or ""
        c = self.canvas_hero
        c.itemconfig(self._h_serie, text=info["serie"].upper(), fill=color_acento)
        c.itemconfig(self._h_nombre, text=info["nombre"], font=self._fuente_nombre(info))
        c.itemconfig(self._h_tag, text=f"\u201c{frase}\u201d" if frase else "", fill=color_acento)
        c.itemconfig(self._h_cap, text="Personalidad")
        c.itemconfig(self._h_desc, text=info["bio"])
        c.itemconfig(self._h_estado, text="\u25cf  EN PANTALLA" if activa else "")
        self._acomodar_texto(bool(frase))

        self._btn_invocar_en_pantalla.actualizar("En pantalla" if activa else f"Invocar a {primer_nombre}", color_acento, True, activa)
        self._btn_cerrar_esta_mascota.configure(state="normal" if activa else "disabled")

        sprite = self._sprite(nombre, info)
        if nombre not in self._fondos:
            self._fondos[nombre] = preview.componer_hero(sprite, color_acento, HERO_W, HERO_H, primer_nombre.upper(), con_sprite=False)
        self._fundir_fondo(self._fondos[nombre])
        self._poner_sprite_vivo(sprite, info)
        self.actualizar_estados()
