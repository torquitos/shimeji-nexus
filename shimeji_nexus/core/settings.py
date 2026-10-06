import json
import os

from shimeji_nexus.core.paths import base_dir

RUTA = os.path.join(base_dir(), "settings_cache.json")

DEFAULT = {
    "monitoreo_ia": True,
    "particulas": True,
    "sonido": True,
    "transparencia": 1.0,
    "velocidad": 1.0,
    "habilidad_auto": True,
    "pomodoro_trabajo": 25,
    "pomodoro_descanso": 5,
}

_cache = None


def cargar():
    global _cache
    if _cache is not None:
        return _cache
    if os.path.exists(RUTA):
        try:
            with open(RUTA, "r", encoding="utf-8") as f:
                _cache = {**DEFAULT, **json.load(f)}
                return _cache
        except Exception:
            pass
    _cache = dict(DEFAULT)
    return _cache


def guardar(settings):
    global _cache
    _cache = settings
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
