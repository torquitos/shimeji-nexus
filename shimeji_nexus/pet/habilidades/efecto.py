import math
import random

from PIL import ImageTk

from shimeji_nexus.pet.habilidades.aura import AuraMixin
from shimeji_nexus.pet.habilidades.config import CARGA, DISPARO, TOTAL
from shimeji_nexus.pet.habilidades.formas import FormasMixin
from shimeji_nexus.pet.habilidades.lienzo import Lienzo
from shimeji_nexus.pet.habilidades.util import _apagar, _ease
from shimeji_nexus.ui.theme import blend_color


class EfectoHabilidad(AuraMixin, FormasMixin):
    """Habilidad de un personaje: carga, disparo e impacto. Dibuja en el canvas de la mascota
    (aura, orbes, chispas) y en un Lienzo grande (letrero, proyectil, ondas)."""

    TAG = "particula"

    def __init__(self, canvas, sprite_id, tamano, habilidad, master=None, sprite_propio=False, silueta=None, retrato=None, autor=""):
        self._retrato_tk = ImageTk.PhotoImage(retrato) if retrato is not None else None
        self.autor = autor
        self.silueta = silueta
        self.tamano = tamano
        self._aura_foto = None
        self.sprite_propio = sprite_propio
        self.c = canvas
        self.sprite = sprite_id
        self.master = master
        self.nombre = habilidad["nombre"]
        self.forma = habilidad["forma"]
        self.colores = habilidad["colores"]
        self.cx, self.cy = tamano // 2, int(tamano * 0.52)
        self.parts = []
        self.chispas = []
        self.vivo = 0
        self.direccion = 1
        self.fase = 0.0
        self.nucleo = 0.0
        self.t = None
        self.lienzo = None

    def _color(self):
        return random.choice(self.colores)

    def iniciar(self, direccion):
        self.t = 0
        self.direccion = direccion
        self.parts = []
        self.chispas = []
        self.nucleo = 0.0

    def generar(self, direccion):
        self.vivo = 4
        self.direccion = direccion
        if self.forma == "orbitar":
            while len(self.parts) < 7:
                self.parts.append({
                    "ang": random.uniform(0, 6.28), "r": random.uniform(46, 70),
                    "vel": random.choice((-1, 1)) * random.uniform(0.10, 0.19),
                    "tam": random.uniform(6, 10), "dy": random.uniform(-34, 34),
                    "col": self._color(), "vida": 1.0,
                })
        elif self.forma in ("brasas", "rayo"):
            for _ in range(0 if self.silueta else 5):
                self.parts.append({
                    "x": self.cx + random.uniform(-42, 42), "y": self.cy + random.uniform(10, 72),
                    "vx": random.uniform(-0.6, 0.6), "vy": -random.uniform(1.5, 3.6),
                    "tam": random.uniform(3.2, 6.5), "col": self._color(), "vida": 1.0,
                })
        elif self.t is None or self.t < CARGA:
            for _ in range(2):
                self.parts.append({"ang": random.uniform(0, 6.28), "r": 46.0, "col": self._color(), "vida": 1.0})


    def dibujar(self):
        activo = self.vivo > 0
        if activo:
            self.vivo -= 1
        self.fase += 0.35
        cargando = self.t is not None and self.t < CARGA
        if self.t is not None and self.t < CARGA + DISPARO:
            alfa = self.silueta() if self.silueta else None
            if alfa is not None:
                self._aura_silueta(alfa)
            elif self.t < CARGA + 4:
                self._aura()
        vivas = []

        if self.forma == "orbitar":
            for p in self.parts:
                p["ang"] += p["vel"] * (1 + 2 * _ease(self.t / CARGA) if cargando else 1)
                if not activo:
                    p["vida"] -= 0.08
                if p["vida"] <= 0.1:
                    continue
                r = p["r"] * (1 - 0.45 * _ease(self.t / CARGA)) if cargando else p["r"]
                x = self.cx + math.cos(p["ang"]) * r
                y = self.cy + p["dy"] * 0.5 + math.sin(p["ang"]) * r * 0.35
                detras = math.sin(p["ang"]) < 0
                self._orbe(x, y, p["tam"] * (0.75 if detras else 1.0), blend_color(p["col"], "#000000", p["vida"]), detras)
                vivas.append(p)

        elif self.forma in ("brasas", "rayo"):
            for p in self.parts:
                p["x"] += p["vx"] + random.uniform(-0.3, 0.3)
                p["y"] += p["vy"]
                p["vida"] -= 0.035
                if p["vida"] <= 0.1 or p["y"] < -6:
                    continue
                r = p["tam"] * (0.5 + p["vida"] / 2)
                self.c.create_oval(p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r,
                                   fill=blend_color(p["col"], "#000000", p["vida"]), outline="", tags=self.TAG)
                vivas.append(p)

        else:
            self.nucleo = _ease(self.t / CARGA) if cargando else max(0.0, self.nucleo - 0.2)
            sx, sy = self.cx + self.direccion * 54, self.cy + 8
            for p in self.parts:
                p["ang"] += 0.55
                p["r"] -= 1.6
                if p["r"] <= 4:
                    continue
                x, y = sx + math.cos(p["ang"]) * p["r"], sy + math.sin(p["ang"]) * p["r"]
                self.c.create_oval(x - 2, y - 2, x + 2, y + 2, fill=p["col"], outline="", tags=self.TAG)
                vivas.append(p)
            if self.nucleo > 0.02 and not self.sprite_propio:
                R = 21 * self.nucleo
                self.c.create_oval(sx - R * 1.25, sy - R * 1.25, sx + R * 1.25, sy + R * 1.25,
                                   fill=_apagar(self.colores[0], 0.5), outline="", tags=self.TAG)
                self.c.create_oval(sx - R, sy - R, sx + R, sy + R, fill=self.colores[2], outline=self.colores[0], width=2, tags=self.TAG)
                self.c.create_oval(sx - R * 0.55, sy - R * 0.55, sx + R * 0.55, sy + R * 0.55,
                                   fill=self.colores[1], outline="", tags=self.TAG)
                for k in range(3):
                    self.c.create_arc(sx - R, sy - R, sx + R, sy + R, start=(self.fase * 55 + k * 120) % 360, extent=70,
                                      style="arc", outline="#ffffff", width=3, tags=self.TAG)
        self.parts = vivas

        restantes = []
        for p in self.chispas:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vx"] *= 0.94
            p["vy"] = p["vy"] * 0.94 + 0.12
            p["vida"] -= 0.05
            if p["vida"] <= 0.1:
                continue
            r = p["tam"] * (0.5 + p["vida"] / 2)
            self.c.create_oval(p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r,
                               fill=_apagar(p["col"], p["vida"]), outline="", tags=self.TAG)
            restantes.append(p)
        self.chispas = restantes

    # ---------- lienzo grande ----------
    def _lienzo(self):
        if self.lienzo is None and self.master is not None:
            self.lienzo = Lienzo(self.master)
        return self.lienzo

    def paso(self, cx, cy, mostrar):
        """Avanza la habilidad un tick. Devuelve el temblor (dx, dy) para la ventana de la mascota."""
        if self.t is None:
            return 0, 0
        t = self.t
        self.t += 1
        if t == CARGA:
            self._estallido_chispas()
        if t < CARGA:
            amp = 1
        elif t < CARGA + 6:
            amp = int(5 * (1 - (t - CARGA) / 6))
        else:
            amp = 0
        temblor = (random.randint(-amp, amp), random.randint(-amp, amp))

        lz = self._lienzo() if mostrar else None
        if lz is not None:
            lz.mostrar(cx, cy)
            lz.canvas.delete("fx")
            ox, oy = Lienzo.W // 2, Lienzo.H // 2
            self._letrero(lz.canvas, t, ox, oy)
            getattr(self, "_fx_" + self.forma)(lz.canvas, t, ox, oy)
        if self.t > TOTAL:
            self.t = None
            if self.lienzo is not None:
                self.lienzo.ocultar()
        return temblor
