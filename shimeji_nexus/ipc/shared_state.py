import json
import os
import time

_listdir_cache = {}
_LISTDIR_TTL_SEG = 1.0


def escribir_estado(shared_dir, nombre, data):
    """Escritura atómica: escribe a un archivo temporal y lo reemplaza,
    para que un lector nunca vea un JSON a medio escribir."""
    try:
        ruta_final = os.path.join(shared_dir, f"{nombre}.json")
        ruta_tmp = os.path.join(shared_dir, f".{nombre}.tmp")
        with open(ruta_tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(ruta_tmp, ruta_final)
    except Exception:
        pass


def _listar_json(shared_dir):
    ahora = time.time()
    cache = _listdir_cache.get(shared_dir)
    if cache and ahora - cache[0] < _LISTDIR_TTL_SEG:
        return cache[1]
    try:
        archivos = [a for a in os.listdir(shared_dir) if a.endswith(".json")]
    except Exception:
        archivos = []
    _listdir_cache[shared_dir] = (ahora, archivos)
    return archivos


def leer_vecinos(shared_dir, mi_nombre, max_edad_seg=3):
    vecinos = []
    ahora = time.time()
    for archivo in _listar_json(shared_dir):
        nombre = archivo[:-5]
        if nombre == mi_nombre:
            continue
        ruta = os.path.join(shared_dir, archivo)
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)
            if ahora - data.get("timestamp", 0) < max_edad_seg:
                vecinos.append(data)
        except Exception:
            pass
    return vecinos


def limpiar_estado(shared_dir, nombre):
    try:
        ruta = os.path.join(shared_dir, f"{nombre}.json")
        if os.path.exists(ruta):
            os.remove(ruta)
    except Exception:
        pass
