import json
import os

from shimeji_nexus.ui.theme import ACCENT_DEFAULT, acento_desde_color_texto, blend_color


def escanear(ruta_personajes, on_carpeta=None):
    """Escanea la carpeta de personajes y devuelve un dict {nombre: info}.
    on_carpeta(carpeta) se llama antes de procesar cada carpeta (para logging opcional)."""
    if not os.path.exists(ruta_personajes):
        os.makedirs(ruta_personajes)
    personajes_datos = {}
    carpetas = sorted(os.listdir(ruta_personajes))
    for carpeta in carpetas:
        if on_carpeta:
            on_carpeta(carpeta)
        conf = os.path.join(ruta_personajes, carpeta, "config.json")
        if not os.path.isdir(os.path.join(ruta_personajes, carpeta)) or not os.path.exists(conf):
            continue
        with open(conf, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        nombre = data["nombre"]
        color_texto_raw = data.get("color_texto")
        color_acento = acento_desde_color_texto(color_texto_raw) if color_texto_raw else ACCENT_DEFAULT
        personajes_datos[nombre] = {
            "folder": carpeta, "nombre": nombre,
            "personalidad": data["personalidad"],
            "imagen": data.get("imagen", "rias.png"),
            "color_globo": data.get("color_globo"),
            "color_texto": color_texto_raw,
            "color_acento": color_acento,
            "color_acento_soft": blend_color(color_acento, "#0b0b0f", 0.13),
            "color_acento_preview": blend_color(color_acento, "#12121a", 0.30),
        }
    return personajes_datos
