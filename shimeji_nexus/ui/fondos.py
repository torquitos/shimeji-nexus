"""Emblema que va detras del personaje en su portada: cada forma de tecnica tiene el suyo."""
import math
import random

from PIL import Image, ImageDraw

K = 2


def _orbes(d, cx, cy):
    for r, w in ((128, 3), (100, 2), (72, 2)):
        d.ellipse((cx - r * K, cy - r * K, cx + r * K, cy + r * K), outline=255, width=w * K)
    for i in range(48):
        a = i * math.pi / 24
        r0, r1 = 128 * K, (146 if i % 4 == 0 else 138) * K
        d.line((cx + r0 * math.cos(a), cy + r0 * math.sin(a), cx + r1 * math.cos(a), cy + r1 * math.sin(a)), fill=255, width=2 * K)
    pts = [(cx + 100 * K * math.cos(-math.pi / 2 + i * 2 * math.pi / 3), cy + 100 * K * math.sin(-math.pi / 2 + i * 2 * math.pi / 3)) for i in range(3)]
    d.polygon(pts, outline=255, width=2 * K)


def _espiral(d, cx, cy):
    for brazo in range(3):
        base = brazo * 2 * math.pi / 3
        pts = [(cx + (6 + t * 2.6) * K * math.cos(base + t * 0.07), cy + (6 + t * 2.6) * K * math.sin(base + t * 0.07)) for t in range(0, 52)]
        d.line(pts, fill=255, width=5 * K, joint="curve")
    d.ellipse((cx - 150 * K, cy - 150 * K, cx + 150 * K, cy + 150 * K), outline=255, width=2 * K)


def _brasas(d, cx, cy):
    for r, w in ((140, 3), (104, 2)):
        d.arc((cx - r * K, cy - r * K, cx + r * K, cy + r * K), 180, 360, fill=255, width=w * K)
    for i in range(15):
        a = math.pi + i * math.pi / 14
        r0, r1 = 140 * K, (176 if i % 2 == 0 else 160) * K
        d.line((cx + r0 * math.cos(a), cy + r0 * math.sin(a), cx + r1 * math.cos(a), cy + r1 * math.sin(a)), fill=255, width=3 * K)
    azar = random.Random(7)
    for _ in range(26):
        x, y, s = cx + azar.randint(-150, 150) * K, cy + azar.randint(-170, 130) * K, azar.randint(3, 7) * K
        d.polygon([(x, y - s), (x + s * 0.6, y), (x, y + s), (x - s * 0.6, y)], fill=255)


def _rayo(d, cx, cy):
    d.regular_polygon((cx, cy, 130 * K), 6, rotation=0, outline=255, width=3 * K)
    d.regular_polygon((cx, cy, 92 * K), 6, rotation=30, outline=255, width=2 * K)
    azar = random.Random(3)
    for i in range(8):
        a = i * math.pi / 4 + 0.2
        x, y, pts = cx, cy, [(cx, cy)]
        for paso in range(5):
            a += azar.uniform(-0.5, 0.5)
            x, y = x + 34 * K * math.cos(a), y + 34 * K * math.sin(a)
            pts.append((x, y))
        d.line(pts, fill=255, width=3 * K)


def _zoomies(d, cx, cy):
    for r, w in ((132, 3), (96, 2)):
        d.arc((cx - r * K, cy - r * K, cx + r * K, cy + r * K), 20, 340, fill=255, width=w * K)
    for i in range(7):
        y = cy + (i - 3) * 30 * K
        d.line((cx - 170 * K, y, cx - 60 * K - i % 3 * 22 * K, y), fill=255, width=3 * K)
    azar = random.Random(11)
    for _ in range(14):
        x, y, s = cx + azar.randint(-130, 140) * K, cy + azar.randint(-150, 150) * K, azar.randint(5, 10) * K
        pts = [(x + s * math.cos(i * math.pi / 5 - math.pi / 2) * (1 if i % 2 == 0 else 0.4), y + s * math.sin(i * math.pi / 5 - math.pi / 2) * (1 if i % 2 == 0 else 0.4)) for i in range(10)]
        d.polygon(pts, fill=255)


FORMAS = {"orbes": _orbes, "orbitar": _orbes, "espiral": _espiral, "brasas": _brasas, "rayo": _rayo, "zoomies": _zoomies}


def emblema(ancho, alto, caja, forma, fuerza=0.85):
    """Capa en escala de grises con el dibujo de la forma, centrado en el escenario."""
    x0, y0, x1, y1 = caja
    cx, cy = ((x0 + x1) / 2) * K, (y0 + (y1 - y0) * 0.46) * K
    capa = Image.new("L", (ancho * K, alto * K), 0)
    FORMAS.get(forma, _orbes)(ImageDraw.Draw(capa), cx, cy)
    return capa.resize((ancho, alto), Image.Resampling.LANCZOS).point(lambda v: int(v * fuerza))
