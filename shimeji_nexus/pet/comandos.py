import random
import time

from shimeji_nexus.audio import sound_manager
from shimeji_nexus.core import memoria
from shimeji_nexus.core import settings as settings_manager
from shimeji_nexus.core.productividad import formatear_segundos


class ComandosMixin:
    """Pomodoro, recordatorios, habilidad automatica y los comandos del chat (/pomodoro, /recordar...)."""

    @staticmethod
    def _num(m):
        return f"{m:g}"

    def _avisar(self, texto, sonido="chat"):
        sound_manager.reproducir(sonido)
        if self.estado != "arrastrando":
            self.estado = "saludo"
            self.pasos_restantes = 40
        self.chat.avisar(texto)

    def _texto_reloj(self, ahora):
        if self.pomodoro.estado == "inactivo":
            return ""
        fase = "TRABAJO" if self.pomodoro.estado == "trabajo" else "DESCANSO"
        return f"{fase} {formatear_segundos(self.pomodoro.restante(ahora))}"

    def _tick_productividad(self):
        ahora = time.time()
        if ahora - self._ult_prod < 1.0:
            return
        self._ult_prod = ahora
        evento = self.pomodoro.tick(ahora)
        if evento == "fin_trabajo":
            self._avisar(self.voz.decir("pomodoro_fin", descanso=self._num(self.pomodoro.descanso_min)), "magic")
        elif evento == "fin_descanso":
            self._avisar(self.voz.decir("descanso_fin"))
        elif evento == "mitad":
            self.chat.avisar(self.voz.decir("pomodoro_mitad"), 8000)
        for r in self.recordatorios.vencidos(ahora):
            self._avisar(self.voz.decir("recordatorio_tarde" if r["tarde"] else "recordatorio", texto=r["texto"]), "magic")
        texto = self._texto_reloj(ahora)
        self.canvas.itemconfig(self.reloj_id, text=texto)
        ajustes = settings_manager.cargar()
        if (ajustes.get("habilidad_auto", True) and not ajustes.get("concentracion") and ahora >= self._prox_habilidad and self.estado == "quieto"
                and not self.chat.chat_abierto and self.efecto.t is None):
            self.accion_magica()
            self._prox_habilidad = ahora + random.uniform(120, 300)
        if texto:
            x0, y0, x1, y1 = self.canvas.bbox(self.reloj_id)
            self.canvas.coords(self.reloj_fondo, x0 - 6, y0 - 2, x1 + 6, y1 + 2)
            self.canvas.itemconfig(self.reloj_fondo, state="normal")
        else:
            self.canvas.itemconfig(self.reloj_fondo, state="hidden")

    def _comando(self, msg):
        """Comandos escritos en el chat (/pomodoro, /parar, /tiempo, /recordar). Devuelve la respuesta."""
        partes = msg.strip().split(None, 2)
        cmd = partes[0].lower()
        if cmd == "/pomodoro":
            minutos = None
            if len(partes) > 1:
                try:
                    minutos = float(partes[1].replace(",", "."))
                except ValueError:
                    return "Uso: /pomodoro [minutos]"
                if not 0 < minutos <= 180:
                    return "Elige entre 0 y 180 minutos."
            self.pomodoro.iniciar(minutos)
            return self.voz.decir("pomodoro_inicio", min=self._num(self.pomodoro.duracion_min))
        if cmd == "/parar":
            if self.pomodoro.estado == "inactivo":
                return self.voz.decir("pomodoro_nada")
            self.pomodoro.detener()
            return self.voz.decir("pomodoro_parar")
        if cmd == "/tiempo":
            if self.pomodoro.estado == "inactivo":
                return self.voz.decir("pomodoro_nada")
            return self.voz.decir("pomodoro_tiempo", restante=formatear_segundos(self.pomodoro.restante()), fase=self.pomodoro.estado)
        if cmd == "/recordar":
            try:
                minutos = float(partes[1].replace(",", ".")) if len(partes) > 1 else 0
            except ValueError:
                minutos = 0
            if minutos <= 0 or len(partes) < 3:
                return "Uso: /recordar <minutos> <texto>"
            self.recordatorios.agregar(minutos, partes[2])
            return self.voz.decir("recordatorio_ok", min=self._num(minutos), texto=partes[2])
        if cmd == "/nombre":
            if len(partes) < 2:
                return memoria.nombre_usuario() and f"Te llamo {memoria.nombre_usuario()}. Cámbialo con /nombre <nombre>." or "Uso: /nombre <cómo quieres que te llame>"
            memoria.guardar_nombre_usuario(" ".join(partes[1:]))
            return f"¡Anotado! A partir de ahora te llamo {memoria.nombre_usuario()}."
        if cmd == "/olvidar":
            self.chat.memoria.olvidar()
            return "Listo, olvidé lo que hablamos."
        return "Comandos: /pomodoro [min], /parar, /tiempo, /recordar <min> <texto>, /nombre <nombre>, /olvidar"
