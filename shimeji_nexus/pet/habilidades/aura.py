import math
import random

from PIL import Image, ImageChops, ImageFilter, ImageTk

from shimeji_nexus.pet.habilidades.config import CARGA
from shimeji_nexus.pet.habilidades.util import _apagar
from shimeji_nexus.ui.theme import blend_color


class AuraMixin:
    """Dibujo sobre el canvas de la mascota: orbes, aura de anillos y aura que abraza la silueta."""

    # ---------- canvas de la mascota ----------
    def _orbe(self, x, y, tam, color, detras):
        a = self.c.create_oval(x - tam, y - tam, x + tam, y + tam, fill=color, outline="", tags=self.TAG)
        t = tam * 0.4
        b = self.c.create_oval(x - t - tam * 0.2, y - t - tam * 0.25, x + t - tam * 0.2, y + t - tam * 0.25,
                               fill=blend_color("#ffffff", color, 0.55), outline="", tags=self.TAG)
        if detras:
            self.c.tag_lower(b, self.sprite)
            self.c.tag_lower(a, self.sprite)

    def _aura(self):
        inten = min(1.0, self.t / CARGA)
        for i in range(3):
            r = 96 - ((self.t * 3 + i * 14) % 42)
            anillo = self.c.create_oval(self.cx - r, self.cy - r, self.cx + r, self.cy + r,
                                        outline=_apagar(self.colores[i % len(self.colores)], 0.4 + 0.6 * inten),
                                        width=2, tags=self.TAG)
            self.c.tag_lower(anillo, self.sprite)

    @staticmethod
    def _desplazar(mascara, dx, dy):
        salida = Image.new("L", mascara.size, 0)
        salida.paste(mascara, (dx, dy))
        return salida

    def _ondular(self, mascara, amplitud, fase):
        salida = Image.new("L", mascara.size, 0)
        for y in range(mascara.height):
            dx = round(amplitud * math.sin(y * 0.55 + fase))
            salida.paste(ImageChops.offset(mascara.crop((0, y, mascara.width, y + 1)), dx, 0), (0, y))
        return salida

    def _aura_silueta(self, alfa):
        """Aura que abraza la silueta del personaje, en tres capas de pixeles grandes que ondulan
        y suben como llamas. Se dibuja detras del sprite."""
        t = self.t
        inten = min(1.0, t / CARGA) if t < CARGA else (1.0 if t < 40 else max(0.0, 1 - (t - 40) / 10))
        if inten <= 0.05:
            return
        rej = 50
        base = alfa.resize((rej, rej), Image.Resampling.BOX).point(lambda v: 255 if v > 50 else 0)
        radio = 3 + round(2 * inten)
        fase = t * 0.65
        capas = []
        for r, color, onda, sube in ((radio, self.colores[2], 2.2, 5), (max(1, round(radio * 0.6)), self.colores[0], 1.4, 3), (max(1, round(radio * 0.3)), self.colores[1], 0.0, 0)):
            m = base.filter(ImageFilter.MaxFilter(2 * r + 1))
            for k in range(2, sube + 1, 2):
                m = ImageChops.lighter(m, self._desplazar(m, 0, -k))
            capas.append((self._ondular(m, onda, fase + r), color))
        img = Image.new("RGBA", (rej, rej), (0, 0, 0, 0))
        brillo = 0.45 + 0.55 * inten
        for m, color in capas:
            img.paste(Image.new("RGBA", (rej, rej), _apagar(color, brillo)), (0, 0), m)
        grande = img.resize((self.tamano, self.tamano), Image.Resampling.NEAREST)
        self._aura_foto = ImageTk.PhotoImage(grande)
        item = self.c.create_image(self.tamano // 2, self.tamano // 2, image=self._aura_foto, tags=self.TAG)
        self.c.tag_lower(item, self.sprite)

    def _estallido_chispas(self):
        for _ in range(34):
            a, v = random.uniform(0, 6.28), random.uniform(2.5, 7)
            self.chispas.append({"x": self.cx, "y": self.cy, "vx": math.cos(a) * v, "vy": math.sin(a) * v,
                                 "tam": random.uniform(2, 5), "col": self._color(), "vida": 1.0})
