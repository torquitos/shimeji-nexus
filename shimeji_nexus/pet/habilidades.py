import ctypes
import math
import random
import tkinter as tk

from PIL import Image, ImageChops, ImageFilter, ImageTk

from shimeji_nexus.ui.theme import acento_desde_color_texto, blend_color

FORMAS = ("orbitar", "brasas", "espiral", "rayo")

# Linea de tiempo de una habilidad, en ticks de 35 ms (92 ticks = 3.2 s)
CARGA, DISPARO, IMPACTO, TOTAL = 28, 22, 16, 92


def cargar_habilidad(config):
    """Habilidad del personaje (config.json -> 'habilidad'). Si falta, un efecto generico
    con el color de acento del personaje."""
    h = dict(config.get("habilidad") or {})
    color = config.get("color_texto")
    acento = acento_desde_color_texto(color) if color else "#5b9bd9"
    h.setdefault("nombre", "Aura mágica")
    h.setdefault("forma", "brasas")
    h.setdefault("colores", [acento, blend_color("#ffffff", acento, 0.5), blend_color("#000000", acento, 0.6)])
    if h["forma"] not in FORMAS:
        h["forma"] = "brasas"
    return h


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


def _destello(c, x, y, p, r0):
    if p >= 0.3:
        return
    r = r0 * (1 + 1.5 * p)
    c.create_oval(x - r, y - r, x + r, y + r, fill=_apagar("#ffffff", 1 - p), outline="", tags="fx")


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


class Lienzo:
    """Ventana transparente mas grande que la mascota, por la que los clics pasan de largo,
    donde se dibujan los efectos grandes (proyectiles, ondas, el letrero)."""

    W, H = 1000, 600

    def __init__(self, master):
        self.win = tk.Toplevel(master)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.wm_attributes("-transparentcolor", "black")
        self.win.configure(bg="black")
        self.canvas = tk.Canvas(self.win, width=self.W, height=self.H, bg="black", bd=0, highlightthickness=0)
        self.canvas.pack()
        self.win.withdraw()
        self.visible = False
        self._clics_listos = False

    def _pasar_clics(self):
        try:
            self.win.update_idletasks()
            user32 = ctypes.windll.user32
            hwnd = user32.GetParent(self.win.winfo_id()) or self.win.winfo_id()
            user32.SetWindowLongW(hwnd, -20, user32.GetWindowLongW(hwnd, -20) | 0x80000 | 0x20)
        except Exception:
            pass

    def mostrar(self, cx, cy):
        self.win.geometry(f"{self.W}x{self.H}+{int(cx - self.W / 2)}+{int(cy - self.H / 2)}")
        if not self.visible:
            self.win.deiconify()
            self.win.lift()
            self.visible = True
            if not self._clics_listos:
                self._pasar_clics()
                self._clics_listos = True

    def ocultar(self):
        self.canvas.delete("fx")
        if self.visible:
            self.win.withdraw()
            self.visible = False


