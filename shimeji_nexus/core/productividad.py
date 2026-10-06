import json
import os
import re
import time

from shimeji_nexus.core.paths import base_dir


def formatear_segundos(seg):
    seg = max(0, int(seg))
    return f"{seg // 60:02d}:{seg % 60:02d}"


class Pomodoro:
    """Ciclo trabajo -> descanso. No usa interfaz: se le pregunta con tick() una vez por segundo."""

    def __init__(self, trabajo_min=25.0, descanso_min=5.0):
        self.trabajo_min = float(trabajo_min)
        self.descanso_min = float(descanso_min)
        self.estado = "inactivo"
        self.duracion_min = self.trabajo_min
        self.fin = 0.0
        self._inicio_fase = 0.0
        self._mitad_avisada = False

    def iniciar(self, minutos=None, ahora=None):
        ahora = time.time() if ahora is None else ahora
        self.duracion_min = float(minutos) if minutos else self.trabajo_min
        self.estado = "trabajo"
        self._inicio_fase = ahora
        self.fin = ahora + self.duracion_min * 60
        self._mitad_avisada = False

    def detener(self):
        self.estado = "inactivo"

    def restante(self, ahora=None):
        ahora = time.time() if ahora is None else ahora
        return max(0.0, self.fin - ahora) if self.estado != "inactivo" else 0.0

    def tick(self, ahora=None):
        """Devuelve 'mitad', 'fin_trabajo', 'fin_descanso' o None."""
        ahora = time.time() if ahora is None else ahora
        if self.estado == "trabajo":
            if ahora >= self.fin:
                self.estado = "descanso"
                self._inicio_fase = ahora
                self.fin = ahora + self.descanso_min * 60
                return "fin_trabajo"
            total = self.fin - self._inicio_fase
            if not self._mitad_avisada and total >= 600 and ahora >= self._inicio_fase + total / 2:
                self._mitad_avisada = True
                return "mitad"
        elif self.estado == "descanso" and ahora >= self.fin:
            self.estado = "inactivo"
            return "fin_descanso"
        return None


class Recordatorios:
    """Recordatorios de un personaje, guardados en disco para que sobrevivan si se cierra."""

    TARDE_SEG = 120

    def __init__(self, nombre):
        seguro = re.sub(r"[^\w\-]", "_", nombre)
        self.ruta = os.path.join(base_dir(), "recordatorios", f"{seguro}.json")
        self.items = self._cargar()

    def _cargar(self):
        try:
            with open(self.ruta, "r", encoding="utf-8") as f:
                return [r for r in json.load(f) if "cuando" in r and "texto" in r]
        except Exception:
            return []

    def _guardar(self):
        try:
            os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
            with open(self.ruta, "w", encoding="utf-8") as f:
                json.dump(self.items, f, ensure_ascii=False)
        except Exception:
            pass

    def agregar(self, minutos, texto, ahora=None):
        ahora = time.time() if ahora is None else ahora
        self.items.append({"cuando": ahora + float(minutos) * 60, "texto": texto})
        self._guardar()

    def vencidos(self, ahora=None):
        ahora = time.time() if ahora is None else ahora
        listos = [dict(r, tarde=ahora - r["cuando"] > self.TARDE_SEG) for r in self.items if r["cuando"] <= ahora]
        if listos:
            self.items = [r for r in self.items if r["cuando"] > ahora]
            self._guardar()
        return listos
