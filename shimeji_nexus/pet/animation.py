import math
import os

from PIL import Image, ImageOps, ImageTk


class AnimationEngine:
    """Precalcula y sirve los frames de sprite para cada estado/dirección de la mascota."""

    def __init__(self, ruta_personaje, config, tamano):
        self.tamano = tamano
        self.direccion = 1
        self.tick_animacion = 0
        self.frames_cache = self._cargar_frames(ruta_personaje, config)

    def _abrir_imagen(self, path):
        img = Image.open(path).convert("RGBA")
        if any(p[3] < 255 for p in img.getdata()):
            return img.resize((self.tamano, self.tamano), Image.Resampling.NEAREST)
        datas = list(img.getdata())
        newData = [(0, 0, 0, 0) if (p[0] > 240 and p[1] > 240 and p[2] > 240) else p for p in datas]
        img.putdata(newData)
        return img.resize((self.tamano, self.tamano), Image.Resampling.NEAREST)

    def _precalcular_par(self, img):
        der, izq = [], []
        img_izq = ImageOps.mirror(img)
        for i in range(16):
            ang = math.sin((i / 16) * math.pi * 2) * 4
            der.append(ImageTk.PhotoImage(img.rotate(ang)))
            izq.append(ImageTk.PhotoImage(img_izq.rotate(-ang)))
        return {"der": der, "izq": izq}

    def _cargar_frames(self, ruta, config):
        cache = {}
        cfg = config.get("frames")
        if cfg:
            for estado, archivo in cfg.items():
                cache[estado] = self._precalcular_par(self._abrir_imagen(os.path.join(ruta, archivo)))
        else:
            archivo = config.get("imagen", "rias.png")
            cache["default"] = self._precalcular_par(self._abrir_imagen(os.path.join(ruta, archivo)))
        return cache

    def avanzar_tick(self):
        self.tick_animacion = (self.tick_animacion + 1) % 16

    def frame_actual(self, estado):
        estado_valido = estado if estado in self.frames_cache else ("default" if "default" in self.frames_cache else list(self.frames_cache.keys())[0])
        par = self.frames_cache.get(estado_valido, list(self.frames_cache.values())[0])
        frames = par["der"] if self.direccion == 1 else par["izq"]
        return frames[self.tick_animacion]

    def offset_y_para_estado(self, estado):
        if estado == "caminando":
            return abs(math.sin((self.tick_animacion / 16) * math.pi * 2)) * 6
        if estado == "siguiendo":
            return abs(math.sin((self.tick_animacion / 16) * math.pi * 2)) * 5
        if estado == "bailando":
            return abs(math.sin((self.tick_animacion / 16) * math.pi * 4)) * 15
        if estado in ("flotando", "magia"):
            return math.sin((self.tick_animacion / 16) * math.pi * 2) * 12
        return 0
