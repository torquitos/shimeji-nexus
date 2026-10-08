import math
import random
import time

from shimeji_nexus.core import pantallas
from shimeji_nexus.pet.habilidades.zoomies import ARRANQUE, FIN_CARRERA


class MovimientoMixin:
    """Un tick del motor, paso a paso: mirar al mouse, caer, decidir reposo y moverse segun el estado."""

    def _mirar_mouse(self):
        # Mirar al mouse cuando está cerca
        if self.estado not in ("arrastrando", "cayendo", "magia", "saludo"):
            self.tick_mouse += 1
            if self.tick_mouse % 4 == 0:
                mouse = self.fisica.pos_mouse_global()
                if mouse:
                    dx = mouse[0] - (self.x_pos + self.tamano // 2)
                    dy = mouse[1] - (self.y_pos + self.tamano // 2)
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < 125 and abs(dy) < 150:
                        self.animacion.direccion = 1 if dx > 0 else -1
                        if dist < 25 and self.estado == "quieto" and self.tick_mouse > 60:
                            self.estado = "saludo"
                            self.pasos_restantes = 12
                            self.mostrar_comentario_autonomo(
                                self.voz.decir("mouse"))
                            self.tick_mouse = 0

    def _caer(self, vel_mult):
        if self.y_pos < self.fisica.suelo_actual and self.estado != "arrastrando":
            self.estado = "cayendo"
            self.y_pos += 16 * vel_mult
            if self.y_pos >= self.fisica.suelo_actual:
                self.y_pos = self.fisica.suelo_actual
                self.estado = "quieto"
                if self.fisica.contador_ventana > 0:
                    self.mostrar_comentario_autonomo(
                        self.voz.decir("aterrizar"))
                    self.fisica.contador_ventana = 0

    def _elegir_reposo(self, vel_mult):
        if not self.chat_abierto and self.estado == "quieto" and self.siguiendo_a is None:
            rand = random.random()
            if rand < 0.02 * vel_mult:
                self.estado = "caminando"
                self.animacion.direccion = random.choice([1, -1])
                self.pasos_restantes = random.randint(30, 80)

    def _mover(self, vel_mult, particulas_on):
        offset_y = 0
        if self.estado == "caminando":
            self.x_pos += self._avance(self.vel_caminar, vel_mult) * self.animacion.direccion
            izquierda, derecha = pantallas.limites_x()
            if self.x_pos < izquierda or self.x_pos > derecha - self.tamano:
                self.animacion.direccion *= -1
            offset_y = self.animacion.offset_y_para_estado("caminando")
            self.pasos_restantes -= 1
            if self.pasos_restantes <= 0:
                self.estado = "quieto"
                self.siguiendo_a = None
        elif self.estado == "siguiendo":
            if self.siguiendo_a:
                vecinos = self.social.leer_vecinos()
                objetivo = self.social.buscar_vecino(vecinos, self.siguiendo_a)
                if objetivo:
                    dx = objetivo["x"] - self.x_pos
                    self.animacion.direccion = 1 if dx > 0 else -1
                    if abs(dx) > 110:
                        self.x_pos += self._avance(self.vel_caminar * 0.8, vel_mult) * self.animacion.direccion
                        offset_y = self.animacion.offset_y_para_estado("siguiendo")
                self.seguir_restantes -= 1
                if self.seguir_restantes <= 0:
                    self.estado = "quieto"
                    self.siguiendo_a = None
            else:
                self.estado = "quieto"
        elif self.estado == "saludo":
            self.pasos_restantes -= 1
            if self.pasos_restantes <= 0:
                self.estado = "quieto"
        elif self.estado == "bailando":
            offset_y = self.animacion.offset_y_para_estado("bailando")
            self.pasos_restantes -= 1
            if self.pasos_restantes <= 0:
                self.estado = "quieto"
        elif self.estado == "flotando" or self.estado == "magia":
            offset_y = self.animacion.offset_y_para_estado(self.estado)
            if self.estado == "magia":
                if self.habilidad["forma"] == "zoomies":
                    offset_y = self._correr_zoomies()
                if particulas_on:
                    self.generar_efecto_aura()
                self.pasos_restantes -= 1
                if self.pasos_restantes <= 0:
                    self.estado = "quieto"
            else:
                self.pasos_restantes -= 1
                if self.pasos_restantes <= 0:
                    self.estado = "quieto"
        return offset_y

    def _correr_zoomies(self):
        """Durante la carrera de los zoomies el gato cruza la pantalla de verdad, a saltitos, y rebota en los bordes."""
        t = self.efecto.t
        if t is None or not ARRANQUE <= t < FIN_CARRERA:
            return 0
        izquierda, derecha = pantallas.limites_x()
        self.x_pos += 15 * self.animacion.direccion
        if self.x_pos < izquierda or self.x_pos > derecha - self.tamano:
            self.x_pos = max(izquierda, min(self.x_pos, derecha - self.tamano))
            self.animacion.direccion *= -1
            self.efecto.direccion = self.animacion.direccion
        return abs(math.sin(t * 0.55)) * 16

    def _dibujar_sprite(self):
        if self.estado == "magia" and self.efecto.t is not None:
            t = self.efecto.t
            self.animacion.indice_magia = sum(1 for limite in self.animacion.tiempos_magia if t >= limite)
        self.img_actual_tk = self.animacion.frame_actual(self.estado)
        self.canvas.itemconfig(self.sprite_canvas_id, image=self.img_actual_tk)
        balanceo = self.animacion.balanceo_x() if self.estado in ("caminando", "siguiendo") else 0
        self.canvas.coords(self.sprite_canvas_id, self.tamano // 2 + balanceo, self.tamano // 2)

    def _avance(self, vel_por_tick, vel_mult):
        """Pixeles a avanzar ahora. La velocidad se define por cada 35 ms, pero se aplica con el tiempo
        real transcurrido para que los pies no patinen si el motor va mas lento que eso."""
        ahora = time.time()
        dt = min(0.12, ahora - self._ult_mov) if self._ult_mov else 0.035
        self._ult_mov = ahora
        self._resto_x += vel_por_tick / 0.035 * dt * vel_mult
        px = int(self._resto_x)
        self._resto_x -= px
        return px
