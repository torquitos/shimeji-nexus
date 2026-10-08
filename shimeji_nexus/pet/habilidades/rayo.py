import math
import random

from shimeji_nexus.pet.habilidades.config import CARGA, DISPARO, IMPACTO
from shimeji_nexus.pet.habilidades.util import _anillos, _apagar, _convergencia, _corazon, _destello, _ease, _rayos

LARGO = 340


class RayoMixin:
    """Rayo de la Cola: un haz rosa y violeta con chispas de corazones."""

    def _fx_rayo(self, c, t, ox, oy):
        d = self.direccion
        x0, y0 = ox + d * 52, oy + 4
        if t < CARGA:
            self._carga_rayo(c, t, x0, y0)
        elif t < CARGA + DISPARO:
            self._haz(c, t, x0, y0, d)
        elif t < CARGA + DISPARO + IMPACTO:
            self._impacto_rayo(c, (t - CARGA - DISPARO) / IMPACTO, x0 + d * LARGO, y0)

    def _carga_rayo(self, c, t, x0, y0):
        p = t / CARGA
        _convergencia(c, x0, y0, p, self.colores, self.fase)
        R = 4 + 14 * p + random.uniform(0, 2)
        c.create_oval(x0 - R * 1.6, y0 - R * 1.6, x0 + R * 1.6, y0 + R * 1.6, fill=_apagar(self.colores[0], 0.35), outline="", tags="fx")
        c.create_oval(x0 - R, y0 - R, x0 + R, y0 + R, fill=self.colores[1], outline=self.colores[0], width=2, tags="fx")
        if t % 5 == 0:
            _corazon(c, x0 + random.uniform(-40, 40), y0 - random.uniform(20, 60), 7, self.colores[0])

    def _haz(self, c, t, x0, y0, d):
        q = (t - CARGA) / DISPARO
        L = LARGO * _ease(min(1.0, q * 5))
        grosor = 1.0 if q < 0.65 else max(0.0, 1 - (q - 0.65) / 0.35)
        x1 = x0 + d * L
        self._flash(c, t, x0, y0, 110)
        for h, color, k in ((46, self.colores[2], 0.45), (30, self.colores[0], 1.0), (13, "#ffffff", 1.0)):
            hh = h * grosor
            if hh < 1:
                continue
            top, bot = [], []
            for i in range(0, 17):
                x = x0 + (x1 - x0) * i / 16
                ond = math.sin(i * 0.9 + self.fase * 2.4) * hh * 0.12
                top.append((x, y0 - hh / 2 * (1 - i / 40) + ond))
                bot.append((x, y0 + hh / 2 * (1 - i / 40) - ond))
            pts = [v for p in top + [(x1 + d * 14, y0)] + bot[::-1] for v in p]
            c.create_polygon(pts, fill=_apagar(color, k), outline="", tags="fx")
        for _ in range(4):
            _corazon(c, x0 + d * random.uniform(30, max(40, L)), y0 + random.uniform(-40, 40) * grosor, random.uniform(5, 10), _apagar(random.choice(self.colores), 0.9))
        for _ in range(6):
            sx, sy, r = x0 + d * random.uniform(0, L), y0 + random.uniform(-30, 30) * grosor, random.uniform(2, 4)
            c.create_oval(sx - r, sy - r, sx + r, sy + r, fill=_apagar(self.colores[1], 0.9), outline="", tags="fx")

    def _impacto_rayo(self, c, p, ex, y0):
        _destello(c, ex, y0, p, 40)
        _anillos(c, ex, y0, p, self.colores, 125)
        _rayos(c, ex, y0, p, self.colores[1], 14)
        rnd = random.Random(5)
        for i in range(8):
            a, v = rnd.uniform(0, 6.28), rnd.uniform(60, 150)
            _corazon(c, ex + math.cos(a) * v * _ease(p), y0 + math.sin(a) * v * _ease(p) - 30 * p, 11 * (1 - p) + 3, _apagar(self.colores[i % 3], 1 - p))
