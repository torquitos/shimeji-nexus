import tkinter as tk
from PIL import Image, ImageTk, ImageOps
import pygetwindow as gw
import threading
import time
import random
import os
import json
import math
import sys
import signal
import settings_manager
import ai_manager

try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ShimejiNexus.Mascota.v3")
except Exception:
    pass

def _base():
    return os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

class MascotaLogica:
    SHARED_DIR = os.path.join(_base(), "shared_state")

    def __init__(self, ruta_personaje, pos_inicial=None, args=None):
        self.args = args or {}
        self.ruta_personaje = ruta_personaje
        os.makedirs(self.SHARED_DIR, exist_ok=True)

        with open(os.path.join(ruta_personaje, "config.json"), "r", encoding="utf-8-sig") as f:
            self.config = json.load(f)

        self.window = tk.Tk()
        self.window.overrideredirect(True)
        self.window.wm_attributes("-transparentcolor", "black")
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW", self.salir)
        try:
            ruta_ico = os.path.join(_base(), "app_icon.ico")
            if os.path.exists(ruta_ico):
                self.window.iconbitmap(ruta_ico)
        except Exception:
            pass

        self.tamano = 200
        self.frames_cache = self._cargar_frames(ruta_personaje)
        self.direccion = 1
        self.tick_animacion = 0
        self.estado = "quieto"

        self.canvas = tk.Canvas(self.window, width=self.tamano, height=self.tamano, bg="black", bd=0, highlightthickness=0)
        self.canvas.pack()
        self.sprite_canvas_id = self.canvas.create_image(self.tamano // 2, self.tamano // 2, image=self._frame_actual()[0])

        # Globo de chat
        self.globo = tk.Toplevel(self.window)
        self.globo.overrideredirect(True)
        self.globo.attributes("-topmost", True)
        self.globo.config(bg="#16161D", bd=2, relief="solid", highlightbackground="#FF3366")
        self.globo_lbl = tk.Label(self.globo, text=self.config.get("saludo", "¡Hola!"), bg="#16161D", fg="#E1E1E6", font=("Segoe UI", 10, "bold"), wraplength=220, justify="center")
        self.globo_lbl.pack(padx=12, pady=10)
        self.entry_chat = tk.Entry(self.globo, bg="#24242D", fg="white", bd=0, insertbackground="white", font=("Segoe UI", 10), highlightthickness=1, highlightbackground="#FF3366")
        self.entry_chat.pack(padx=12, pady=8, fill="x")
        self.entry_chat.bind("<Return>", self.enviar_mensaje_usuario)

        # Menú contextual
        self.menu = tk.Menu(self.window, tearoff=0, bg="#16161D", fg="white", activebackground="#FF3366")
        self.menu.add_command(label="Abrir/Ocultar Chat", command=self.conmutar_chat_directo)
        self.menu.add_command(label="Desplegar Aura Mágica", command=self.accion_magica)
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

        self.suelo_fijo = self.screen_height - (self.tamano + 40)
        if self.y_pos > self.suelo_fijo:
            self.y_pos = self.suelo_fijo

        self.window.geometry(f"+{self.x_pos}+{int(self.y_pos)}")
        self.actualizar_posicion_globo()

        self.canvas.bind("<Button-1>", self.iniciar_arrastre)
        self.canvas.bind("<B1-Motion>", self.arrastrar)
        self.canvas.bind("<ButtonRelease-1>", self.soltar)
        self.canvas.bind("<Button-3>", self.desplegar_menu)

        self.chat_abierto = False
        self.particulas = []
        self.tick_interaccion = 0
        self.ultimo_saludo = ""
        self.siguiendo_a = None
        self.seguir_restantes = 0

        self.actualizar_motor()
        if self.args.get("monitoreo_ia", True):
            threading.Thread(target=self.bucle_monitoreo_ia, daemon=True).start()
        self.window.mainloop()

    def _abrir_imagen(self, path):
        img = Image.open(path).convert("RGBA")
        if any(p[3] < 255 for p in img.getdata()):
            return img.resize((self.tamano, self.tamano), Image.Resampling.NEAREST)
        datas = list(img.getdata())
        newData = [(0, 0, 0, 0) if (p[0] > 240 and p[1] > 240 and p[2] > 240) else p for p in datas]
        img.putdata(newData)
        return img.resize((self.tamano, self.tamano), Image.Resampling.NEAREST)

    def _precalcular_par(self, img):
        der, izq = [], []
        img_izq = ImageOps.mirror(img)
        for i in range(16):
            ang = math.sin((i / 16) * math.pi * 2) * 4
            der.append(ImageTk.PhotoImage(img.rotate(ang)))
            izq.append(ImageTk.PhotoImage(img_izq.rotate(-ang)))
        return {"der": der, "izq": izq}

    def _cargar_frames(self, ruta):
        cache = {}
        cfg = self.config.get("frames")
        if cfg:
            for estado, archivo in cfg.items():
                cache[estado] = self._precalcular_par(self._abrir_imagen(os.path.join(ruta, archivo)))
        else:
            archivo = self.config.get("imagen", "rias.png")
            cache["default"] = self._precalcular_par(self._abrir_imagen(os.path.join(ruta, archivo)))
        return cache

    def _frame_actual(self):
        estado = self.estado if self.estado in self.frames_cache else ("default" if "default" in self.frames_cache else list(self.frames_cache.keys())[0])
        par = self.frames_cache.get(estado, list(self.frames_cache.values())[0])
        return par["der"] if self.direccion == 1 else par["izq"]

    def actualizar_motor(self):
        settings = settings_manager.cargar()
        vel_mult = settings.get("velocidad", 1.0)
        particulas_on = settings.get("particulas", True)

        self.tick_animacion = (self.tick_animacion + 1) % 16
        self.canvas.delete("particula")

        if self.y_pos < self.suelo_fijo and self.estado != "arrastrando":
            self.estado = "cayendo"
            self.y_pos += 16 * vel_mult
            if self.y_pos > self.suelo_fijo:
                self.y_pos = self.suelo_fijo
                self.estado = "quieto"

        if not self.chat_abierto and self.estado == "quieto" and self.siguiendo_a is None:
            rand = random.random()
            if rand < 0.02 * vel_mult:
                self.estado = "caminando"
                self.direccion = random.choice([1, -1])
                self.pasos_restantes = random.randint(30, 80)
            elif rand > 0.985:
                self.estado = "flotando"
                self.pasos_restantes = 60

        offset_y = 0
        if self.estado == "caminando":
            self.x_pos += int(3 * self.direccion * vel_mult)
            if self.x_pos < 0 or self.x_pos > self.screen_width - self.tamano:
                self.direccion *= -1
            offset_y = abs(math.sin((self.tick_animacion / 16) * math.pi * 2)) * 6
            self.pasos_restantes -= 1
            if self.pasos_restantes <= 0:
                self.estado = "quieto"
                self.siguiendo_a = None
        elif self.estado == "siguiendo":
            if self.siguiendo_a:
                vecinos = self.leer_vecinos()
                objetivo = None
                for v in vecinos:
                    if v.get("nombre") == self.siguiendo_a:
                        objetivo = v
                        break
                if objetivo:
                    dx = objetivo["x"] - self.x_pos
                    self.direccion = 1 if dx > 0 else -1
                    self.x_pos += int(2.5 * self.direccion * vel_mult)
                    offset_y = abs(math.sin((self.tick_animacion / 16) * math.pi * 2)) * 5
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
            offset_y = abs(math.sin((self.tick_animacion / 16) * math.pi * 4)) * 15
            self.pasos_restantes -= 1
            if self.pasos_restantes <= 0:
                self.estado = "quieto"
        elif self.estado == "flotando" or self.estado == "magia":
            offset_y = math.sin((self.tick_animacion / 16) * math.pi * 2) * 12
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

        frames = self._frame_actual()
        self.img_actual_tk = frames[self.tick_animacion]
        self.canvas.itemconfig(self.sprite_canvas_id, image=self.img_actual_tk)

        if particulas_on:
            self.renderizar_y_mover_particulas()

        self.window.geometry(f"+{self.x_pos}+{int(self.y_pos - offset_y)}")
        self.actualizar_posicion_globo()

        trans = settings.get("transparencia", 1.0)
        try:
            self.window.attributes("-alpha", trans)
        except Exception:
            pass

        self.tick_interaccion += 1
        if self.tick_interaccion % 5 == 0:
            self.compartir_estado()
            if self.estado != "arrastrando":
                self.procesar_interacciones()

        self.window.after(35, self.actualizar_motor)

    def generar_efecto_aura(self):
        for _ in range(2):
            px = self.tamano // 2 + random.randint(-35, 35)
            py = self.tamano // 2 + random.randint(-45, 45)
            largo = random.randint(4, 10)
            color = random.choice(["#FF3366", "#FF0033", "#D100D1"])
            velocidad = random.randint(3, 6)
            self.particulas.append({"x": px, "y": py, "l": largo, "color": color, "v": velocidad})

    def renderizar_y_mover_particulas(self):
        particulas_vivas = []
        for p in self.particulas:
            p["y"] -= p["v"]
            p["x"] += random.choice([-1, 0, 1])
            self.canvas.create_line(p["x"] - p["l"], p["y"], p["x"] + p["l"], p["y"], fill=p["color"], width=2, tags="particula")
            self.canvas.create_line(p["x"], p["y"] - p["l"], p["x"], p["y"] + p["l"], fill=p["color"], width=2, tags="particula")
            if p["y"] > 10:
                particulas_vivas.append(p)
        self.particulas = particulas_vivas

    def iniciar_arrastre(self, event):
        self.estado = "arrastrando"
        self.x_mouse = event.x
        self.y_mouse = event.y

    def arrastrar(self, event):
        self.x_pos = self.window.winfo_x() + (event.x - self.x_mouse)
        self.y_pos = self.window.winfo_y() + (event.y - self.y_mouse)
        self.window.geometry(f"+{self.x_pos}+{int(self.y_pos)}")
        self.actualizar_posicion_globo()

    def soltar(self, event):
        if self.y_pos < self.suelo_fijo:
            self.estado = "cayendo"
        else:
            self.estado = "quieto"

    def conmutar_chat_directo(self):
        import sound_manager
        sound_manager.reproducir("chat")
        if self.chat_abierto:
            self.globo.withdraw()
            self.chat_abierto = False
        else:
            self.globo.deiconify()
            self.chat_abierto = True
            self.estado = "quieto"
            self.entry_chat.focus_set()
            self.actualizar_posicion_globo()

    def accion_magica(self):
        import sound_manager
        sound_manager.reproducir("magic")
        self.estado = "magia"
        self.pasos_restantes = 100
        self.mostrar_comentario_autonomo("¡Por el orgullo del clan Gremory!")

    def actualizar_posicion_globo(self):
        self.globo.geometry(f"+{self.x_pos - 20}+{int(self.y_pos - 120)}")

    def enviar_mensaje_usuario(self, event):
        msg = self.entry_chat.get().strip()
        if not msg:
            return
        self.entry_chat.delete(0, tk.END)
        self.globo_lbl.config(text="Pensando...")
        import sound_manager
        sound_manager.reproducir("chat")
        threading.Thread(target=self.procesar_conversacion_ia, args=(msg,), daemon=True).start()

    def procesar_conversacion_ia(self, mensaje_usuario):
        try:
            texto = ai_manager.generar_texto(self.config["personalidad"], mensaje_usuario, 12)
            self.window.after(0, lambda: self.globo_lbl.config(text=texto))
        except Exception as e:
            print(f"Error en IA: {e}")
            self.window.after(0, lambda: self.globo_lbl.config(text="Error..."))

    def bucle_monitoreo_ia(self):
        while True:
            time.sleep(30)
            if not self.chat_abierto:
                try:
                    v = gw.getActiveWindow()
                    ventana = v.title if v else "Escritorio"
                    texto = ai_manager.generar_comentario_entorno(self.config["personalidad"], ventana, 10)
                    self.window.after(0, lambda: self.mostrar_comentario_autonomo(texto))
                except Exception as e:
                    print(f"Error monitoreo IA: {e}")

    def mostrar_comentario_autonomo(self, texto):
        if not self.chat_abierto:
            self.globo_lbl.config(text=texto)
            self.globo.deiconify()
            self.window.after(7000, lambda: self.globo.withdraw() if not self.chat_abierto else None)

    def desplegar_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def compartir_estado(self):
        try:
            nombre = self.config.get("nombre", "unknown")
            data = {
                "nombre": nombre,
                "x": self.x_pos, "y": int(self.y_pos),
                "direccion": self.direccion,
                "estado": self.estado,
                "tamano": self.tamano,
                "timestamp": time.time(),
            }
            with open(os.path.join(self.SHARED_DIR, f"{nombre}.json"), "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def leer_vecinos(self):
        vecinos = []
        mi_nombre = self.config.get("nombre", "unknown")
        ahora = time.time()
        try:
            for archivo in os.listdir(self.SHARED_DIR):
                if not archivo.endswith(".json"):
                    continue
                nombre = archivo[:-5]
                if nombre == mi_nombre:
                    continue
                ruta = os.path.join(self.SHARED_DIR, archivo)
                try:
                    with open(ruta, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if ahora - data.get("timestamp", 0) < 3:
                        vecinos.append(data)
                except Exception:
                    pass
        except Exception:
            pass
        return vecinos

    def procesar_interacciones(self):
        vecinos = self.leer_vecinos()
        for v in vecinos:
            dx = v["x"] - self.x_pos
            dy = v["y"] - self.y_pos
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 150:
                continue
            if dist < 40:
                if dist > 0:
                    empuje = int(8 / max(dist, 1))
                    self.x_pos -= int(dx / dist * empuje)
                self.direccion = -1 if dx > 0 else 1
                if self.estado == "quieto" and self.tick_interaccion > 30:
                    self.estado = "saludo"
                    self.pasos_restantes = 20
                    reacciones = ["¡Oye!", "¡Quita!", "Eh...", "¡Casi chocamos!", "Ups~"]
                    self.mostrar_comentario_autonomo(random.choice(reacciones))
                    self.tick_interaccion = 0
            elif dist < 100 and self.estado == "quieto" and self.tick_interaccion > 50:
                self.direccion = -1 if dx > 0 else 1
                r = random.random()
                if r < 0.35:
                    self.estado = "saludo"
                    self.pasos_restantes = 25
                    saludos = ["¡Hola!", "Hey!", "¿Qué tal?", f"¡{v.get('nombre','')}!", "Que gusto~"]
                    msg = random.choice(saludos)
                    if msg != self.ultimo_saludo:
                        self.mostrar_comentario_autonomo(msg)
                        self.ultimo_saludo = msg
                elif r < 0.55:
                    self.estado = "bailando"
                    self.pasos_restantes = 30
                    self.mostrar_comentario_autonomo(random.choice(["¡A bailar!", "Sigue el ritmo~", "*danza*"]))
                elif r < 0.70:
                    self.estado = "siguiendo"
                    self.siguiendo_a = v.get("nombre")
                    self.seguir_restantes = random.randint(40, 100)
                else:
                    self.estado = "flotando"
                    self.pasos_restantes = 40
                    self.mostrar_comentario_autonomo(random.choice(["¡A volar!", "*flota*", "Arriba~"]))
                self.tick_interaccion = 0
            elif dist < 140 and self.estado == "quieto" and self.tick_interaccion > 90 and v.get("estado") == "caminando":
                if random.random() < 0.15:
                    self.estado = "siguiendo"
                    self.siguiendo_a = v.get("nombre")
                    self.seguir_restantes = random.randint(30, 70)
                    self.tick_interaccion = 0

    def salir(self):
        self.guardar_posicion()
        self.limpiar_estado_compartido()
        import sound_manager
        sound_manager.reproducir("close")
        self.window.quit()
        self.window.destroy()
        os._exit(0)

    def limpiar_estado_compartido(self):
        try:
            nombre = self.config.get("nombre", "unknown")
            ruta = os.path.join(self.SHARED_DIR, f"{nombre}.json")
            if os.path.exists(ruta):
                os.remove(ruta)
        except Exception:
            pass

    def guardar_posicion(self):
        try:
            nombre = self.config.get("nombre", "personaje")
            data = {"x": self.x_pos, "y": self.y_pos}
            ruta = os.path.join(_base(), "pos_cache", f"{nombre}.json")
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass


if __name__ == "__main__":
    import sound_manager
    sound_manager.asegurar_sonidos()
    if len(sys.argv) > 1:
        ruta = sys.argv[1]
        pos = None
        extra = {}
        if len(sys.argv) > 2:
            try:
                pos = json.loads(sys.argv[2])
            except Exception:
                pos = None
        if len(sys.argv) > 3:
            try:
                extra = json.loads(sys.argv[3])
            except Exception:
                extra = {}
        MascotaLogica(ruta, pos_inicial=pos, args=extra)
    else:
        print("Uso: python mascota_motor.py <ruta_personaje> [pos_json] [args_json]")
