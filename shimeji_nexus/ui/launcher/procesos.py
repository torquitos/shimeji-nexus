import json
import os
import subprocess
import sys
import threading
from tkinter import messagebox

from PIL import Image

from shimeji_nexus.audio import sound_manager
from shimeji_nexus.core import settings as settings_manager
from shimeji_nexus.core.paths import base_dir



class ProcesosMixin:
    """Lanzar y cerrar los procesos de las mascotas, bandeja del sistema y salida de la app."""

    def lanzar(self):
        item = self.personaje_seleccionado
        if not item:
            return
        if item in self.mascotas_activas:
            messagebox.showinfo("Ya activa", f"{item} ya está en pantalla.")
            return
        if self._lanzar(item):
            self.seleccionar_personaje(item)

    def lanzar_todas(self):
        for nombre in [n for n in self.personajes_datos if n not in self.mascotas_activas]:
            self._lanzar(nombre)
        if self.personaje_seleccionado:
            self.seleccionar_personaje(self.personaje_seleccionado)

    def _vigilar_procesos(self):
        """Si una mascota se cierra por su cuenta (menu 'Cerrar mascota'), el launcher se entera."""
        try:
            cerradas = [n for n, i in self.mascotas_activas.items() if i["proceso"].poll() is not None]
            for nombre in cerradas:
                del self.mascotas_activas[nombre]
            if cerradas and self.personaje_seleccionado:
                self.seleccionar_personaje(self.personaje_seleccionado)
            self.actualizar_estados()
            self.root.after(2000, self._vigilar_procesos)
        except Exception:
            pass

    def _lanzar(self, item):
        info = self.personajes_datos[item]
        folder = info["folder"]
        ruta_envio = os.path.join(base_dir(), "personajes", folder)
        sound_manager.reproducir("invoke")

        pos_cache = os.path.join(base_dir(), "pos_cache", f"{info['nombre']}.json")
        pos_data = None
        if os.path.exists(pos_cache):
            try:
                with open(pos_cache, "r", encoding="utf-8") as f:
                    pos_data = json.load(f)
            except Exception:
                pass

        settings = settings_manager.cargar()
        mon = settings.get("monitoreo_ia", True)
        par = settings.get("particulas", True)
        extra_args = {"monitoreo_ia": mon, "particulas": par}

        args = [sys.executable]
        if not getattr(sys, 'frozen', False):
            args.append(os.path.join(base_dir(), "mascota_motor.py"))
        args.extend([ruta_envio, json.dumps(pos_data) if pos_data else "null", json.dumps(extra_args)])
        self.root.update_idletasks()
        try:
            proc = subprocess.Popen(args)
            self.mascotas_activas[item] = {"proceso": proc, "folder": folder}
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo invocar a {item}:\n{e}")
            return False

    def cerrar_mascota_seleccionada(self):
        if not self.personaje_seleccionado:
            return
        self.cerrar_por_nombre(self.personaje_seleccionado)

    def cerrar_por_nombre(self, nombre):
        if nombre not in self.mascotas_activas:
            return
        info = self.mascotas_activas[nombre]
        try:
            proc = info["proceso"]
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=3)
        except Exception:
            try:
                import psutil
                parent = psutil.Process(proc.pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
            except Exception:
                pass
        del self.mascotas_activas[nombre]
        if self.personaje_seleccionado == nombre:
            self.seleccionar_personaje(nombre)

    def matar_todos(self):
        for nombre in list(self.mascotas_activas.keys()):
            self.cerrar_por_nombre(nombre)
        sound_manager.reproducir("close")
        messagebox.showinfo("Limpieza", "Todas las mascotas cerradas.")
        if self.personaje_seleccionado:
            self.seleccionar_personaje(self.personaje_seleccionado)

    def iniciar_tray_icon(self):
        try:
            import pystray
            from pystray import MenuItem as Item

            img_tray = Image.open(os.path.join(base_dir(), "app_icon.ico")).resize((64, 64))
            icono = pystray.Icon("shimeji", img_tray, "Shimeji Nexus", menu=pystray.Menu(
                Item("Mostrar Ventana", lambda: self.root.after(0, self.root.deiconify)),
                Item("Salir", lambda: self.root.after(0, self.salir_completo)),
            ))

            def minimizar():
                self.root.withdraw()
                threading.Thread(target=icono.run, daemon=True).start()

            self.root.protocol("WM_DELETE_WINDOW", minimizar)
            self._tray_icon = icono
        except ImportError:
            pass

    def salir_completo(self):
        self.matar_todos()
        try:
            self._tray_icon.stop()
        except Exception:
            pass
        self.root.quit()
        self.root.destroy()
        os._exit(0)
