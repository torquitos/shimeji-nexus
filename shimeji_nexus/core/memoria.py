"""Memoria de conversacion de cada personaje: los ultimos intercambios y como se llama el usuario.
Se guarda en memoria/<personaje>.json y se le pasa a la IA como contexto."""
import json
import os
import re

from shimeji_nexus.core import settings as settings_manager
from shimeji_nexus.core.paths import base_dir

MAX_TURNOS = 10
CARPETA = os.path.join(base_dir(), "memoria")


def nombre_usuario():
    return settings_manager.cargar().get("nombre_usuario") or ""


def guardar_nombre_usuario(nombre):
    ajustes = settings_manager.cargar()
    ajustes["nombre_usuario"] = nombre.strip()
    settings_manager.guardar(ajustes)


class Memoria:
    def __init__(self, personaje):
        self.ruta = os.path.join(CARPETA, re.sub(r"[^\w-]", "_", personaje.lower()) + ".json")
        self.turnos = self._cargar()

    def _cargar(self):
        try:
            with open(self.ruta, encoding="utf-8") as f:
                return list(json.load(f))[-MAX_TURNOS:]
        except Exception:
            return []

    def recordar(self, pregunta, respuesta):
        self.turnos = (self.turnos + [[pregunta, respuesta]])[-MAX_TURNOS:]
        try:
            os.makedirs(CARPETA, exist_ok=True)
            with open(self.ruta, "w", encoding="utf-8") as f:
                json.dump(self.turnos, f, ensure_ascii=False)
        except OSError:
            pass

    def olvidar(self):
        self.turnos = []
        try:
            os.remove(self.ruta)
        except OSError:
            pass

    def contexto(self):
        """Texto para anteponer al mensaje: nombre del usuario y conversacion reciente."""
        partes = []
        if nombre_usuario():
            partes.append(f"El usuario se llama {nombre_usuario()}.")
        if self.turnos:
            partes.append("Conversación reciente (para que seas coherente):")
            partes += [f"Usuario: {q}\nTú: {a}" for q, a in self.turnos]
        return "\n".join(partes)
