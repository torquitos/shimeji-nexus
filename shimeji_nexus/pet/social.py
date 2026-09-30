import math
import random
import time

from shimeji_nexus.ipc import shared_state


class SocialBehavior:
    """Compartir estado e interactuar con otras mascotas vía shared_state."""

    def __init__(self, shared_dir, nombre):
        self.shared_dir = shared_dir
        self.nombre = nombre
        self.ultimo_saludo = ""

    def compartir_estado(self, x_pos, y_pos, direccion, estado, tamano):
        data = {
            "nombre": self.nombre,
            "x": x_pos, "y": int(y_pos),
            "direccion": direccion,
            "estado": estado,
            "tamano": tamano,
            "timestamp": time.time(),
        }
        shared_state.escribir_estado(self.shared_dir, self.nombre, data)

    def leer_vecinos(self):
        return shared_state.leer_vecinos(self.shared_dir, self.nombre)

    def limpiar_estado(self):
        shared_state.limpiar_estado(self.shared_dir, self.nombre)

    def buscar_vecino(self, vecinos, nombre):
        for v in vecinos:
            if v.get("nombre") == nombre:
                return v
        return None

    def procesar_interacciones(self, x_pos, y_pos, estado, tick_interaccion, mostrar_comentario):
        """Devuelve un dict con las mutaciones a aplicar: x_pos, direccion, estado, pasos_restantes,
        siguiendo_a, seguir_restantes, tick_interaccion (solo las claves que cambian)."""
        cambios = {}
        vecinos = self.leer_vecinos()
        for v in vecinos:
            dx = v["x"] - x_pos
            dy = v["y"] - y_pos
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 150:
                continue
            if dist < 40:
                if dist > 0:
                    empuje = int(8 / max(dist, 1))
                    x_pos -= int(dx / dist * empuje)
                    cambios["x_pos"] = x_pos
                direccion = -1 if dx > 0 else 1
                cambios["direccion"] = direccion
                if estado == "quieto" and tick_interaccion > 30:
                    cambios["estado"] = "saludo"
                    cambios["pasos_restantes"] = 20
                    reacciones = ["¡Oye!", "¡Quita!", "Eh...", "¡Casi chocamos!", "Ups~"]
                    mostrar_comentario(random.choice(reacciones))
                    cambios["tick_interaccion"] = 0
            elif dist < 100 and estado == "quieto" and tick_interaccion > 50:
                cambios["direccion"] = -1 if dx > 0 else 1
                r = random.random()
                if r < 0.35:
                    cambios["estado"] = "saludo"
                    cambios["pasos_restantes"] = 25
                    saludos = ["¡Hola!", "Hey!", "¿Qué tal?", f"¡{v.get('nombre','')}!", "Que gusto~"]
                    msg = random.choice(saludos)
                    if msg != self.ultimo_saludo:
                        mostrar_comentario(msg)
                        self.ultimo_saludo = msg
                elif r < 0.55:
                    cambios["estado"] = "bailando"
                    cambios["pasos_restantes"] = 30
                    mostrar_comentario(random.choice(["¡A bailar!", "Sigue el ritmo~", "*danza*"]))
                elif r < 0.70:
                    cambios["estado"] = "siguiendo"
                    cambios["siguiendo_a"] = v.get("nombre")
                    cambios["seguir_restantes"] = random.randint(40, 100)
                else:
                    cambios["estado"] = "flotando"
                    cambios["pasos_restantes"] = 40
                    mostrar_comentario(random.choice(["¡A volar!", "*flota*", "Arriba~"]))
                cambios["tick_interaccion"] = 0
            elif dist < 140 and estado == "quieto" and tick_interaccion > 90 and v.get("estado") == "caminando":
                if random.random() < 0.15:
                    cambios["estado"] = "siguiendo"
                    cambios["siguiendo_a"] = v.get("nombre")
                    cambios["seguir_restantes"] = random.randint(30, 70)
                    cambios["tick_interaccion"] = 0
        return cambios
