import os
import queue
import threading
from tkinter import messagebox

import customtkinter as ctk

from shimeji_nexus.audio import sound_manager
from shimeji_nexus.core.paths import base_dir
from shimeji_nexus.ui import theme
from shimeji_nexus.ui.launcher.registro import debug_log

from shimeji_nexus.ui.nuevo_personaje import AddCharacterWindow
from shimeji_nexus.ui.nuevo_personaje.editar import EditarPersonajeWindow
from shimeji_nexus.ui.launcher.hero import HeroMixin
from shimeji_nexus.ui.launcher.procesos import ProcesosMixin
from shimeji_nexus.ui.launcher.sidebar import SidebarMixin
from shimeji_nexus.ui.launcher.tarjeta import TarjetaHabilidadMixin
from shimeji_nexus.ui.launcher.tecnica import TecnicaMixin
from shimeji_nexus.ui.launcher.vida import VidaMixin
from shimeji_nexus.ui import ventanas
from shimeji_nexus.ui.ajustes import SettingsWindow

ctk.set_appearance_mode("dark")


class LauncherPremiumAnime(SidebarMixin, HeroMixin, TarjetaHabilidadMixin, TecnicaMixin, VidaMixin, ProcesosMixin):
    def __init__(self):
        self.mascotas_activas = {}
        self._cola_tray = queue.Queue()
        self.personajes_datos = {}
        self.personaje_seleccionado = None
        self.cards = {}
        self.card_thumbs = {}
        self.hero_photo = None
        self._sprites = {}
        self._fondos = {}

        self.root = ctk.CTk()
        self.root.title("Shimeji Nexus")
        self.root.geometry(ventanas.geometria_launcher(980, 720))
        ventanas.recordar_posicion(self.root)
        ventanas.estilizar(self.root)
        self.root.configure(fg_color=theme.BG)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_cerrar)

        try:
            ruta_icono = os.path.join(base_dir(), "app_icon.ico")
            if os.path.exists(ruta_icono):
                self.root.iconbitmap(ruta_icono)
        except Exception:
            pass

        self._build_ui()
        self.root.update_idletasks()

        # Carga inmediata (no lazy)
        try:
            self.escanear_personajes()
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                messagebox.showerror("Error Personajes",
                    f"Error al cargar personajes:\n{e}\n\n"
                    f"Revisa que la carpeta 'personajes' exista\n"
                    f"con subcarpetas y config.json dentro")
            except Exception:
                pass

        threading.Thread(target=sound_manager.asegurar_sonidos, daemon=True).start()
        print(f"DEBUG: {len(self.cards)} personajes cargados")
        print(f"DEBUG: Nombres: {list(self.cards.keys())}")
        self.root.after(100, self._iniciar_tray)
        ventanas.mostrar(self.root)
        self.root.mainloop()

    def _iniciar_tray(self):
        try:
            self.iniciar_tray_icon()
        except Exception as e:
            debug_log(f"Error tray icon: {e}")

    def _build_ui(self):
        self._build_sidebar()
        self._build_main()
        self._iniciar_vida()
        self.root.after(2000, self._vigilar_procesos)
        self.root.after(500, self._vigilar_atajo)

    def abrir_agregar(self):
        AddCharacterWindow(self.root, self)

    def editar_personaje(self):
        if self.personaje_seleccionado:
            EditarPersonajeWindow(self.root, self, self.personajes_datos[self.personaje_seleccionado])

    def abrir_settings(self):
        SettingsWindow(self.root)

    def on_cerrar(self):
        self.root.withdraw()
