import os

from dotenv import set_key

from shimeji_nexus.core.paths import base_dir

RUTA = os.path.join(base_dir(), ".env")


def _guardar(variable, valor):
    if not os.path.exists(RUTA):
        open(RUTA, "a", encoding="utf-8").close()
    set_key(RUTA, variable, valor, quote_mode="never")
    os.environ[variable] = valor


def guardar_clave(variable, clave):
    limpia = clave.strip().strip("'\"")
    if limpia:
        _guardar(variable, limpia)


def guardar_proveedor(proveedor):
    _guardar("AI_PROVIDER", proveedor)


def enmascarar(clave):
    return "•" * 8 + clave[-4:] if clave and len(clave) > 8 else ""
