import math
import random

from shimeji_nexus.pet.habilidades.config import CARGA, DISPARO, IMPACTO
from shimeji_nexus.pet.habilidades.util import _anillos, _apagar, _convergencia, _destello, _ease, _lineas_velocidad, _rayos, _zigzag

AZUL, ROJO, OSCURO = "#4aa8ff", "#ff4a6a", "#1d0b36"
ALCANCE = 250


class OrbitarMixin:
    """Vacio Purpura: el Azul y el Rojo giran hasta fundirse en una esfera de vacio que lo borra todo."""

    def _fx_orbitar(self, c, t, ox, oy):
        d = self.direccion
        mx, my = ox + d * 70, oy - 14
        morado = self.colores[1]
        if t < CARGA:
            self._carga_orbitar(c, t, mx, my, morado)
        elif t < CARGA + DISPARO:
            self._disparo_orbitar(c, t, mx, my, morado, d)
        elif t < CARGA + DISPARO + IMPACTO:
            self._impacto_orbitar(c, (t - CARGA - DISPARO) / IMPACTO, mx + d * ALCANCE, my, morado)

    def _carga_orbitar(self, c, t, mx, my, morado):
        p = t / CARGA
        _convergencia(c, mx, my, p, [AZUL, ROJO, morado], self.fase)
        if self.sprite_propio:
            return
        radio, r = (1 - _ease(p)) * 80 + 4, 9 + 10 * p
        for color, a0 in ((AZUL, 0.0), (ROJO, math.pi)):
            a = a0 + p * 11
            x, y = mx + math.cos(a) * radio, my + math.sin(a) * radio * 0.6
            c.create_oval(x - r * 1.6, y - r * 1.6, x + r * 1.6, y + r * 1.6, fill=_apagar(color, 0.4), outline="", tags="fx")
            c.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="#ffffff", width=1, tags="fx")

    def _disparo_orbitar(self, c, t, mx, my, morado, d):
        q = (t - CARGA) / DISPARO
        x, r = mx + d * ALCANCE * _ease(q), 38 + 12 * q
        self._flash(c, t, mx, my)
        _lineas_velocidad(c, x, my, q, morado, 18)
        for i in range(6, 0, -1):
            rr = r * (1 - i * 0.12)
            c.create_oval(x - d * i * 20 - rr, my - rr, x - d * i * 20 + rr, my + rr, fill=_apagar(morado, 0.55 - i * 0.08), outline="", tags="fx")
        c.create_oval(x - r * 1.5, my - r * 1.5, x + r * 1.5, my + r * 1.5, fill=_apagar(morado, 0.35), outline="", tags="fx")
        c.create_oval(x - r, my - r, x + r, my + r, fill=OSCURO, outline=morado, width=4, tags="fx")
        c.create_oval(x - r * 0.45, my - r * 0.45, x + r * 0.45, my + r * 0.45, fill=_apagar("#e5d4ff", 0.55), outline="", tags="fx")
        for _ in range(4):
            a = random.uniform(0, 6.28)
            _zigzag(c, x, my, x + math.cos(a) * r * 1.9, my + math.sin(a) * r * 1.9, random.choice((morado, "#ffffff")), 2, 5, 9)
        for color, a0 in ((AZUL, 0.0), (ROJO, math.pi)):
            a = a0 + self.fase * 1.4
            ox2, oy2 = x + math.cos(a) * r * 1.35, my + math.sin(a) * r * 0.55
            c.create_oval(ox2 - 7, oy2 - 7, ox2 + 7, oy2 + 7, fill=color, outline="#ffffff", tags="fx")

    def _impacto_orbitar(self, c, p, ex, my, morado):
        R = 120 * _ease(min(1.0, p * 1.5))
        c.create_oval(ex - R, my - R, ex + R, my + R, fill=_apagar(OSCURO, 1 - p ** 2 * 0.9), outline=_apagar(morado, 1 - p), width=max(1, int(8 * (1 - p))), tags="fx")
        for i in range(10):
            a = i * 0.628 + p
            _zigzag(c, ex, my, ex + math.cos(a) * R * 1.25, my + math.sin(a) * R * 1.25, _apagar(morado, 1 - p), 3, 6, 12)
        _destello(c, ex, my, p, 56)
        _anillos(c, ex, my, p, [morado, AZUL, ROJO], 200)
        _rayos(c, ex, my, p, morado, 14)
