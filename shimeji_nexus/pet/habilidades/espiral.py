import math

from shimeji_nexus.pet.habilidades.config import CARGA, DISPARO, IMPACTO
from shimeji_nexus.pet.habilidades.util import _anillos, _apagar, _convergencia, _destello, _ease, _lineas_velocidad, _rayos

ALCANCE = 250


def _brazos(c, x, y, R, giro, color, ancho, n=3):
    """Espiral de viento que gira dentro de la esfera."""
    for k in range(n):
        pts = []
        for i in range(14):
            r = R * (0.12 + 0.88 * i / 13)
            a = giro + k * 2 * math.pi / n + i * 0.34
            pts += [x + math.cos(a) * r, y + math.sin(a) * r]
        c.create_line(*pts, fill=color, width=ancho, smooth=True, tags="fx")


class EspiralMixin:
    """Rasengan: esfera de chakra con el viento girando en su interior."""

    def _fx_espiral(self, c, t, ox, oy):
        d = self.direccion
        hx, hy = ox + d * 54, oy + 8
        if t < CARGA:
            _convergencia(c, hx, hy, t / CARGA, self.colores, self.fase)
            if t > 6 and not self.sprite_propio:
                R = 4 + 20 * _ease(t / CARGA)
                c.create_oval(hx - R, hy - R, hx + R, hy + R, fill=self.colores[2], outline=self.colores[1], width=2, tags="fx")
                _brazos(c, hx, hy, R, self.fase * 2.2, "#ffffff", 2)
        elif t < CARGA + DISPARO:
            self._disparo_espiral(c, t, hx, hy, d)
        elif t < CARGA + DISPARO + IMPACTO:
            self._impacto_espiral(c, (t - CARGA - DISPARO) / IMPACTO, hx + d * ALCANCE, hy)

    def _disparo_espiral(self, c, t, hx, hy, d):
        q = (t - CARGA) / DISPARO
        azul, claro, hondo = self.colores
        x, R = hx + d * ALCANCE * _ease(q), 32 + 8 * q
        self._flash(c, t, hx, hy, 120)
        _lineas_velocidad(c, x, hy, q, claro, 16)
        for i in range(4, 0, -1):
            rr = R * (1 - 0.18 * i)
            c.create_oval(x - d * i * 22 - rr, hy - rr, x - d * i * 22 + rr, hy + rr, fill=_apagar(azul, 0.5 - i * 0.09), outline="", tags="fx")
        c.create_oval(x - R * 1.35, hy - R * 1.35, x + R * 1.35, hy + R * 1.35, fill=_apagar(azul, 0.35), outline="", tags="fx")
        c.create_oval(x - R, hy - R, x + R, hy + R, fill=hondo, outline=claro, width=2, tags="fx")
        _brazos(c, x, hy, R, self.fase * 2.2, "#ffffff", 3)
        _brazos(c, x, hy, R * 0.8, -self.fase * 1.6, azul, 3, 2)
        for k in range(2):
            a = self.fase * 1.2 + k * math.pi
            c.create_arc(x - R * 1.6, hy - R * 0.55, x + R * 1.6, hy + R * 0.55, start=math.degrees(a) % 360, extent=110, style="arc",
                         outline=_apagar(claro, 0.8), width=3, tags="fx")

    def _impacto_espiral(self, c, p, ex, hy):
        azul, claro, hondo = self.colores
        R = 125 * _ease(min(1.0, p * 1.4))
        c.create_oval(ex - R, hy - R, ex + R, hy + R, fill=_apagar(hondo, (1 - p) * 0.8), outline=_apagar(claro, 1 - p), width=max(1, int(6 * (1 - p))), tags="fx")
        _brazos(c, ex, hy, R, p * 6, _apagar("#ffffff", 1 - p), 4, 4)
        _destello(c, ex, hy, p, 52)
        _anillos(c, ex, hy, p, [azul, claro, "#ffffff"], 200)
        _rayos(c, ex, hy, p, claro, 16)
