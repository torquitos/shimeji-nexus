import math
import random
import time

from shimeji_nexus.ipc import shared_state


class SocialBehavior:
    """Compartir estado e interactuar con otras mascotas vía shared_state."""

    def __init__(self, shared_dir, nombre, voz):
        self.voz = voz
        self.shared_dir = shared_dir
        self.nombre = nombre
        self.ultimo_saludo = ""
        self.evento = None
        self._ev_visto = {}

    def compartir_estado(self, x_pos, y_pos, direccion, estado, tamano):
        data = {
            "nombre": self.nombre,
            "x": x_pos, "y": int(y_pos),
            "direccion": direccion,
            "estado": estado,
            "tamano": tamano,
            "timestamp": time.time(),
            "evento": self.evento if self.evento and time.time() - self.evento["ts"] < 4 else None,
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

    DISTANCIA_MIN = 80

    def emitir(self, tipo, para="*"):
        """Avisa a los demas de algo que acabo de hacer (se manda dentro del estado compartido)."""
        self.evento = {"tipo": tipo, "para": para, "ts": time.time()}

    def procesar_interacciones(self, x_pos, y_pos, estado, tick_interaccion, mostrar_comentario):
        """Devuelve un dict con las mutaciones a aplicar: x_pos, direccion, estado, pasos_restantes,
        siguiendo_a, seguir_restantes, tick_interaccion, responder (solo las claves que cambian)."""
        cambios = {}
        ahora = time.time()
        for v in self.leer_vecinos():
            dx = v["x"] - x_pos
            dy = v["y"] - y_pos
            dist = math.sqrt(dx * dx + dy * dy)
            hacia = 1 if dx > 0 else -1

            ev = v.get("evento")
            if (ev and ev.get("para") in (self.nombre, "*") and ahora - ev.get("ts", 0) < 3
                    and self._ev_visto.get(v["nombre"]) != ev["ts"] and dist < 450):
                self._ev_visto[v["nombre"]] = ev["ts"]
                if "responder" not in cambios:
                    cambios["responder"] = (ev["tipo"], v["nombre"])
                    cambios["direccion"] = hacia

            if dist > 150:
                continue
            if dist < self.DISTANCIA_MIN:
                sentido = -hacia
                if abs(dx) < 2:
                    sentido = 1 if self.nombre < v["nombre"] else -1
                x_pos += sentido * int(4 + (self.DISTANCIA_MIN - dist) / 6)
                cambios["x_pos"] = x_pos
                cambios["direccion"] = hacia
                if estado == "quieto" and tick_interaccion > 30:
                    cambios["estado"] = "saludo"
                    cambios["pasos_restantes"] = 20
                    mostrar_comentario(self.voz.decir("choque"))
                    cambios["tick_interaccion"] = 0
            elif dist < 110 and estado == "quieto" and tick_interaccion > 50:
                cambios["direccion"] = hacia
                r = random.random()
                if r < 0.35:
                    cambios["estado"] = "saludo"
                    cambios["pasos_restantes"] = 25
                    msg = self.voz.decir("hola_otro", nombre=v.get("nombre", ""))
                    if msg != self.ultimo_saludo:
                        mostrar_comentario(msg)
                        self.ultimo_saludo = msg
                    self.emitir("saludo", v["nombre"])
                elif r < 0.55:
                    cambios["estado"] = "bailando"
                    cambios["pasos_restantes"] = 30
                    mostrar_comentario(self.voz.decir("bailar"))
                    self.emitir("baile", v["nombre"])
                elif r < 0.70:
                    cambios["estado"] = "siguiendo"
                    cambios["siguiendo_a"] = v.get("nombre")
                    cambios["seguir_restantes"] = random.randint(40, 100)
                else:
                    cambios["estado"] = "caminando"
                    cambios["pasos_restantes"] = 40
                cambios["tick_interaccion"] = 0
            elif dist < 140 and estado == "quieto" and tick_interaccion > 90 and v.get("estado") == "caminando":
                if random.random() < 0.15:
                    cambios["estado"] = "siguiendo"
                    cambios["siguiendo_a"] = v.get("nombre")
                    cambios["seguir_restantes"] = random.randint(30, 70)
                    cambios["tick_interaccion"] = 0
        return cambios
