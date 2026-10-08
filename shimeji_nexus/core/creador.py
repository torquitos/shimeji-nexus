"""Crea la carpeta de un personaje nuevo: config.json, imagenes y, si hay hoja de sprites, sus animaciones."""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

from shimeji_nexus.core.paths import base_dir
from shimeji_nexus.ui.theme import siguiente_color_rotativo

PERSONAJES = os.path.join(base_dir(), "personajes")
HERRAMIENTA = os.path.join(base_dir(), "herramientas", "preparar_sprites.py")
TEXTO_BASE = "Actúa como [personaje] de [anime]. Eres un personaje amigable y carismático."


class ErrorCreacion(Exception):
    pass


def carpeta_de(nombre):
    return re.sub(r"[^a-z0-9_]", "", nombre.lower().replace(" ", "_"))


def siguiente_color():
    existentes = [d for d in os.listdir(PERSONAJES) if os.path.isdir(os.path.join(PERSONAJES, d))] if os.path.isdir(PERSONAJES) else []
    return siguiente_color_rotativo(len(existentes))


def personalidad(nombre, serie, texto):
    texto = texto.strip()
    if texto and texto != TEXTO_BASE:
        return texto
    de = f" de {serie}" if serie else ""
    return f"Actúa como {nombre}{de}. Eres un personaje amigable, carismático y divertido. Hablas con energía y siempre animas al usuario."


def dependencias_listas():
    """La hoja de sprites se procesa con numpy y scipy (solo la herramienta, no la app)."""
    return all(importlib.util.find_spec(m) is not None for m in ("numpy", "scipy"))


def instalar_dependencias():
    r = subprocess.run([sys.executable, "-m", "pip", "install", "numpy", "scipy"], capture_output=True, text=True)
    return r.returncode == 0, (r.stderr or r.stdout)[-300:]


def _copiar(origen, carpeta, nombre):
    destino = nombre + (os.path.splitext(origen)[1] or ".png")
    shutil.copy2(origen, os.path.join(carpeta, destino))
    return destino


def crear(nombre, serie="", texto="", imagen="", hoja="", retrato=""):
    """Crea el personaje y devuelve su carpeta. Lanza ErrorCreacion con un mensaje legible si algo falla."""
    nombre = nombre.strip()
    if not nombre:
        raise ErrorCreacion("El nombre es obligatorio.")
    if not (hoja or imagen):
        raise ErrorCreacion("Elige una imagen o una hoja de sprites.")
    if hoja and not dependencias_listas():
        raise ErrorCreacion("FALTAN_DEPENDENCIAS")
    ruta = os.path.join(PERSONAJES, carpeta_de(nombre))
    if os.path.exists(ruta):
        raise ErrorCreacion("Ya existe un personaje con ese nombre.")
    color = siguiente_color()
    os.makedirs(ruta)
    try:
        config = {"nombre": nombre, "personalidad": personalidad(nombre, serie, texto), "saludo": f"¡Hola! Soy {nombre}~",
                  "color_globo": "#E1E1E6", "color_texto": color}
        for origen, destino in ((imagen, "quieto"), (retrato, "retrato")):
            if origen:
                config["imagen"] = _copiar(origen, ruta, destino)
        with open(os.path.join(ruta, "config.json"), "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        if hoja:
            _procesar_hoja(_copiar(hoja, ruta, "hoja_animaciones"), ruta)
    except Exception as e:
        shutil.rmtree(ruta, ignore_errors=True)
        raise e if isinstance(e, ErrorCreacion) else ErrorCreacion(str(e))
    return ruta


def _procesar_hoja(archivo, ruta):
    r = subprocess.run([sys.executable, HERRAMIENTA, os.path.join(ruta, archivo), ruta], capture_output=True, text=True)
    if r.returncode != 0:
        raise ErrorCreacion("No se pudo procesar la hoja de sprites. Revisa que tenga 8 columnas x 3 filas y fondo de un solo color.\n\n" + (r.stderr or r.stdout)[-250:])