class EfectoHabilidad:
    """Habilidad de un personaje: carga, disparo e impacto. Dibuja en el canvas de la mascota
    (aura, orbes, chispas) y en un Lienzo grande (letrero, proyectil, ondas)."""

    TAG = "particula"

    def __init__(self, canvas, sprite_id, tamano, habilidad, master=None, sprite_propio=False, silueta=None):
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

    def _letrero(self, c, t, ox, oy):
        desp = -(1 - _ease(t / 6)) * 160 if t < 6 else 0
        k = 1.0 if t <= 56 else 1 - (t - 56) / 10
        if k <= 0.05:
            return
        mitad = max(105, len(self.nombre) * 6.6 + 34)
        y = oy - 250
        pts = [ox - mitad + 12 + desp, y - 15, ox + mitad + 12 + desp, y - 15, ox + mitad - 2 + desp, y + 15, ox - mitad - 2 + desp, y + 15]
        c.create_polygon(pts, fill=_apagar("#16161f", k), outline=_apagar(self.colores[0], k), width=2, tags="fx")
        c.create_text(ox + 5 + desp, y, text=self.nombre.upper(), font=("Segoe UI", 12, "bold italic"),
                      fill=_apagar("#ffffff", k), tags="fx")

    def _fx_orbitar(self, c, t, ox, oy):
        d = self.direccion
        mx, my = ox + d * 70, oy - 14
        azul, rojo, morado = "#4aa8ff", "#ff4a6a", self.colores[1]
        if t < CARGA and self.sprite_propio:
            return
        if t < CARGA:
            p = t / CARGA
            h = (1 - _ease(p)) * 60 + 2
            r = 7 + 7 * p
            for color, yy in ((azul, my - h), (rojo, my + h)):
                c.create_oval(mx - r * 1.5, yy - r * 1.5, mx + r * 1.5, yy + r * 1.5, fill=_apagar(color, 0.45), outline="", tags="fx")
                c.create_oval(mx - r, yy - r, mx + r, yy + r, fill=color, outline="#ffffff", width=1, tags="fx")
        elif t < CARGA + DISPARO:
            q = (t - CARGA) / DISPARO
            x = mx + d * 280 * _ease(q)
            r = 20 + 8 * q
            for i in range(5, 0, -1):
                c.create_oval(x - d * i * 16 - r * (1 - i * 0.14), my - r * (1 - i * 0.14),
                              x - d * i * 16 + r * (1 - i * 0.14), my + r * (1 - i * 0.14),
                              fill=_apagar(morado, 0.55 - i * 0.09), outline="", tags="fx")
            _esfera(c, x, my, r, [morado, "#e5d4ff", self.colores[2]], self.fase)
            if t == CARGA:
                _destello(c, mx, my, 0.0, 26)
        elif t < CARGA + DISPARO + IMPACTO:
            p = (t - CARGA - DISPARO) / IMPACTO
            ex = mx + d * 280
            _destello(c, ex, my, p, 40)
            _anillos(c, ex, my, p, [morado, azul, rojo], 175)

    def _fx_brasas(self, c, t, ox, oy):
        d = self.direccion
        ang = 0 if d > 0 else 180
        cy = oy - 6
        if t < CARGA and self.sprite_propio:
            return
        if t < CARGA:
            p = _ease(t / CARGA)
            R = 6 + 16 * p + random.uniform(0, 2)
            c.create_oval(ox - R * 1.6, cy - R * 1.6, ox + R * 1.6, cy + R * 1.6, fill=_apagar(self.colores[0], 0.35), outline="", tags="fx")
            c.create_oval(ox - R, cy - R, ox + R, cy + R, fill=self.colores[2], outline=self.colores[1], width=2, tags="fx")
        elif t < CARGA + DISPARO:
            q = (t - CARGA) / DISPARO
            for i in range(5):
                ri = 40 + 300 * _ease(q) - i * 22
                if ri < 10:
                    continue
                c.create_arc(ox - ri, cy - ri, ox + ri, cy + ri, start=ang - 38, extent=76, style="arc",
                             outline=_apagar(self.colores[i % 2], 1 - q * 0.85 - i * 0.08), width=max(2, 9 - i * 2), tags="fx")
            ex = ox + d * (50 + 250 * _ease(q))
            R = 20 + 6 * q
            for i in range(4, 0, -1):
                rr = R * (1 - 0.15 * i)
                c.create_oval(ex - d * i * 18 - rr, cy - rr, ex - d * i * 18 + rr, cy + rr,
                              fill=_apagar(self.colores[2], 0.55 - i * 0.1), outline="", tags="fx")
            c.create_oval(ex - R * 1.3, cy - R * 1.3, ex + R * 1.3, cy + R * 1.3, fill=_apagar(self.colores[0], 0.4), outline="", tags="fx")
            c.create_oval(ex - R, cy - R, ex + R, cy + R, fill="#0c0508", outline=self.colores[0], width=4, tags="fx")
        elif t < CARGA + DISPARO + IMPACTO:
            p = (t - CARGA - DISPARO) / IMPACTO
            fx = ox + d * 300
            _destello(c, fx, cy, p, 34)
            _anillos(c, fx, cy, p, [self.colores[0], self.colores[1]], 160, 2)
            _rayos(c, fx, cy, p, self.colores[1], 12)

    def _fx_espiral(self, c, t, ox, oy):
        d = self.direccion
        hx, hy = ox + d * 54, oy + 8
        if CARGA <= t < CARGA + DISPARO:
            q = (t - CARGA) / DISPARO
            x = hx + d * 266 * _ease(q)
            R = 21 + 6 * q
            for i in range(4, 0, -1):
                c.create_oval(x - d * i * 20 - R * (1 - 0.18 * i), hy - R * (1 - 0.18 * i),
                              x - d * i * 20 + R * (1 - 0.18 * i), hy + R * (1 - 0.18 * i),
                              fill=_apagar(self.colores[0], 0.5 - i * 0.09), outline="", tags="fx")
            _esfera(c, x, hy, R, [self.colores[0], self.colores[1], self.colores[2]], self.fase)
        elif CARGA + DISPARO <= t < CARGA + DISPARO + IMPACTO:
            p = (t - CARGA - DISPARO) / IMPACTO
            ex = hx + d * 266
            _destello(c, ex, hy, p, 52)
            _anillos(c, ex, hy, p, [self.colores[0], self.colores[1], "#ffffff"], 190)
            _rayos(c, ex, hy, p, self.colores[1], 16)

    def _fx_rayo(self, c, t, ox, oy):
        d = self.direccion
        x0, y0 = ox + d * 52, oy + 4
        largo = 430
        if t < CARGA:
            return
        if t < CARGA + DISPARO:
            q = (t - CARGA) / DISPARO
            L = largo * _ease(min(1.0, q * 5))
            grosor = 1.0 if q < 0.65 else max(0.0, 1 - (q - 0.65) / 0.35)
            x1 = x0 + d * L
            for h, color, k in ((42, self.colores[2], 0.45), (26, self.colores[0], 1.0), (11, "#ffffff", 1.0)):
                hh = h * grosor
                if hh < 1:
                    continue
                c.create_polygon([x0, y0 - hh / 2, x1, y0 - hh * 0.38, x1 + d * 12, y0, x1, y0 + hh * 0.38, x0, y0 + hh / 2],
                                 fill=_apagar(color, k), outline="", tags="fx")
            for _ in range(7):
                sx = x0 + d * random.uniform(0, L)
                sy = y0 + random.uniform(-26, 26) * grosor
                r = random.uniform(2, 4)
                c.create_oval(sx - r, sy - r, sx + r, sy + r, fill=_apagar(self.colores[1], 0.9), outline="", tags="fx")
            _destello(c, x0, y0, q * 3, 30)
        elif t < CARGA + DISPARO + IMPACTO:
            p = (t - CARGA - DISPARO) / IMPACTO
            ex = x0 + d * largo
            _destello(c, ex, y0, p, 36)
            _anillos(c, ex, y0, p, [self.colores[0], self.colores[1], self.colores[2]], 170)
            _rayos(c, ex, y0, p, self.colores[1], 12)
