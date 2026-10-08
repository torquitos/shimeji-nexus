"""Emblemas de tecnica: un icono por forma de energia, dibujado 4x con PIL y reducido con LANCZOS."""
import math

from PIL import Image, ImageChops, ImageDraw, ImageFilter

K = 4


def _brillo(n, color, cx, cy, radio, fuerza, curva=1.6):
    """Capa RGBA con un halo radial del color dado."""
    g = Image.radial_gradient("L").resize((radio * 2, radio * 2), Image.Resampling.BICUBIC)
    g = g.point(lambda v: int(255 * fuerza * ((255 - v) / 255) ** curva))
    mascara = Image.new("L", (n, n), 0)
    mascara.paste(g, (int(cx - radio), int(cy - radio)))
    capa = Image.new("RGBA", (n, n), color)
    capa.putalpha(mascara)
    return capa


def _disco(img, cx, cy, r, color, borde=None, ancho=0):
    ImageDraw.Draw(img).ellipse((cx - r, cy - r, cx + r, cy + r), fill=color, outline=borde, width=ancho)


def _desenfocar(capa, radio):
    return capa.filter(ImageFilter.GaussianBlur(radio))


def _orbitar(img, n, c):
    """Vacio purpura: esfera oscura con nucleo violeta y dos orbes (azul y rojo) en orbita."""
    m = n / 2
    img.alpha_composite(_brillo(n, c[1], m, m, int(n * 0.48), 0.8))
    _disco(img, m, m, n * 0.20, "#1a0b33", c[1], 2 * K)
    _disco(img, m, m, n * 0.12, "#05020d")
    d = ImageDraw.Draw(img)
    d.ellipse((m - n * 0.36, m - n * 0.36, m + n * 0.36, m + n * 0.36), outline=c[1] + "88" if len(c[1]) == 7 else c[1], width=K)
    for ang, col in ((-0.6, "#4aa8ff"), (math.pi - 0.6, "#ff4a5a")):
        x, y = m + n * 0.36 * math.cos(ang), m + n * 0.36 * math.sin(ang)
        img.alpha_composite(_brillo(n, col, x, y, int(n * 0.2), 0.9))
        _disco(img, x, y, n * 0.075, col, "#ffffff", K)


def _brasas(img, n, c):
    """Poder de la Destruccion: agujero negro con anillo de acrecion carmesi."""
    m = n / 2
    img.alpha_composite(_brillo(n, c[0], m, m, int(n * 0.5), 0.85, 1.3))
    anillo = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    ImageDraw.Draw(anillo).ellipse((m - n * 0.33, m - n * 0.33, m + n * 0.33, m + n * 0.33), outline=c[1], width=int(n * 0.07))
    img.alpha_composite(_desenfocar(anillo, K * 2.2))
    d = ImageDraw.Draw(img)
    d.ellipse((m - n * 0.30, m - n * 0.30, m + n * 0.30, m + n * 0.30), outline=c[0], width=int(n * 0.06))
    d.ellipse((m - n * 0.255, m - n * 0.255, m + n * 0.255, m + n * 0.255), outline="#ffd6cc", width=K)
    _disco(img, m, m, n * 0.235, "#060104")
    for ang in (0.5, 2.4, 4.1):
        _disco(img, m + n * 0.40 * math.cos(ang), m + n * 0.40 * math.sin(ang), n * 0.018, c[1])


def _espiral(img, n, c):
    """Rasengan: esfera azul con espirales blancas."""
    m = n / 2
    img.alpha_composite(_brillo(n, c[0], m, m, int(n * 0.5), 0.9))
    _disco(img, m, m, n * 0.36, c[2], c[1], 2 * K)
    _disco(img, m, m, n * 0.30, c[0])
    d = ImageDraw.Draw(img)
    for fase in (0, math.pi * 2 / 3, math.pi * 4 / 3):
        pts = []
        for i in range(60):
            t = i / 59
            ang = fase + t * 4.2
            r = n * (0.04 + 0.30 * t)
            pts.append((m + r * math.cos(ang), m + r * math.sin(ang)))
        d.line(pts, fill="#ffffff", width=int(n * 0.035), joint="curve")
    _disco(img, m, m, n * 0.05, "#ffffff")


def _corazon(img, x, y, r, color):
    d = ImageDraw.Draw(img)
    d.ellipse((x - r, y - r * 0.9, x, y + r * 0.1), fill=color)
    d.ellipse((x, y - r * 0.9, x + r, y + r * 0.1), fill=color)
    d.polygon([(x - r, y - r * 0.25), (x + r, y - r * 0.25), (x, y + r * 1.0)], fill=color)


def _rayo(img, n, c):
    """Rayo de la Cola: estrella rosa-violeta con haz y corazoncitos."""
    m = n / 2
    img.alpha_composite(_brillo(n, c[2], m, m, int(n * 0.5), 0.9))
    haz = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    ImageDraw.Draw(haz).line([(n * 0.14, n * 0.86), (n * 0.86, n * 0.14)], fill=c[0], width=int(n * 0.07))
    img.alpha_composite(_desenfocar(haz, K * 2.5))
    d = ImageDraw.Draw(img)
    pts = []
    for i in range(10):
        r = n * (0.34 if i % 2 == 0 else 0.14)
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((m + r * math.cos(a), m + r * math.sin(a)))
    d.polygon(pts, fill=c[0], outline=c[1])
    _disco(img, m, m, n * 0.07, "#ffffff")
    _corazon(img, n * 0.22, n * 0.26, n * 0.07, c[1])
    _corazon(img, n * 0.80, n * 0.76, n * 0.06, c[0])


_FORMAS = {"orbitar": _orbitar, "brasas": _brasas, "espiral": _espiral, "rayo": _rayo}


def _generico(img, n, c):
    m = n / 2
    img.alpha_composite(_brillo(n, c[0], m, m, int(n * 0.5), 0.8))
    for r, col in ((0.34, c[0]), (0.22, c[1]), (0.1, "#ffffff")):
        _disco(img, m, m, n * r, col)


def emblema(forma, colores, tam=64):
    """Icono de app (cuadrado de esquinas redondeadas oscuro) con la energia de la tecnica."""
    n = tam * K
    fondo = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    ImageDraw.Draw(fondo).rounded_rectangle((0, 0, n - 1, n - 1), radius=int(n * 0.24), fill="#0a0a10")
    arte = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    _FORMAS.get(forma, _generico)(arte, n, colores)
    mascara = fondo.getchannel("A")
    arte.putalpha(ImageChops.multiply(arte.getchannel("A"), mascara))
    fondo.alpha_composite(arte)
    ImageDraw.Draw(fondo).rounded_rectangle((0, 0, n - 1, n - 1), radius=int(n * 0.24), outline="#2a2a36", width=K)
    return fondo.resize((tam, tam), Image.Resampling.LANCZOS)
