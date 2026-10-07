import math
import os
import time

from PIL import Image, ImageOps, ImageTk


class AnimationEngine:
    """Precalcula y sirve los frames de sprite para cada estado/dirección de la mascota."""

    def __init__(self, ruta_personaje, config, tamano):
        self.tamano = tamano
        self.direccion = 1
        self.tick_animacion = 0
        self.frames_cache = self._cargar_frames(ruta_personaje, config)
        self.anim = self._cargar_animaciones(ruta_personaje, config)
        self.indice_magia = 0

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

    ALIAS = {"siguiendo": "caminando", "cayendo": "quieto", "flotando": "quieto", "bailando": "saludo", "arrastrando": "quieto"}

    def _cargar_animaciones(self, ruta, config):
        """Secuencias de frames reales (config.json -> 'animaciones'). Si no hay, queda vacio y se usa
        la animacion por rotacion de siempre."""
        anim = {}
        for estado, datos in (config.get("animaciones") or {}).items():
            frames = []
            for archivo in datos.get("frames", []):
                try:
                    frames.append(Image.open(os.path.join(ruta, archivo)).convert("RGBA"))
                except OSError:
                    continue
            if frames:
                anim[estado] = {
                    "der": [ImageTk.PhotoImage(f) for f in frames],
                    "izq": [ImageTk.PhotoImage(ImageOps.mirror(f)) for f in frames],
                    "fps": float(datos.get("fps", 8)),
                }
        return anim

    def _frame_de_secuencia(self, estado):
        nombre = estado if estado in self.anim else self.ALIAS.get(estado, "quieto")
        datos = self.anim.get(nombre) or self.anim.get("quieto")
        if not datos:
            return None
        lista = datos["der"] if self.direccion == 1 else datos["izq"]
        if nombre == "magia":
            return lista[min(self.indice_magia, len(lista) - 1)]
        return lista[int(time.time() * datos["fps"]) % len(lista)]

    def fase_caminata(self):
        """Posicion (0 a 1) dentro del ciclo de pasos; solo si el personaje tiene caminata animada."""
        datos = self.anim.get("caminando")
        if not datos:
            return None
        return (time.time() * datos["fps"] / len(datos["der"])) % 1.0

    def balanceo_x(self):
        fase = self.fase_caminata()
        return 0 if fase is None else 2.5 * math.sin(2 * math.pi * fase)

    def avanzar_tick(self):
        self.tick_animacion = (self.tick_animacion + 1) % 16

    def frame_actual(self, estado):
        if self.anim:
            frame = self._frame_de_secuencia(estado)
            if frame is not None:
                return frame
        if estado == "magia" and "saludo" in self.frames_cache:
            estado = "saludo"
        estado_valido = estado if estado in self.frames_cache else ("default" if "default" in self.frames_cache else list(self.frames_cache.keys())[0])
        par = self.frames_cache.get(estado_valido, list(self.frames_cache.values())[0])
        frames = par["der"] if self.direccion == 1 else par["izq"]
        return frames[self.tick_animacion]

    def offset_y_para_estado(self, estado):
        if self.anim and estado in ("caminando", "siguiendo"):
            return abs(math.sin(2 * math.pi * (self.fase_caminata() or 0))) * 5
        if estado == "caminando":
            return abs(math.sin((self.tick_animacion / 16) * math.pi * 2)) * 6
        if estado == "siguiendo":
            return abs(math.sin((self.tick_animacion / 16) * math.pi * 2)) * 5
        if estado == "bailando":
            return abs(math.sin((self.tick_animacion / 16) * math.pi * 4)) * 15
        if estado in ("flotando", "magia"):
            return math.sin((self.tick_animacion / 16) * math.pi * 2) * 12
        return 0
