from PIL import ImageTk

from shimeji_nexus.ui import emblemas, theme
from shimeji_nexus.ui.formas import contorno_redondeado

TEXTO_W = 290
MARGEN = 36
ALTO_MIN = 92
TIPOS = {"orbitar": "ORBES", "brasas": "ONDA", "espiral": "ESFERA", "rayo": "RAYO", "zoomies": "CARRERA"}


class TarjetaHabilidadMixin:
    """Bajo la descripcion del personaje: su tecnica en una sola tarjeta clicable, con un emblema de los
    colores de su energia, una frase que la describe y 'Ver en accion'."""

    def _crear_tarjeta(self):
        c = self.canvas_hero
        oculto = {"state": "hidden"}
        self._emblemas = {}
        self._t_fondo = c.create_polygon([0] * 24, smooth=True, width=1, **oculto)
        self._t_emblema = c.create_image(0, 0, anchor="nw", **oculto)
        self._t_cap = c.create_text(0, 0, anchor="w", font=theme.FONT_CAPTION_BOLD, **oculto)
        self._t_nombre = c.create_text(0, 0, anchor="nw", font=theme.FONT_HEADING, fill=theme.TEXT, width=TEXTO_W - 112, **oculto)
        self._t_desc = c.create_text(0, 0, anchor="nw", font=theme.FONT_CAPTION, fill=theme.TEXT_DIM, width=TEXTO_W - 112, **oculto)
        self._t_accion = c.create_text(0, 0, anchor="e", text="▶  Ver en acción", font=theme.FONT_CAPTION_BOLD, **oculto)
        for item in (self._t_fondo, self._t_emblema, self._t_cap, self._t_nombre, self._t_desc, self._t_accion):
            c.tag_bind(item, "<Button-1>", lambda e: self._ver_tecnica())
            c.tag_bind(item, "<Enter>", lambda e: self._resaltar_tarjeta(True))
            c.tag_bind(item, "<Leave>", lambda e: self._resaltar_tarjeta(False))

    def _resaltar_tarjeta(self, activa):
        c = self.canvas_hero
        c.configure(cursor="hand2" if activa else "")
        info = self.personajes_datos.get(self.personaje_seleccionado)
        if info:
            c.itemconfig(self._t_fondo, fill=theme.blend_color(info["color_acento"], theme.BG, 0.2 if activa else 0.12))

    def _emblema(self, nombre, forma, colores):
        if nombre not in self._emblemas:
            self._emblemas[nombre] = ImageTk.PhotoImage(emblemas.emblema(forma, colores, 64))
        return self._emblemas[nombre]

    def _poner_tarjeta(self, info, y):
        c = self.canvas_hero
        hab, acento = info["habilidad"], info["color_acento"]
        x1, x2, xt = MARGEN, MARGEN + TEXTO_W, MARGEN + 90
        c.itemconfig(self._t_cap, text=TIPOS.get(hab["forma"], ""), fill=acento, state="normal")
        c.itemconfig(self._t_nombre, text=hab["nombre"], state="normal")
        c.itemconfig(self._t_desc, text=hab["descripcion"], state="normal")
        c.coords(self._t_cap, xt, y + 22)
        c.coords(self._t_nombre, xt, y + 32)
        c.coords(self._t_desc, xt, c.bbox(self._t_nombre)[3] + 2)
        y2 = max(y + 96, c.bbox(self._t_desc)[3] + 38)
        c.coords(self._t_fondo, contorno_redondeado(x1, y, x2, y2, 14))
        c.itemconfig(self._t_fondo, fill=theme.blend_color(acento, theme.BG, 0.12), outline=theme.blend_color(acento, theme.BG, 0.4), state="normal")
        c.coords(self._t_emblema, x1 + 14, y + 16)
        c.itemconfig(self._t_emblema, image=self._emblema(info["nombre"], hab["forma"], hab["colores"]), state="normal")
        c.coords(self._t_accion, x2 - 16, y2 - 18)
        c.itemconfig(self._t_accion, fill=acento, state="normal")
