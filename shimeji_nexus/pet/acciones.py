import json
import os
import random

from shimeji_nexus.audio import sound_manager
from shimeji_nexus.core import pantallas
from shimeji_nexus.core.paths import base_dir
from shimeji_nexus.pet.habilidades.config import TOTAL


class AccionesMixin:
    """Lo que hace la mascota por interaccion: arrastrar, menu, habilidad, respuestas a otras mascotas, salir."""

    def _procesar_interacciones(self):
        cambios = self.social.procesar_interacciones(
            self.x_pos, self.y_pos, self.estado, self.tick_interaccion, self.mostrar_comentario_autonomo)
        if "x_pos" in cambios:
            izquierda, derecha = pantallas.limites_x()
            self.x_pos = max(izquierda, min(derecha - self.tamano, cambios["x_pos"]))
        if "responder" in cambios:
            tipo, quien = cambios["responder"]
            self.window.after(random.randint(900, 1700), lambda: self._responder(tipo, quien))
        if "direccion" in cambios:
            self.animacion.direccion = cambios["direccion"]
        if "estado" in cambios:
            self.estado = cambios["estado"]
        if "pasos_restantes" in cambios:
            self.pasos_restantes = cambios["pasos_restantes"]
        if "siguiendo_a" in cambios:
            self.siguiendo_a = cambios["siguiendo_a"]
        if "seguir_restantes" in cambios:
            self.seguir_restantes = cambios["seguir_restantes"]
        if "tick_interaccion" in cambios:
            self.tick_interaccion = cambios["tick_interaccion"]

    def _responder(self, tipo, quien):
        categoria = {"saludo": "responder_saludo", "baile": "responder_baile", "habilidad": "reaccion_habilidad"}.get(tipo)
        if not categoria or self.estado == "arrastrando":
            return
        if self.estado == "quieto":
            self.estado = "saludo"
            self.pasos_restantes = 20
        self.mostrar_comentario_autonomo(self.voz.decir(categoria, nombre=quien))

    def generar_efecto_aura(self):
        self.efecto.generar(self.animacion.direccion)

    def renderizar_y_mover_particulas(self):
        self.efecto.dibujar()

    def iniciar_arrastre(self, event):
        self.estado = "arrastrando"
        self.x_mouse = event.x
        self.y_mouse = event.y
        self._arrastro = False

    def arrastrar(self, event):
        self._arrastro = True
        self.x_pos = self.window.winfo_x() + (event.x - self.x_mouse)
        self.y_pos = self.window.winfo_y() + (event.y - self.y_mouse)
        self.window.geometry(f"+{self.x_pos}+{int(self.y_pos)}")
        self.chat.actualizar_posicion(self.x_pos, self.y_pos)

    def soltar(self, event):
        if not self._arrastro and not self.config.get("habla", True):
            self.estado, self.pasos_restantes = "saludo", 24
            self.mostrar_comentario_autonomo(random.choice(("Prrr...", "*ronronea*", "Miau~", "*cierra los ojos feliz*")))
            return
        nuevo_y = self.fisica.sentarse_en_ventana_cercana(self.x_pos, self.y_pos, margen_extra=100)
        if nuevo_y is not None:
            self.y_pos = nuevo_y
            self.estado = "quieto"
            self.mostrar_comentario_autonomo(self.voz.decir("posarse"))
            return
        if self.y_pos < self.fisica.suelo_fijo:
            self.estado = "cayendo"
        else:
            self.estado = "quieto"

    def accion_magica(self):
        sound_manager.reproducir("hab_" + self.habilidad["forma"])
        self.estado = "magia"
        self.pasos_restantes = TOTAL + 6
        self.efecto.iniciar(self.animacion.direccion)
        self.social.emitir("habilidad", "*")
        self.mostrar_comentario_autonomo(self.voz.decir("magia"))

    def desplegar_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def salir(self):
        self.guardar_posicion()
        self.social.limpiar_estado()
        sound_manager.reproducir("close")
        self.window.quit()
        self.window.destroy()
        os._exit(0)

    def guardar_posicion(self):
        try:
            nombre = self.config.get("nombre", "personaje")
            data = {"x": self.x_pos, "y": self.y_pos}
            ruta = os.path.join(base_dir(), "pos_cache", f"{nombre}.json")
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass
