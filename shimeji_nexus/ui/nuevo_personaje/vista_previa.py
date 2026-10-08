import customtkinter as ctk
from PIL import Image

from shimeji_nexus.core import image_utils
from shimeji_nexus.ui import theme

RASGOS = ("Se mueve por tu escritorio", "Chatea con su personalidad", "Tiene técnica propia")


class VistaPrevia(ctk.CTkFrame):
    """Panel de la derecha: la tarjeta del personaje tal como se vera, con su color, y si ya esta listo."""

    def __init__(self, parent, acento):
        super().__init__(parent, fg_color=theme.PANEL, corner_radius=0, width=290)
        self.pack_propagate(False)
        self.acento = acento
        ctk.CTkLabel(self, text="Vista previa", font=theme.FONT_PIXEL, text_color=theme.ACCENT_2).pack(anchor="w", padx=24, pady=(34, 14))
        self.tarjeta = ctk.CTkFrame(self, fg_color=theme.SURFACE, corner_radius=16, border_width=2, border_color=acento)
        self.tarjeta.pack(fill="x", padx=20)
        self.marco_img = ctk.CTkFrame(self.tarjeta, fg_color=theme.blend_color(acento, theme.BG, 0.13), corner_radius=12, height=170)
        self.marco_img.pack(fill="x", padx=12, pady=(12, 10))
        self.marco_img.pack_propagate(False)
        self.lbl_img = ctk.CTkLabel(self.marco_img, text="Aquí aparecerá tu imagen", font=theme.FONT_CAPTION, text_color=theme.TEXT_DIM)
        self.lbl_img.place(relx=0.5, rely=0.5, anchor="center")
        self.lbl_nombre = ctk.CTkLabel(self.tarjeta, text="", font=theme.FONT_HEADING, text_color=theme.TEXT, wraplength=230, anchor="w", justify="left")
        self.lbl_nombre.pack(anchor="w", padx=16)
        self.lbl_serie = ctk.CTkLabel(self.tarjeta, text="", font=theme.FONT_CAPTION_BOLD, text_color=acento, anchor="w")
        self.lbl_serie.pack(anchor="w", padx=16, pady=(0, 14))
        self.pasos = []
        for _ in range(3):
            self.pasos.append(ctk.CTkLabel(self, text="", font=theme.FONT_ROW, anchor="w"))
            self.pasos[-1].pack(anchor="w", padx=24, pady=(14 if not self.pasos[:-1] else 3, 0))
        ctk.CTkLabel(self, text="  ·  ".join(RASGOS), font=theme.FONT_CAPTION, text_color=theme.TEXT_FAINT, anchor="w", justify="left",
                     wraplength=240).pack(anchor="w", padx=24, pady=(22, 0))
        self._foto = None

    def _poner_imagen(self, ruta, es_hoja):
        try:
            if es_hoja:
                img = Image.open(ruta).convert("RGB")
                img.thumbnail((240, 150))
            else:
                img = image_utils.cargar_sprite(ruta, 150)
            self._foto = ctk.CTkImage(img, size=img.size)
            self.lbl_img.configure(image=self._foto, text="")
        except Exception:
            self._foto = None
            self.lbl_img.configure(image=None, text="No se pudo leer la imagen")

    def actualizar(self, nombre, serie, es_hoja, ruta_imagen, pendiente, personalidad=False):
        """`pendiente` es lo que falta ('Ponle un nombre', 'Falta la imagen') o None si ya se puede crear."""
        self.lbl_nombre.configure(text=nombre.strip() or "Sin nombre todavía")
        self.lbl_serie.configure(text=serie.strip().upper())
        if ruta_imagen:
            self._poner_imagen(ruta_imagen, es_hoja)
        else:
            self._foto = None
            self.lbl_img.configure(image=None, text="Aquí aparecerá tu imagen")
        hechos = (bool(nombre.strip()), bool(ruta_imagen), bool(personalidad))
        textos = (("Nombre listo", "Ponle un nombre"), ("Imagen lista", "Sube una imagen"), ("Personalidad lista", "Define cómo habla (opcional)"))
        for etiqueta, hecho, (si, no) in zip(self.pasos, hechos, textos):
            etiqueta.configure(text=("●  " + si) if hecho else ("○  " + no), text_color=theme.SUCCESS if hecho else theme.TEXT_DIM)
        self.tarjeta.configure(border_color=theme.SUCCESS if not pendiente else self.acento)
