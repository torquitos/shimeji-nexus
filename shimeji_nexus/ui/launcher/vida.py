import math
import random
import tkinter as tk

from PIL import ImageTk

from shimeji_nexus.ui import preview, theme
from shimeji_nexus.ui.launcher.hero import HERO_H, HERO_W

AMBIENTE = 16
PERIODO_MS = 40


class VidaMixin:
    """Portada viva: el personaje flota, el aire se llena de particulas de su color y un clic
    sobre el provoca un estallido con el nombre de su habilidad."""

    def _iniciar_vida(self):
        self._t = 0
        self._tecnica_t = None
        self._entrada = 99
        self._ambiente = []
        self._estallido = []
        self._spr_pos = (0, 0)
        self._spr_caja = (0, 0, 0, 0)
        self.canvas_hero.bind("<Button-1>", self._clic_hero)
        self.root.after(PERIODO_MS, self._vida_tick)

    def _poner_sprite_vivo(self, sprite, info):
        """Muestra el sprite sobre el fondo, hace que entre subiendo y reinicia las particulas."""
        c = self.canvas_hero
        for p in self._estallido:
            c.delete(p["id"])
        self._estallido = []
        self._tecnica_t = None
        c.delete("fx")
        if sprite is None:
            self._spr_foto = None
            c.itemconfig(self._hero_sprite, image="")
            return
        self._spr_foto = ImageTk.PhotoImage(sprite)
        self._spr_pos = preview.posicion_sprite(sprite, HERO_W, HERO_H)
        x, y = self._spr_pos
        self._spr_caja = (x, y, x + sprite.width, y + sprite.height)
        c.itemconfig(self._hero_sprite, image=self._spr_foto)
        c.coords(self._hero_sprite, x, y + 30)
        self._entrada = 0
        self._reiniciar_ambiente(info)

    def _reiniciar_ambiente(self, info):
        c = self.canvas_hero
        for p in self._ambiente:
            c.delete(p["id"])
        x0, y0, x1, y1 = preview.ESCENARIO
        y0, y1 = y0 + 20, y1 - 30
        colores = [info["color_acento"]] + info["habilidad"]["colores"][:2]
        self._ambiente = []
        for _ in range(AMBIENTE):
            p = {"x": random.uniform(x0 + 14, x1 - 14), "y": random.uniform(y0, y1), "vy": random.uniform(0.25, 0.9),
                 "r": random.uniform(1.6, 3.6), "fase": random.uniform(0, 6.28), "col": random.choice(colores)}
            p["id"] = c.create_oval(0, 0, 0, 0, outline="")
            c.tag_lower(p["id"], self._hero_sprite)
            self._ambiente.append(p)

    def _vida_tick(self):
        try:
            self.root.after(PERIODO_MS, self._vida_tick)
            if self.root.state() == "withdrawn" or self.personaje_seleccionado is None:
                return
        except tk.TclError:
            return
        self._t += 1
        self._mover_sprite()
        self._mover_ambiente()
        self._mover_estallido()

    def _mover_sprite(self):
        if getattr(self, "_spr_foto", None) is None:
            return
        self._entrada += 1
        subida = 30 * max(0.0, 1 - self._entrada / 12) ** 2
        flotar = 4 * math.sin(self._t * 0.09)
        x, y = self._spr_pos
        self.canvas_hero.coords(self._hero_sprite, x, y + flotar + subida)

    def _mover_ambiente(self):
        c = self.canvas_hero
        x0, y0, x1, y1 = preview.ESCENARIO
        y0, y1 = y0 + 20, y1 - 30
        for p in self._ambiente:
            p["y"] -= p["vy"]
            if p["y"] < y0 - 20:
                p["y"], p["x"] = y1 - random.uniform(0, 60), random.uniform(x0 + 14, x1 - 14)
            x = min(x1 - 8, max(x0 + 8, p["x"] + 10 * math.sin(self._t * 0.04 + p["fase"])))
            brillo = max(0.0, min(1.0, (p["y"] - y0 + 20) / (y1 - y0 + 20)))
            c.coords(p["id"], x - p["r"], p["y"] - p["r"], x + p["r"], p["y"] + p["r"])
            c.itemconfig(p["id"], fill=theme.blend_color(p["col"], theme.BG, 0.15 + 0.75 * brillo))

    def _clic_hero(self, e):
        x0, y0, x1, y1 = self._spr_caja
        if self.personaje_seleccionado is None or not (x0 <= e.x <= x1 and y0 <= e.y <= y1):
            return
        info = self.personajes_datos[self.personaje_seleccionado]
        colores = [info["color_acento"]] + info["habilidad"]["colores"]
        cx, cy = (x0 + x1) / 2, y0 + (y1 - y0) * 0.45
        for _ in range(34):
            a, v = random.uniform(0, 6.28), random.uniform(3, 9)
            self._estallido.append({"k": "chispa", "x": cx, "y": cy, "vx": math.cos(a) * v, "vy": math.sin(a) * v - 1,
                                    "r": random.uniform(2, 5), "col": random.choice(colores), "v": 1.0, "id": self.canvas_hero.create_oval(0, 0, 0, 0, outline="")})
        for i in range(2):
            self._estallido.append({"k": "anillo", "x": cx, "y": cy, "r": 10 - i * 8, "col": colores[i], "v": 1.0,
                                    "id": self.canvas_hero.create_oval(0, 0, 0, 0, fill="")})
        nombre = info["habilidad"]["nombre"].upper()
        self._estallido.append({"k": "letrero", "x": cx, "y": y0 - 6, "col": info["color_acento"], "v": 1.0,
                                "id": self.canvas_hero.create_text(cx, y0 - 6, text=nombre, font=theme.FONT_HEADING, fill=theme.TEXT)})

    def _mover_estallido(self):
        c = self.canvas_hero
        vivos = []
        for p in self._estallido:
            p["v"] -= 0.045
            if p["v"] <= 0:
                c.delete(p["id"])
                continue
            color = theme.blend_color(p["col"], theme.BG, p["v"])
            if p["k"] == "chispa":
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vx"] *= 0.94
                p["vy"] = p["vy"] * 0.94 + 0.18
                r = p["r"] * (0.4 + p["v"] * 0.6)
                c.coords(p["id"], p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r)
                c.itemconfig(p["id"], fill=color)
            elif p["k"] == "anillo":
                p["r"] += 9
                c.coords(p["id"], p["x"] - p["r"], p["y"] - p["r"], p["x"] + p["r"], p["y"] + p["r"])
                c.itemconfig(p["id"], outline=color, width=max(1, int(5 * p["v"])))
            else:
                p["y"] -= 1.2
                c.coords(p["id"], p["x"], p["y"])
                c.itemconfig(p["id"], fill=theme.blend_color("#ffffff", theme.BG, min(1.0, p["v"] * 1.6)))
            vivos.append(p)
        self._estallido = vivos
