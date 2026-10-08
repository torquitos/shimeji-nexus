"""Funciones de dibujo compartidas por todas las formas de habilidad."""
import math
import random

from shimeji_nexus.ui.theme import blend_color

def _ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def _apagar(color, k):
    """Los ventanas de la mascota usan negro como transparente: 'desvanecer' es acercar al negro."""
    return blend_color(color, "#000000", max(0.0, min(1.0, k)))


def _anillos(c, x, y, p, colores, rmax, n=3):
    for i in range(n):
        pi = p - i * 0.12
        if pi <= 0:
            continue
        r = rmax * _ease(pi)
        c.create_oval(x - r, y - r, x + r, y + r, outline=_apagar(colores[i % len(colores)], 1 - pi),
                      width=max(1, int(8 * (1 - pi))), tags="fx")


def _estrella(c, x, y, R, color, puntas=12):
    """Destello de manga: estrella de puntas finas."""
    pts = []
    for i in range(puntas * 2):
        r = R if i % 2 == 0 else R * 0.24
        a = i * math.pi / puntas
        pts += [x + math.cos(a) * r, y + math.sin(a) * r]
    c.create_polygon(pts, fill=color, outline="", tags="fx")
    c.create_oval(x - R * 0.2, y - R * 0.2, x + R * 0.2, y + R * 0.2, fill=color, outline="", tags="fx")


def _destello(c, x, y, p, r0):
    if p < 0.3:
        _estrella(c, x, y, r0 * (1.3 + 1.5 * p), _apagar("#ffffff", 1 - p))


def _rayos(c, x, y, p, color, n=14):
    for i in range(n):
        a = i * 2 * math.pi / n
        r1 = 24 + 150 * _ease(p)
        r2 = r1 + 48 * (1 - p)
        c.create_line(x + math.cos(a) * r1, y + math.sin(a) * r1, x + math.cos(a) * r2, y + math.sin(a) * r2,
                      fill=_apagar(color, 1 - p), width=3, tags="fx")


def _esfera(c, x, y, R, colores, fase):
    c.create_oval(x - R * 1.25, y - R * 1.25, x + R * 1.25, y + R * 1.25, fill=_apagar(colores[0], 0.5), outline="", tags="fx")
    c.create_oval(x - R, y - R, x + R, y + R, fill=colores[2], outline=colores[0], width=2, tags="fx")
    c.create_oval(x - R * 0.55, y - R * 0.55, x + R * 0.55, y + R * 0.55, fill=colores[1], outline="", tags="fx")
    for k in range(3):
        c.create_arc(x - R, y - R, x + R, y + R, start=(fase * 55 + k * 120) % 360, extent=70,
                     style="arc", outline="#ffffff", width=3, tags="fx")


def _zigzag(c, x1, y1, x2, y2, color, ancho=2, tramos=7, desvio=14):
    """Rayo electrico entre dos puntos."""
    pts = [x1, y1]
    for i in range(1, tramos):
        k = i / tramos
        pts += [x1 + (x2 - x1) * k + random.uniform(-desvio, desvio), y1 + (y2 - y1) * k + random.uniform(-desvio, desvio)]
    c.create_line(*pts, x2, y2, fill=color, width=ancho, tags="fx")


def _corazon(c, x, y, r, color):
    pts = []
    for i in range(24):
        a = i * 2 * math.pi / 24
        pts += [x + 16 * math.sin(a) ** 3 * r / 16,
                y - (13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)) * r / 16]
    c.create_polygon(pts, fill=color, outline="", tags="fx")


def _lineas_velocidad(c, x, y, p, color, n=26):
    """Lineas de impacto del manga, que salen del centro hacia afuera."""
    rnd = random.Random(7)
    for _ in range(n):
        a, d0, largo = rnd.uniform(0, 2 * math.pi), rnd.uniform(90, 200) + p * 190, rnd.uniform(60, 170)
        c.create_line(x + math.cos(a) * d0, y + math.sin(a) * d0, x + math.cos(a) * (d0 + largo), y + math.sin(a) * (d0 + largo),
                      fill=_apagar(color, (1 - p) * 0.9), width=rnd.choice((1, 2, 3)), tags="fx")


def _convergencia(c, x, y, p, colores, fase=0.0, n=30):
    """Energia que se aprieta hacia el centro durante la carga (p de 0 a 1)."""
    for i in range(n):
        a = i * 2 * math.pi / n + 0.35 * math.sin(i * 1.7) + fase * 0.15
        r = 36 + 200 * (1 - _ease(p)) * (0.55 + 0.45 * ((i * 37) % 10) / 10)
        r2 = r + 40 * (1 - p) + 8
        c.create_line(x + math.cos(a) * r2, y + math.sin(a) * r2, x + math.cos(a) * r, y + math.sin(a) * r,
                      fill=_apagar(colores[i % len(colores)], 0.45 + 0.55 * p), width=3, tags="fx")
