import tkinter as tk
from PIL import Image, ImageTk, ImageOps
import pygetwindow as gw
from google import genai
import threading
import time
import random
import os
import json
import math

# Inicialización de la API
API_KEY = "AQ.Ab8RN6KjrA7ymL7g1oHmFxI9takvvfA0SogcncLqw4FOTsVEjw" 
client = genai.Client(api_key=API_KEY)

class MascotaLogica:
    def __init__(self, ruta_personaje):
        self.window = tk.Tk()
        
        with open(os.path.join(ruta_personaje, "config.json"), "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.window.overrideredirect(True)
        self.window.wm_attributes('-transparentcolor', 'black')
        self.window.attributes('-topmost', True)

        img_path = os.path.join(ruta_personaje, "rias.png")
        img_base = Image.open(img_path).convert("RGBA")
        
        datas = img_base.getdata()
        newData = []
        for item in datas:
            if item[0] > 240 and item[1] > 240 and item[2] > 240:
                newData.append((0, 0, 0, 0))
            else:
                newData.append(item)
        img_base.putdata(newData)
        
        self.tamano = 200
        self.img_base = img_base.resize(
            (self.tamano, self.tamano), 
            Image.Resampling.NEAREST
        )

        self.precalcular_animaciones()
        self.direccion = 1
        self.tick_animacion = 0
        
        self.canvas = tk.Canvas(
            self.window, width=self.tamano, 
            height=self.tamano, bg='black', 
            bd=0, highlightthickness=0
        )
        self.canvas.pack()

        self.sprite_canvas_id = self.canvas.create_image(
            self.tamano//2, self.tamano//2, 
            image=self.cache_der[0]
        )

        # GLOBO DE CHAT PERMANENTE
        self.globo = tk.Toplevel(self.window)
        self.globo.overrideredirect(True)
        self.globo.attributes('-topmost', True)
        self.globo.config(
            bg="#16161D", bd=2, relief="solid", 
            highlightbackground="#FF3366"
        )
        
        self.globo_lbl = tk.Label(
            self.globo, 
            text="Presidenta Rias. Clic derecho para opciones.", 
            bg="#16161D", fg="#E1E1E6", 
            font=("Segoe UI", 10, "bold"), 
            wraplength=220, justify="center"
        )
        self.globo_lbl.pack(padx=12, pady=10)

        self.entry_chat = tk.Entry(
            self.globo, bg="#24242D", fg="white", bd=0, 
            insertbackground="white", font=("Segoe UI", 10), 
            highlightthickness=1, highlightbackground="#FF3366"
        )
        self.entry_chat.pack(padx=12, pady=8, fill="x")
        self.entry_chat.bind("<Return>", self.enviar_mensaje_usuario)

        # MENÚ TÁCTIL RESTAURADO
        self.menu = tk.Menu(
            self.window, tearoff=0, bg="#16161D", 
            fg="white", activebackground="#FF3366"
        )
        self.menu.add_command(
            label="💬 Abrir/Ocultar Chat", 
            command=self.conmutar_chat_directo
        )
        self.menu.add_command(
            label="✨ Desplegar Aura Mágica", 
            command=self.accion_magica
        )
        self.menu.add_separator()
        self.menu.add_command(
            label="❌ Cerrar Mascota", 
            command=self.window.quit
        )

        self.screen_width = self.window.winfo_screenwidth()
        self.screen_height = self.window.winfo_screenheight()
        self.x_pos = random.randint(200, self.screen_width - 300)
        self.suelo_fijo = self.screen_height - (self.tamano + 40)
        self.y_pos = self.suelo_fijo
        
        self.window.geometry(f'+{self.x_pos}+{int(self.y_pos)}')
        self.actualizar_posicion_globo()

        # EVENTOS CLAVE REASIGNADOS
        self.canvas.bind("<Button-1>", self.iniciar_arrastre)
        self.canvas.bind("<B1-Motion>", self.arrastrar)
        self.canvas.bind("<ButtonRelease-1>", self.soltar)
        self.canvas.bind("<Button-3>", self.desplegar_menu)

        self.estado = "quieto"
        self.chat_abierto = False
        self.particulas = []
        
        self.actualizar_motor()
        threading.Thread(target=self.bucle_monitoreo_ia, daemon=True).start()
        self.window.mainloop()

    def precalcular_animaciones(self):
        self.cache_der = []
        self.cache_izq = []
        for i in range(16):
            angulo = math.sin((i / 16) * math.pi * 2) * 4
            img_rot_der = self.img_base.rotate(angulo)
            img_rot_izq = ImageOps.mirror(self.img_base).rotate(-angulo)
            self.cache_der.append(ImageTk.PhotoImage(img_rot_der))
            self.cache_izq.append(ImageTk.PhotoImage(img_rot_izq))

    def actualizar_motor(self):
        self.tick_animacion = (self.tick_animacion + 1) % 16
        self.canvas.delete("particula")
        
        if self.y_pos < self.suelo_fijo and self.estado != "arrastrando":
            self.estado = "cayendo"
            self.y_pos += 16
            if self.y_pos > self.suelo_fijo:
                self.y_pos = self.suelo_fijo
                self.estado = "quieto"

        if not self.chat_abierto and self.estado == "quieto":
            rand = random.random()
            if rand < 0.02:
                self.estado = "caminando"
                self.direccion = random.choice([1, -1])
                self.pasos_restantes = random.randint(30, 80)
            elif rand > 0.985:
                self.estado = "flotando"
                self.pasos_restantes = 60

        offset_y = 0
        if self.estado == "caminando":
            self.x_pos += (3 * self.direccion)
            if self.x_pos < 0 or self.x_pos > self.screen_width - self.tamano:
                self.direccion *= -1
            offset_y = abs(math.sin((self.tick_animacion / 16) * math.pi * 2)) * 6
            self.pasos_restantes -= 1
            if self.pasos_restantes <= 0: self.estado = "quieto"
            
        elif self.estado == "flotando" or self.estado == "magia":
            offset_y = math.sin((self.tick_animacion / 16) * math.pi * 2) * 12
            if self.estado == "magia":
                self.generar_efecto_aura()
                self.pasos_restantes -= 1
                if self.pasos_restantes <= 0: self.estado = "quieto"
            else:
                self.pasos_restantes -= 1
                if self.pasos_restantes <= 0: self.estado = "quieto"

        lista_actual = self.cache_der if self.direccion == 1 else self.cache_izq
        self.img_actual_tk = lista_actual[self.tick_animacion]
        self.canvas.itemconfig(self.sprite_canvas_id, image=self.img_actual_tk)
        
        self.renderizar_y_mover_particulas()
        self.window.geometry(f'+{self.x_pos}+{int(self.y_pos - offset_y)}')
        self.actualizar_posicion_globo()
        self.window.after(35, self.actualizar_motor)

    def generar_efecto_aura(self):
        for _ in range(2):
            px = self.tamano // 2 + random.randint(-35, 35)
            py = self.tamano // 2 + random.randint(-45, 45)
            largo = random.randint(4, 10)
            color = random.choice(["#FF3366", "#FF0033", "#D100D1"])
            velocidad = random.randint(3, 6)
            self.particulas.append({
                "x": px, "y": py, "l": largo, 
                "color": color, "v": velocidad
            })

    def renderizar_y_mover_particulas(self):
        particulas_vivas = []
        for p in self.particulas:
            p["y"] -= p["v"]
            p["x"] += random.choice([-1, 0, 1])
            
            # Cruz pixel art limpia sin manchas
            self.canvas.create_line(
                p["x"] - p["l"], p["y"], p["x"] + p["l"], p["y"], 
                fill=p["color"], width=2, tags="particula"
            )
            self.canvas.create_line(
                p["x"], p["y"] - p["l"], p["x"], p["y"] + p["l"], 
                fill=p["color"], width=2, tags="particula"
            )
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
        self.estado = "quieto"

    def conmutar_chat_directo(self):
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
        self.estado = "magia"
        self.pasos_restantes = 100
        self.mostrar_comentario_autonomo("¡Por el orgullo del clan Gremory!")

    def actualizar_posicion_globo(self):
        self.globo.geometry(f"+{self.x_pos - 20}+{int(self.y_pos - 120)}")

    def enviar_mensaje_usuario(self, event):
        msg = self.entry_chat.get().strip()
        if not msg: return
        self.entry_chat.delete(0, tk.END)
        self.globo_lbl.config(text="Pensando...")
        threading.Thread(
            target=self.procesar_conversacion_ia, 
            args=(msg,), daemon=True
        ).start()

    def procesar_conversacion_ia(self, mensaje_usuario):
        try:
            prompt = f"{self.config['personalidad']} El usuario dice: '{mensaje_usuario}'. Responde corto (12 palabras max) en espanol."
            response = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=prompt
            )
            texto = response.text.strip().replace('"', '')
            self.window.after(0, lambda: self.globo_lbl.config(text=texto))
        except:
            self.window.after(0, lambda: self.globo_lbl.config(text="Error..."))

    def bucle_monitoreo_ia(self):
        while True:
            time.sleep(30)
            if not self.chat_abierto:
                try:
                    v = gw.getActiveWindow()
                    ventana = v.title if v else "Escritorio"
                    prompt = f"{self.config['personalidad']} El usuario ve: '{ventana}'. Comenta en personaje (10 palabras max)."
                    response = client.models.generate_content(
                        model='gemini-2.5-flash', 
                        contents=prompt
                    )
                    texto = response.text.strip().replace('"', '')
                    self.window.after(0, lambda: self.mostrar_comentario_autonomo(texto))
                except: 
                    pass

    def mostrar_comentario_autonomo(self, texto):
        if not self.chat_abierto:
            self.globo_lbl.config(text=texto)
            self.globo.deiconify()
            self.window.after(
                7000, 
                lambda: self.globo.withdraw() if not self.chat_abierto else None
            )

    def desplegar_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

if __name__ == "__main__":
    pass

