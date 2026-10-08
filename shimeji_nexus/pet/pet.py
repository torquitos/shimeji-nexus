import json
import os
import random
import time
import tkinter as tk

from shimeji_nexus.core import image_utils
from shimeji_nexus.core import settings as settings_manager
from shimeji_nexus.core.paths import base_dir
from shimeji_nexus.core.productividad import Pomodoro, Recordatorios
from shimeji_nexus.core.voice import Voz
from shimeji_nexus.pet.animation import AnimationEngine
from shimeji_nexus.pet.acciones import AccionesMixin
from shimeji_nexus.pet.chat_ui import ChatBubble
from shimeji_nexus.pet.comandos import ComandosMixin
from shimeji_nexus.pet.habilidades import EfectoHabilidad, cargar_habilidad
from shimeji_nexus.pet.movimiento import MovimientoMixin
from shimeji_nexus.pet.physics import PhysicsEngine
from shimeji_nexus.pet.social import SocialBehavior

try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ShimejiNexus.Mascota.v3")
except Exception:
    pass


class MascotaLogica(MovimientoMixin, ComandosMixin, AccionesMixin):
    SHARED_DIR = os.path.join(base_dir(), "shared_state")

    def __init__(self, ruta_personaje, pos_inicial=None, args=None):
        self.args = args or {}
        self.ruta_personaje = ruta_personaje
        os.makedirs(self.SHARED_DIR, exist_ok=True)

        with open(os.path.join(ruta_personaje, "config.json"), "r", encoding="utf-8-sig") as f:
            self.config = json.load(f)

        self.voz = Voz(self.config)
        self.habilidad = cargar_habilidad(self.config)
        ajustes = settings_manager.cargar()
        self.pomodoro = Pomodoro(ajustes.get("pomodoro_trabajo", 25), ajustes.get("pomodoro_descanso", 5))
        self.recordatorios = Recordatorios(self.config.get("nombre", "personaje"))
        self._ult_prod = 0.0
        self._ult_mov = 0.0
        self._resto_x = 0.0
        self.habilidad_auto = ajustes.get("habilidad_auto", True)
        self._prox_habilidad = time.time() + random.uniform(120, 300)

        self.window = tk.Tk()
        self.window.overrideredirect(True)
        self.window.wm_attributes("-transparentcolor", "black")
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW", self.salir)
        try:
            ruta_ico = os.path.join(base_dir(), "app_icon.ico")
            if os.path.exists(ruta_ico):
                self.window.iconbitmap(ruta_ico)
        except Exception:
            pass

        self.tamano = 200
        self.estado = "quieto"
        self.animacion = AnimationEngine(ruta_personaje, self.config, self.tamano)
        self.vel_caminar = float(((self.config.get("animaciones") or {}).get("caminando") or {}).get("velocidad", 3))

        self.canvas = tk.Canvas(self.window, width=self.tamano, height=self.tamano, bg="black", bd=0, highlightthickness=0)
        self.canvas.pack()
        self.sprite_canvas_id = self.canvas.create_image(self.tamano // 2, self.tamano // 2, image=self.animacion.frame_actual(self.estado))
        self.reloj_id = self.canvas.create_text(self.tamano // 2, 10, text="", fill="#ffffff", font=("Segoe UI", 10, "bold"))
        self.reloj_fondo = self.canvas.create_rectangle(0, 0, 0, 0, fill="#16161D", outline="#3a3a4a", state="hidden")
        self.canvas.tag_lower(self.reloj_fondo, self.reloj_id)
        self.efecto = EfectoHabilidad(self.canvas, self.sprite_canvas_id, self.tamano, self.habilidad, self.window, sprite_propio="magia" in self.animacion.anim,
                                      silueta=lambda: self.animacion.silueta_actual(self.estado),
                                      retrato=self._retrato(), autor=self.config.get("nombre", ""))

        # Menú contextual
        self.menu = tk.Menu(self.window, tearoff=0, bg="#16161D", fg="white", activebackground="#FF3366")
        self.menu.add_command(label="Abrir/Ocultar Chat", command=self._conmutar_chat)
        self.menu.add_command(label=f"Usar {self.habilidad['nombre']}", command=self.accion_magica)
        self.menu.add_separator()
        self.menu.add_command(label="Iniciar pomodoro", command=lambda: self.chat.avisar(self._comando("/pomodoro")))
        self.menu.add_command(label="Detener pomodoro", command=lambda: self.chat.avisar(self._comando("/parar")))
        self.menu.add_separator()
        self.menu.add_command(label="Cerrar Mascota", command=self.salir)

        self.fisica = PhysicsEngine(self.tamano)
        if pos_inicial and isinstance(pos_inicial, (list, tuple)) and len(pos_inicial) == 2:
            self.x_pos, self.y_pos = pos_inicial
        else:
            area = self.fisica.area
            self.x_pos = random.randint(area.left + 200, area.right - 300)
            self.y_pos = self.fisica.suelo_fijo
        self.fisica.actualizar_monitor(self.x_pos, self.y_pos)
        self.y_pos = min(self.y_pos, self.fisica.suelo_fijo)

        self.window.geometry(f"+{self.x_pos}+{int(self.y_pos)}")

        nombre = self.config.get("nombre", "unknown")
        self.social = SocialBehavior(self.SHARED_DIR, nombre, self.voz)
        self.chat = ChatBubble(self.window, self.config, self.x_pos, self.y_pos, on_estado_quieto=self._forzar_quieto, on_comando=self._comando, ruta=self.ruta_personaje)

        self.canvas.bind("<Button-1>", self.iniciar_arrastre)
        self.canvas.bind("<B1-Motion>", self.arrastrar)
        self.canvas.bind("<ButtonRelease-1>", self.soltar)
        self.canvas.bind("<Button-3>", self.desplegar_menu)

        self.particulas = []
        self.tick_interaccion = 0
        self.tick_mouse = 0
        self.siguiendo_a = None
        self.seguir_restantes = 0
        self.pasos_restantes = 0

        self.actualizar_motor()
        if self.args.get("monitoreo_ia", True):
            self.chat.iniciar_monitoreo_ia()
        self.window.mainloop()

    def _retrato(self):
        try:
            return image_utils.cargar_avatar(os.path.join(self.ruta_personaje, self.config["imagen"]), 84)
        except Exception:
            return None

    def _forzar_quieto(self):
        self.estado = "quieto"

    def _conmutar_chat(self):
        self.chat.conmutar()
        if self.chat.chat_abierto:
            self.estado = "quieto"

    @property
    def chat_abierto(self):
        return self.chat.chat_abierto

    def mostrar_comentario_autonomo(self, texto):
        self.chat.mostrar_comentario_autonomo(texto)

    def actualizar_motor(self):
        settings = settings_manager.cargar()
        vel_mult = settings.get("velocidad", 1.0)
        particulas_on = settings.get("particulas", True)

        self.animacion.avanzar_tick()
        self.canvas.delete("particula")
        self.fisica.actualizar_suelo(self.x_pos, self.y_pos)
        self.y_pos = self.fisica.clamp_posicion(self.y_pos)

        self._mirar_mouse()
        self._caer(vel_mult)
        self._elegir_reposo(vel_mult)
        offset_y = self._mover(vel_mult, particulas_on)
        self._dibujar_sprite()
        if particulas_on:
            self.renderizar_y_mover_particulas()

        sx, sy = self.efecto.paso(self.x_pos + self.tamano // 2, int(self.y_pos - offset_y + self.tamano * 0.52), particulas_on)
        self.window.geometry(f"+{self.x_pos + sx}+{int(self.y_pos - offset_y) + sy}")
        self.chat.actualizar_posicion(self.x_pos, self.y_pos)
        self._aplicar_transparencia(settings)
        self._tick_interaccion()
        self._tick_productividad()
        self.window.after(35, self.actualizar_motor)

    def _aplicar_transparencia(self, settings):
        try:
            self.window.attributes("-alpha", settings.get("transparencia", 1.0))
        except Exception:
            pass

    def _tick_interaccion(self):
        self.tick_interaccion += 1
        if self.tick_interaccion % 5 == 0:
            self.social.compartir_estado(self.x_pos, self.y_pos, self.animacion.direccion, self.estado, self.tamano)
            if self.estado != "arrastrando":
                self._procesar_interacciones()
