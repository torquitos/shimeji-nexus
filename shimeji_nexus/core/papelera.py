"""Quitar un personaje de la lista sin perderlo del todo: su carpeta pasa a papelera/ y se puede devolver a mano."""
import os
import shutil
import time

from shimeji_nexus.core.memoria import Memoria
from shimeji_nexus.core.paths import base_dir


def eliminar(carpeta, nombre):
    """Mueve personajes/<carpeta> a papelera/ y borra lo que hablaron. Devuelve la nueva ruta."""
    origen = os.path.join(base_dir(), "personajes", carpeta)
    destino_base = os.path.join(base_dir(), "papelera")
    os.makedirs(destino_base, exist_ok=True)
    destino = os.path.join(destino_base, f"{carpeta}_{time.strftime('%Y%m%d_%H%M%S')}")
    shutil.move(origen, destino)
    Memoria(nombre).olvidar()
    return destino
