from shimeji_nexus.pet.habilidades.config import CARGA
from shimeji_nexus.pet.habilidades.util import _apagar, _ease, _estrella

BANDA_Y = 50
BANDA_ALTO = 86
INCLINA = 36


class CinematicaMixin:
    """Corte de camara estilo anime: banda diagonal con el retrato y el nombre de la tecnica."""

    def _banda(self, c, ancho, desp, y, alto, relleno, borde, grosor):
        a = alto / 2
        pts = [-INCLINA + desp, y - a, ancho + desp, y - a, ancho + INCLINA + desp, y + a, desp, y + a]
        c.create_polygon(pts, fill=relleno, outline=borde, width=grosor, tags="fx")

    def _letrero(self, c, t, ox, oy):
        k = 1.0 if t <= 58 else 1 - (t - 58) / 12
        if k <= 0.04:
            return
        ancho = int(float(c.cget("width")))
        desp = -(1 - _ease(t / 7)) * ancho
        acento, y = self.colores[0], BANDA_Y
        self._banda(c, ancho, desp + 14, y + 10, BANDA_ALTO, _apagar(self.colores[2], 0.75 * k), "", 0)
        self._banda(c, ancho, desp, y, BANDA_ALTO, _apagar("#12121a", k), _apagar(acento, k), 3)
        xr = 66 + desp
        c.create_oval(xr - 46, y - 46, xr + 46, y + 46, fill=_apagar("#1d1d28", k), outline=_apagar(acento, k), width=3, tags="fx")
        if self._retrato_tk is not None and k > 0.85:
            c.create_image(xr, y, image=self._retrato_tk, tags="fx")
        x0 = 128 + desp
        c.create_text(x0, y - 22, anchor="w", text=self.autor.upper(), font=("Segoe UI", 10, "bold"), fill=_apagar(acento, k), tags="fx")
        nombre = self.nombre.upper()
        c.create_text(x0 + 2, y + 10, anchor="w", text=nombre, font=("Segoe UI", 26, "bold italic"), fill=_apagar(self.colores[2], k), tags="fx")
        c.create_text(x0, y + 8, anchor="w", text=nombre, font=("Segoe UI", 26, "bold italic"), fill=_apagar("#ffffff", k), tags="fx")

    def _flash(self, c, t, x, y, radio=170):
        """Destello de pantalla al soltar el ataque."""
        p = (t - CARGA) / 3
        if 0 <= p < 1:
            _estrella(c, x, y, radio * (0.55 + 0.45 * p), "#ffffff", 14)
