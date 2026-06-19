import json
import os
import sys

def _base():
    return os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

RUTA = os.path.join(_base(), "settings_cache.json")

DEFAULT = {
    "monitoreo_ia": True,
    "particulas": True,
    "sonido": True,
    "transparencia": 1.0,
    "velocidad": 1.0,
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
