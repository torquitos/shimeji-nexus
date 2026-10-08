import tkinter as tk

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageTk

from shimeji_nexus.ui import theme

ANCHO = 512
ALTO = 56
HALO = 14
RADIO = 16
K = 3
_FUENTES = ("C:/Windows/Fonts/seguisb.ttf", "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf")


def _fuente(px):
    for ruta in _FUENTES:
        try:
            return ImageFont.truetype(ruta, px)
        except OSError:
            continue
    return ImageFont.load_default()


def _componer(texto, color, check, intensidad):
    """Boton de acento con un halo suave de su color, compuesto sobre theme.BG (Tk no tiene sombras)."""
    w, h = ANCHO + HALO * 2, ALTO + HALO * 2
    base = Image.new("RGB", (w, h), theme.BG)
    caja = (HALO, HALO, HALO + ANCHO - 1, HALO + ALTO - 1)
    if intensidad > 0:
        halo = Image.new("L", (w, h), 0)
        ImageDraw.Draw(halo).rounded_rectangle((caja[0] + 2, caja[1] + 5, caja[2] - 2, caja[3] + 3), radius=RADIO, fill=int(255 * intensidad))
        halo = halo.filter(ImageFilter.GaussianBlur(7))
        base = Image.composite(Image.new("RGB", (w, h), color), base, halo)
    mascara = Image.new("L", (w * K, h * K), 0)
    ImageDraw.Draw(mascara).rounded_rectangle([v * K for v in caja], radius=RADIO * K, fill=255)
    mascara = mascara.resize((w, h), Image.Resampling.LANCZOS)
    base = Image.composite(Image.new("RGB", (w, h), color), base, mascara)

    d = ImageDraw.Draw(base)
    fuente = _fuente(19)
    ancho_t = d.textlength(texto, font=fuente)
    extra = 26 if check else 0
    x = (w - ancho_t - extra) / 2 + extra
    d.text((x, h / 2 - 1), texto, font=fuente, fill=theme.BG, anchor="lm")
    if check:
        cx, cy = x - 16, h / 2
        d.line([(cx - 6, cy), (cx - 2, cy + 5), (cx + 7, cy - 6)], fill=theme.BG, width=3, joint="curve")
    return base


class BotonInvocar(tk.Label):
    """Boton principal de la portada: imagen con el color del personaje y su resplandor."""

    def __init__(self, master, comando):
        super().__init__(master, bd=0, highlightthickness=0, bg=theme.BG, cursor="arrow")
        self._comando = comando
        self._fotos = {}
        self._estado = ("Invocar", theme.ACCENT_DEFAULT, False, False)
        self._encima = False
        self.bind("<Button-1>", self._clic)
        self.bind("<Enter>", lambda e: self._hover(True))
        self.bind("<Leave>", lambda e: self._hover(False))
        self.actualizar(*self._estado)

    def actualizar(self, texto, color, activo=True, check=False):
        self._estado = (texto, color, activo, check)
        self.configure(cursor="hand2" if activo else "arrow")
        self._pintar()

    def _pintar(self):
        texto, color, activo, check = self._estado
        if not activo:
            color, brillo = theme.blend_color(color, theme.BG, 0.35), 0.0
        else:
            brillo = 0.9 if self._encima else 0.65
            if self._encima:
                color = theme.blend_color("#ffffff", color, 0.12)
        clave = (texto, color, check, brillo)
        if clave not in self._fotos:
            self._fotos[clave] = ImageTk.PhotoImage(_componer(texto, color, check, brillo))
        self.configure(image=self._fotos[clave])

    def _hover(self, encima):
        self._encima = encima
        self._pintar()

    def _clic(self, _e):
        if self._estado[2]:
            self._comando()
