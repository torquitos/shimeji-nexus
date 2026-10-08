from PIL import ImageTk

from shimeji_nexus.ui import preview, theme
from shimeji_nexus.ui.formas import contorno_redondeado

TEXTO_W = 290
MARGEN = 36
ALTO = 108
ALTO_BOTON = 38
TIPOS = {"orbitar": "ORBES", "brasas": "ONDA", "espiral": "ESFERA", "rayo": "RAYO"}


class TarjetaHabilidadMixin:
    """Bajo la descripcion del personaje: su tecnica, con un emblema de los colores de su energia,
    una frase que la describe y un boton para verla en accion."""

    def _crear_tarjeta(self):
        c = self.canvas_hero
        oculto = {"state": "hidden"}
        self._emblemas = {}
        self._t_fondo = c.create_polygon([0] * 24, smooth=True, width=1, **oculto)
        self._t_emblema = c.create_image(0, 0, anchor="nw", **oculto)
        self._t_cap = c.create_text(0, 0, anchor="w", font=theme.FONT_CAPTION_BOLD, **oculto)
        self._t_nombre = c.create_text(0, 0, anchor="w", font=theme.FONT_HEADING, fill=theme.TEXT, width=TEXTO_W - 120, **oculto)
        self._t_desc = c.create_text(0, 0, anchor="nw", font=theme.FONT_CAPTION, fill=theme.TEXT_DIM, width=TEXTO_W - 118, **oculto)
        self._t_boton = c.create_polygon([0] * 24, smooth=True, width=1, **oculto)
        self._t_boton_txt = c.create_text(0, 0, text="▶   VER TÉCNICA", font=theme.FONT_CAPTION_BOLD, **oculto)
        for item in (self._t_boton, self._t_boton_txt):
            c.tag_bind(item, "<Button-1>", lambda e: self._ver_tecnica())
            c.tag_bind(item, "<Enter>", lambda e: c.configure(cursor="hand2"))
            c.tag_bind(item, "<Leave>", lambda e: c.configure(cursor=""))

    def _emblema(self, nombre, colores):
        if nombre not in self._emblemas:
            self._emblemas[nombre] = ImageTk.PhotoImage(preview.emblema(colores))
        return self._emblemas[nombre]

    def _poner_tarjeta(self, info, y):
        c = self.canvas_hero
        hab, acento = info["habilidad"], info["color_acento"]
        x1, x2, y2 = MARGEN, MARGEN + TEXTO_W, y + ALTO
        c.coords(self._t_fondo, contorno_redondeado(x1, y, x2, y2, 16))
        c.itemconfig(self._t_fondo, fill=theme.blend_color(acento, theme.BG, 0.12), outline=theme.blend_color(acento, theme.BG, 0.5), state="normal")
        c.coords(self._t_emblema, x1 + 12, y + (ALTO - 84) // 2)
        c.itemconfig(self._t_emblema, image=self._emblema(info["nombre"], hab["colores"]), state="normal")
        for item, dy in ((self._t_cap, 16), (self._t_nombre, 36)):
            c.coords(item, x1 + 108, y + dy)
            c.itemconfig(item, state="normal")
        c.coords(self._t_desc, x1 + 108, y + 54)
        c.itemconfig(self._t_desc, text=hab["descripcion"], state="normal")
        c.itemconfig(self._t_cap, text=f"TÉCNICA  ·  {TIPOS.get(hab['forma'], '')}", fill=acento)
        c.itemconfig(self._t_nombre, text=hab["nombre"])
        yb = y2 + 12
        c.coords(self._t_boton, contorno_redondeado(x1, yb, x2, yb + ALTO_BOTON, 14))
        c.itemconfig(self._t_boton, fill=theme.blend_color(acento, theme.BG, 0.2), outline=acento, state="normal")
        c.coords(self._t_boton_txt, (x1 + x2) / 2, yb + ALTO_BOTON / 2)
        c.itemconfig(self._t_boton_txt, fill=acento, state="normal")
