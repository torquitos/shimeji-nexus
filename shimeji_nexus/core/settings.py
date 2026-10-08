import json
import os
import time

from shimeji_nexus.core.paths import base_dir

RUTA = os.path.join(base_dir(), "settings_cache.json")

DEFAULT = {
    "monitoreo_ia": True,
    "particulas": True,
    "sonido": True,
    "transparencia": 1.0,
    "velocidad": 1.0,
    "habilidad_auto": True,
    "ocultar_pantalla_completa": True,
    "concentracion": False,
    "ventana_launcher": None,
    "nombre_usuario": "",
    "pomodoro_trabajo": 25,
    "pomodoro_descanso": 5,
}

_cache = None
_mtime = 0
_revisado = 0


def _modificado():
    try:
        return os.path.getmtime(RUTA)
    except OSError:
        return 0


def cargar():
    """Ajustes en cache; si otro proceso (Ajustes) cambio el archivo, se recargan como mucho cada segundo."""
    global _cache, _mtime, _revisado
    ahora = time.time()
    if _cache is not None and ahora - _revisado < 1:
        return _cache
    _revisado = ahora
    m = _modificado()
    if _cache is not None and m == _mtime:
        return _cache
    _mtime = m
    if m:
        try:
            with open(RUTA, "r", encoding="utf-8") as f:
                _cache = {**DEFAULT, **json.load(f)}
                return _cache
        except Exception:
            pass
    _cache = _cache or dict(DEFAULT)
    return _cache


def guardar(settings):
    global _cache, _mtime
    _cache = settings
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
    _mtime = _modificado()
