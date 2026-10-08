import os
import random
import threading
import time

from shimeji_nexus.core import actividad, sistema
from shimeji_nexus.core import settings as settings_manager
from shimeji_nexus.core.reacciones import Reacciones


class ReaccionarMixin:
    """La mascota reacciona a lo que haces (ventana activa, inactividad, hora, tiempo sin parar)
    y se esconde cuando hay algo a pantalla completa."""

    def iniciar_reacciones(self):
        self._reacciones = Reacciones(self.SHARED_DIR)
        self._oculta = False
        self._inicio = time.time()
        threading.Thread(target=self._bucle_reacciones, daemon=True).start()
        threading.Thread(target=self._vigilar_pantalla_completa, daemon=True).start()

    def _bucle_reacciones(self):
        while True:
            time.sleep(4 + random.random())
            ajustes = settings_manager.cargar()
            if not ajustes.get("monitoreo_ia", True) or ajustes.get("concentracion"):
                continue
            try:
                categoria = self._reacciones.evaluar(actividad.titulo_ventana_activa(), actividad.segundos_inactivo())
                if categoria:
                    self.window.after(random.randint(200, 2500), lambda c=categoria: self._decir_reaccion(c))
            except Exception:
                pass

    def _vigilar_pantalla_completa(self):
        while True:
            time.sleep(1.5)
            if self._orden_cerrar_todas() > self._inicio:
                self.window.after(0, self.salir)
                return
            debe = settings_manager.cargar().get("ocultar_pantalla_completa", True) and sistema.pantalla_completa_activa()
            if debe != self._oculta:
                self._oculta = debe
                self.window.after(0, self._mostrar_u_ocultar)

    def _ruta_cerrar_todas(self):
        return os.path.join(self.SHARED_DIR, "cerrar_todas.txt")

    def _orden_cerrar_todas(self):
        try:
            return os.path.getmtime(self._ruta_cerrar_todas())
        except OSError:
            return 0

    def cerrar_todas(self):
        """Avisa a las demas mascotas (cada una mira esta marca) y se cierra tambien."""
        try:
            with open(self._ruta_cerrar_todas(), "w") as f:
                f.write("1")
        except OSError:
            pass
        self.window.after(300, self.salir)

    def _mostrar_u_ocultar(self):
        if self._oculta:
            self.window.withdraw()
        else:
            self.window.deiconify()
            self.window.attributes("-topmost", True)

    def _decir_reaccion(self, categoria):
        if self.estado in ("arrastrando", "magia") or self.chat_abierto or self._oculta:
            return
        self.mostrar_comentario_autonomo(self.voz.decir(categoria))
        if categoria == "vuelve" and self.estado == "quieto":
            self.estado, self.pasos_restantes = "saludo", 20
