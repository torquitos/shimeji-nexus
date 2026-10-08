import math
import random

from shimeji_nexus.pet.habilidades.config import CARGA, DISPARO, IMPACTO
from shimeji_nexus.pet.habilidades.util import _anillos, _apagar, _convergencia, _destello, _ease, _lineas_velocidad, _zigzag

NEGRO_ROJO = "#1c040a"
ALCANCE = 250


class BrasasMixin:
    """Poder de la Destruccion: una esfera negra y carmesi que desintegra todo lo que toca."""

    def _fx_brasas(self, c, t, ox, oy):
        d, cy = self.direccion, oy - 6
        if t < CARGA:
            _convergencia(c, ox, cy, t / CARGA, self.colores, self.fase)
            if not self.sprite_propio:
                R = 8 + 14 * _ease(t / CARGA) + random.uniform(0, 2)
                c.create_oval(ox - R, cy - R, ox + R, cy + R, fill=NEGRO_ROJO, outline=self.colores[0], width=3, tags="fx")
        elif t < CARGA + DISPARO:
            self._disparo_brasas(c, t, ox, cy, d)
        elif t < CARGA + DISPARO + IMPACTO:
            self._impacto_brasas(c, (t - CARGA - DISPARO) / IMPACTO, ox + d * ALCANCE, cy)

    def _disparo_brasas(self, c, t, ox, cy, d):
        q = (t - CARGA) / DISPARO
        rojo, brasa = self.colores[0], self.colores[1]
        x, R = ox + d * (50 + 200 * _ease(q)), 30 + 8 * q
        self._flash(c, t, ox, cy, 130)
        _lineas_velocidad(c, x, cy, q, rojo, 14)
        for i in range(5):
            ri = 40 + 300 * _ease(q) - i * 24
            if ri >= 10:
                c.create_arc(ox - ri, cy - ri, ox + ri, cy + ri, start=(0 if d > 0 else 180) - 36, extent=72, style="arc",
                             outline=_apagar(self.colores[i % 2], 1 - q * 0.85 - i * 0.08), width=max(2, 8 - i * 2), tags="fx")
        for _ in range(14):
            fx_, fy = x - d * random.uniform(10, 120), cy + random.uniform(-26, 40)
            s = random.uniform(2, 6)
            c.create_rectangle(fx_ - s, fy - s, fx_ + s, fy + s, fill=_apagar(random.choice((rojo, brasa, "#5a0a14")), random.uniform(0.4, 0.9)), outline="", tags="fx")
        c.create_oval(x - R * 1.5, cy - R * 1.5, x + R * 1.5, cy + R * 1.5, fill=_apagar(rojo, 0.3), outline="", tags="fx")
        c.create_oval(x - R, cy - R, x + R, cy + R, fill=NEGRO_ROJO, outline=rojo, width=4, tags="fx")
        for _ in range(5):
            a = random.uniform(0, 6.28)
            _zigzag(c, x, cy, x + math.cos(a) * R * 1.7, cy + math.sin(a) * R * 1.7, random.choice((rojo, brasa)), 2, 5, 8)

    def _impacto_brasas(self, c, p, ex, cy):
        rojo, brasa = self.colores[0], self.colores[1]
        R = 120 * _ease(min(1.0, p * 1.4))
        c.create_oval(ex - R, cy - R, ex + R, cy + R, fill=_apagar(NEGRO_ROJO, 1 - p ** 2 * 0.9), outline=_apagar(rojo, 1 - p), width=max(1, int(7 * (1 - p))), tags="fx")
        rnd = random.Random(3)
        for _ in range(12):
            a = rnd.uniform(0, 6.28)
            _zigzag(c, ex, cy, ex + math.cos(a) * R * 1.2, cy + math.sin(a) * R * 1.2, _apagar(brasa, 1 - p), 3, 7, 10)
        _destello(c, ex, cy, p, 40)
        _anillos(c, ex, cy, p, [rojo, brasa], 190, 2)
