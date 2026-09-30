import ctypes
import ctypes.wintypes

import pygetwindow as gw


class PhysicsEngine:
    """Suelo, caída y detección de ventanas para que la mascota se pueda sentar encima."""

    def __init__(self, tamano, screen_width, screen_height):
        self.tamano = tamano
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.suelo_fijo = screen_height - (tamano + 40)
        self.suelo_actual = self.suelo_fijo
        self.ultima_ventana = None
        self.contador_ventana = 0

    def ventana_para_sentarse(self, x_pos, y_pos, margen_extra=0):
        """Busca una ventana cuyo borde superior esté cerca de los pies de la mascota.
        margen_extra: cuánto puede estar la ventana por DEBAJO de los pies (px)."""
        cx = x_pos + self.tamano // 2
        cy = y_pos + self.tamano  # posición de los pies
        mejor = None
        mejor_dist = float("inf")
        try:
            for w in gw.getAllWindows():
                if not w.visible or w.isMinimized:
                    continue
                t = w.title.lower()
                if not t or any(x in t for x in ("mascota", "shimeji", "tk", "personaje")):
                    continue
                if w.width < 60 or w.height < 60:
                    continue
                if not (w.left <= cx <= w.right):
                    continue
                dist = w.top - cy
                if -30 <= dist <= margen_extra:
                    if dist < mejor_dist:
                        mejor_dist = dist
                        mejor = w
        except Exception:
            pass
        return mejor

    def actualizar_suelo(self, x_pos, y_pos):
        """Recalcula suelo_actual según ventanas cercanas. Devuelve (aterrizo_en_ventana_nueva)."""
        ventana_bajo = self.ventana_para_sentarse(x_pos, y_pos, margen_extra=200)
        if ventana_bajo:
            borde = ventana_bajo.top - self.tamano - 5
            if 0 < borde < self.suelo_fijo:
                self.suelo_actual = borde
                if ventana_bajo != self.ultima_ventana:
                    self.contador_ventana = 20
                    self.ultima_ventana = ventana_bajo
        else:
            self.contador_ventana -= 1
            if self.contador_ventana <= 0:
                self.suelo_actual = self.suelo_fijo
                self.ultima_ventana = None

    def sentarse_en_ventana_cercana(self, x_pos, y_pos, margen_extra=100):
        """Usado al soltar el drag. Devuelve el nuevo y_pos si encontró ventana, o None."""
        ventana = self.ventana_para_sentarse(x_pos, y_pos, margen_extra=margen_extra)
        if ventana:
            borde = ventana.top - self.tamano - 5
            if 0 < borde < self.suelo_fijo:
                self.suelo_actual = borde
                self.ultima_ventana = ventana
                self.contador_ventana = 20
                return borde
        return None

    def clamp_posicion(self, y_pos):
        if y_pos > self.suelo_fijo + 50 or y_pos < -200:
            return self.suelo_fijo
        return y_pos

    def pos_mouse_global(self):
        try:
            point = ctypes.wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
            return point.x, point.y
        except Exception:
            return None
