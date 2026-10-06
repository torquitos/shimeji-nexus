import json
import math
import os
import random
import time
import tkinter as tk

from shimeji_nexus.audio import sound_manager
from shimeji_nexus.core import settings as settings_manager
from shimeji_nexus.core.paths import base_dir
from shimeji_nexus.core.productividad import Pomodoro, Recordatorios, formatear_segundos
from shimeji_nexus.core.voice import Voz
from shimeji_nexus.pet.animation import AnimationEngine
from shimeji_nexus.pet.chat_ui import ChatBubble
from shimeji_nexus.pet.habilidades import EfectoHabilidad, cargar_habilidad
from shimeji_nexus.pet.physics import PhysicsEngine
from shimeji_nexus.pet.social import SocialBehavior

try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ShimejiNexus.Mascota.v3")
except Exception:
    pass


class MascotaLogica:
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

        self.canvas = tk.Canvas(self.window, width=self.tamano, height=self.tamano, bg="black", bd=0, highlightthickness=0)
        self.canvas.pack()
        self.sprite_canvas_id = self.canvas.create_image(self.tamano // 2, self.tamano // 2, image=self.animacion.frame_actual(self.estado))
        self.reloj_id = self.canvas.create_text(self.tamano // 2, 10, text="", fill="#ffffff", font=("Segoe UI", 10, "bold"))
        self.reloj_fondo = self.canvas.create_rectangle(0, 0, 0, 0, fill="#16161D", outline="#3a3a4a", state="hidden")
        self.canvas.tag_lower(self.reloj_fondo, self.reloj_id)
        self.efecto = EfectoHabilidad(self.canvas, self.sprite_canvas_id, self.tamano, self.habilidad, self.window)

        # Menú contextual
        self.menu = tk.Menu(self.window, tearoff=0, bg="#16161D", fg="white", activebackground="#FF3366")
        self.menu.add_command(label="Abrir/Ocultar Chat", command=self._conmutar_chat)
        self.menu.add_command(label=f"Usar {self.habilidad['nombre']}", command=self.accion_magica)
        self.menu.add_separator()
        self.menu.add_command(label="Iniciar pomodoro", command=lambda: self.chat.avisar(self._comando("/pomodoro")))
        self.menu.add_command(label="Detener pomodoro", command=lambda: self.chat.avisar(self._comando("/parar")))
        self.menu.add_separator()
        self.menu.add_command(label="Cerrar Mascota", command=self.salir)

        self.screen_width = self.window.winfo_screenwidth()
        self.screen_height = self.window.winfo_screenheight()

        # Posición inicial
        if pos_inicial and isinstance(pos_inicial, (list, tuple)) and len(pos_inicial) == 2:
            self.x_pos = pos_inicial[0]
            self.y_pos = pos_inicial[1]
        else:
            self.x_pos = random.randint(200, self.screen_width - 300)
            self.y_pos = self.screen_height - (self.tamano + 40)

        self.fisica = PhysicsEngine(self.tamano, self.screen_width, self.screen_height)
        if self.y_pos > self.fisica.suelo_fijo:
            self.y_pos = self.fisica.suelo_fijo

        self.window.geometry(f"+{self.x_pos}+{int(self.y_pos)}")

        nombre = self.config.get("nombre", "unknown")
        self.social = SocialBehavior(self.SHARED_DIR, nombre, self.voz)
        self.chat = ChatBubble(self.window, self.config, self.x_pos, self.y_pos, on_estado_quieto=self._forzar_quieto, on_comando=self._comando)

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

        if not self.chat_abierto and self.estado == "quieto" and self.siguiendo_a is None:
            rand = random.random()
            if rand < 0.02 * vel_mult:
                self.estado = "caminando"
                self.animacion.direccion = random.choice([1, -1])
                self.pasos_restantes = random.randint(30, 80)
            elif rand > 0.985:
                self.estado = "flotando"
                self.pasos_restantes = 60

        offset_y = 0
        if self.estado == "caminando":
            self.x_pos += int(3 * self.animacion.direccion * vel_mult)
            if self.x_pos < 0 or self.x_pos > self.screen_width - self.tamano:
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
                        self.x_pos += int(2.5 * self.animacion.direccion * vel_mult)
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
                if particulas_on:
                    self.generar_efecto_aura()
                self.pasos_restantes -= 1
                if self.pasos_restantes <= 0:
                    self.estado = "quieto"
            else:
                self.pasos_restantes -= 1
                if self.pasos_restantes <= 0:
                    self.estado = "quieto"

        self.img_actual_tk = self.animacion.frame_actual(self.estado)
        self.canvas.itemconfig(self.sprite_canvas_id, image=self.img_actual_tk)

        if particulas_on:
            self.renderizar_y_mover_particulas()

        sx, sy = self.efecto.paso(self.x_pos + self.tamano // 2, int(self.y_pos - offset_y + self.tamano * 0.52), particulas_on)
        self.window.geometry(f"+{self.x_pos + sx}+{int(self.y_pos - offset_y) + sy}")
        self.chat.actualizar_posicion(self.x_pos, self.y_pos)

        # Transparencia configurable
        trans = settings.get("transparencia", 1.0)
        try:
            self.window.attributes("-alpha", trans)
        except Exception:
            pass

        self.tick_interaccion += 1
        if self.tick_interaccion % 5 == 0:
            self.social.compartir_estado(self.x_pos, self.y_pos, self.animacion.direccion, self.estado, self.tamano)
            if self.estado != "arrastrando":
                self._procesar_interacciones()

        self._tick_productividad()
        self.window.after(35, self.actualizar_motor)

    def _procesar_interacciones(self):
        cambios = self.social.procesar_interacciones(
            self.x_pos, self.y_pos, self.estado, self.tick_interaccion, self.mostrar_comentario_autonomo)
        if "x_pos" in cambios:
            self.x_pos = max(0, min(self.screen_width - self.tamano, cambios["x_pos"]))
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
        if (self.habilidad_auto and ahora >= self._prox_habilidad and self.estado == "quieto"
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
        return "Comandos: /pomodoro [min], /parar, /tiempo, /recordar <min> <texto>"

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

    def arrastrar(self, event):
        self.x_pos = self.window.winfo_x() + (event.x - self.x_mouse)
        self.y_pos = self.window.winfo_y() + (event.y - self.y_mouse)
        self.window.geometry(f"+{self.x_pos}+{int(self.y_pos)}")
        self.chat.actualizar_posicion(self.x_pos, self.y_pos)

    def soltar(self, event):
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
        self.pasos_restantes = 100
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
