import os
import time

from shimeji_nexus.audio import sound_manager
from shimeji_nexus.core import image_utils
from shimeji_nexus.core.paths import base_dir
from shimeji_nexus.pet.habilidades import EfectoHabilidad
from shimeji_nexus.pet.habilidades.config import TOTAL


class TecnicaMixin:
    """'Ver tecnica': reproduce en la portada el mismo corte de camara y ataque que hace la mascota."""

    def _ver_tecnica(self):
        if self._tecnica_t is not None or self.personaje_seleccionado is None:
            return
        info = self.personajes_datos[self.personaje_seleccionado]
        try:
            retrato = image_utils.cargar_avatar(os.path.join(base_dir(), "personajes", info["folder"], info["imagen"]), 84)
        except Exception:
            retrato = None
        self._efecto_prev = EfectoHabilidad(self.canvas_hero, self._hero_sprite, 200, info["habilidad"], None, False, None,
                                            retrato=retrato, autor=info["nombre"])
        self._efecto_prev.direccion = -1
        sound_manager.reproducir("hab_" + info["habilidad"]["forma"])
        self._tecnica_t = 0
        self._tecnica_ini = time.time()
        self._tecnica_tick()

    def _tecnica_tick(self):
        c, ef = self.canvas_hero, self._efecto_prev
        t = None if self._tecnica_t is None else int((time.time() - self._tecnica_ini) / 0.035)
        c.delete("fx")
        if t is None or t > TOTAL:
            self._tecnica_t = None
            return
        x0, y0, x1, y1 = self._spr_caja
        ox, oy = (x0 + x1) / 2, y0 + (y1 - y0) * 0.45
        ef.fase += 0.35
        ef._letrero(c, t, ox, oy)
        getattr(ef, "_fx_" + ef.forma)(c, t, ox, oy)
        self._tecnica_t = t
        self.root.after(35, self._tecnica_tick)
