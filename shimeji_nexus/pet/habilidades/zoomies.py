import math
import random

from shimeji_nexus.pet.habilidades.util import _apagar, _convergencia, _ease, _estrella, _lineas_velocidad

ARRANQUE = 20
FIN_CARRERA = 58


class ZoomiesMixin:
    """Zoomies: el gato se agacha, se carga de energia y sale corriendo con una estela de estrellas."""

    def _fx_zoomies(self, c, t, ox, oy):
        d = self.direccion
        dorado, claro, naranja = self.colores
        if t < ARRANQUE:
            _convergencia(c, ox, oy - 10, t / ARRANQUE, [dorado, claro, naranja], self.fase, 24)
            if t > 8 and t % 2 == 0:
                self._destello_gato(c, ox + random.randint(-60, 60), oy + random.randint(-70, 10), 5 + random.random() * 6, claro)
        elif t < FIN_CARRERA:
            self._carrera(c, t, ox, oy, d, dorado, claro, naranja)
        elif t < FIN_CARRERA + 18:
            self._aterrizaje(c, (t - FIN_CARRERA) / 18, ox, oy, dorado, claro)

    def _carrera(self, c, t, ox, oy, d, dorado, claro, naranja):
        q = (t - ARRANQUE) / (FIN_CARRERA - ARRANQUE)
        for i in range(5):
            y = oy - 70 + i * 34 + math.sin(self.fase + i) * 4
            largo = 140 + (i % 3) * 70
            c.create_line(ox - d * 70, y, ox - d * (70 + largo), y, fill=_apagar(claro if i % 2 else dorado, 0.7), width=3 - i % 2, tags="fx")
        for k in range(1, 9):
            x = ox - d * k * 44
            r = max(4, 20 - k * 2)
            self._destello_gato(c, x, oy + math.sin(self.fase * 2 + k) * 24 - 6, r, dorado if k % 2 else naranja, 1 - k * 0.1)
        for k in range(4):
            c.create_oval(ox - d * (k * 60 + 30) - 14, oy + 76 - k * 3, ox - d * (k * 60 + 30) + 14, oy + 90 - k * 3, fill=_apagar("#e8e0d0", 0.45 - k * 0.1), outline="", tags="fx")
        if 0.4 < q < 0.8:
            _lineas_velocidad(c, ox, oy, (q - 0.4) / 0.4, claro, 10)

    def _aterrizaje(self, c, p, ox, oy, dorado, claro):
        for i in range(10):
            a = i * 0.628 + p
            r = 40 + 90 * _ease(p)
            self._destello_gato(c, ox + math.cos(a) * r, oy - 16 + math.sin(a) * r * 0.7, 9 * (1 - p) + 2, dorado if i % 2 else claro, 1 - p)
        for i in range(3):
            x = ox + (i - 1) * 50
            c.create_oval(x - 10, oy + 78 - 6 * math.sin(p * 3.1), x + 10, oy + 92, fill=_apagar(claro, 1 - p), outline="", tags="fx")

    def _destello_gato(self, c, x, y, r, color, k=1.0):
        _estrella(c, x, y, r, _apagar(color, max(0.0, min(1.0, k))), 4)
