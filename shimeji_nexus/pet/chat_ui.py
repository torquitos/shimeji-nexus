import os
import threading
import time
import tkinter as tk
import tkinter.font as tkfont

import pygetwindow as gw
from PIL import ImageTk

from shimeji_nexus.ai import client as ai_manager
from shimeji_nexus.audio import sound_manager
from shimeji_nexus.core import image_utils
from shimeji_nexus.ui import theme

ESTILO_DEFECTO = {"fuente": "Segoe UI", "tam": 10, "adorno": "", "forma": "redondeada", "borde": "simple", "esquina": 14}

PAD = 14
MAXW = 230
COLA = 14
MARGEN = 12


def _contorno_redondeado(x1, y1, x2, y2, r):
    return [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]


def _contorno_grito(x1, y1, x2, y2, paso=13, salto=6):
    """Globo de grito: los cuatro lados en zigzag."""
    n = max(2, int((x2 - x1) / paso))
    m = max(2, int((y2 - y1) / paso))
    p = []
    for i in range(n + 1):
        p += [x1 + (x2 - x1) * i / n, y1 - (salto if i % 2 else 0)]
    for i in range(1, m + 1):
        p += [x2 + (salto if i % 2 else 0), y1 + (y2 - y1) * i / m]
    for i in range(1, n + 1):
        p += [x2 - (x2 - x1) * i / n, y2 + (salto if i % 2 else 0)]
    for i in range(1, m):
        p += [x1 - (salto if i % 2 else 0), y2 - (y2 - y1) * i / m]
    return p


class ChatBubble:
    """Globo de dialogo del personaje, con su propia forma, tipografia y colores. Muestra comentarios,
    avisos y el chat con IA (el cuadro de escritura solo aparece cuando se abre el chat)."""

    def __init__(self, window, config, x_pos, y_pos, on_estado_quieto, on_comando=None, ruta=None):
        self.window = window
        self.config = config
        self.on_estado_quieto = on_estado_quieto
        self.on_comando = on_comando
        self.chat_abierto = False
        self.x_pos, self.y_pos = x_pos, y_pos

        estilo = dict(ESTILO_DEFECTO)
        estilo.update(config.get("chat") or {})
        if estilo["fuente"] not in set(tkfont.families(window)):
            estilo["fuente"] = ESTILO_DEFECTO["fuente"]
        self.estilo = estilo

        color = config.get("color_texto")
        self.acento = theme.acento_desde_color_texto(color) if color else theme.ACCENT_DEFAULT
        self.fondo = theme.blend_color(self.acento, "#0b0b0f", 0.16)
        self.nombre = (config.get("nombre") or "").split()[0] if config.get("nombre") else ""
        self.avatar = self._cargar_avatar(ruta)

        self.globo = tk.Toplevel(window)
        self.globo.overrideredirect(True)
        self.globo.attributes("-topmost", True)
        self.globo.wm_attributes("-transparentcolor", "black")
        self.globo.configure(bg="black")
        self.canvas = tk.Canvas(self.globo, bg="black", bd=0, highlightthickness=0)
        self.canvas.pack()
        self.entry_chat = tk.Entry(
            self.canvas, bg=theme.blend_color(self.acento, "#0b0b0f", 0.30), fg=theme.TEXT, bd=0,
            insertbackground=self.acento, font=(estilo["fuente"], estilo["tam"]), highlightthickness=1,
            highlightbackground=self.acento, highlightcolor=self.acento)
        self.entry_chat.bind("<Return>", self.enviar_mensaje_usuario)

        self.texto = ""
        self._revelado = 0
        self._id_texto = None
        self._ancho = self._alto = 10
        self._job_revelar = None
        self._job_ocultar = None
        self._pensando = False
        self.globo.withdraw()
        self.mostrar_comentario_autonomo(config.get("saludo", "¡Hola!"))

    def _cargar_avatar(self, ruta):
        try:
            archivo = self.config.get("imagen")
            if ruta and archivo and os.path.exists(os.path.join(ruta, archivo)):
                return ImageTk.PhotoImage(image_utils.cargar_avatar(os.path.join(ruta, archivo), 28))
        except Exception:
            pass
        return None

    # ---------- dibujo ----------
    def _dibujar(self):
        c, e = self.canvas, self.estilo
        c.delete("all")
        fuente = (e["fuente"], e["tam"])
        medida = c.create_text(0, 0, text=self.texto or " ", font=fuente, width=MAXW, anchor="nw")
        bx0, by0, bx1, by1 = c.bbox(medida)
        c.delete(medida)
        tw, th = max(bx1 - bx0, 100), by1 - by0
        cabecera = 44 if self.avatar else 30
        ancho = max(tw, 150) + 2 * PAD
        alto = cabecera + 4 + th + PAD + (40 if self.chat_abierto else 0)
        W, H = ancho + 2 * MARGEN, alto + COLA + 2 * MARGEN
        x1, y1, x2, y2 = MARGEN, MARGEN, MARGEN + ancho, MARGEN + alto
        r = e["esquina"]
        grito = e["forma"] == "grito"
        cx = W / 2

        def contorno(dx=0, dy=0, ex=0):
            if grito:
                return _contorno_grito(x1 - ex + dx, y1 - ex + dy, x2 + ex + dx, y2 + ex + dy)
            return _contorno_redondeado(x1 - ex + dx, y1 - ex + dy, x2 + ex + dx, y2 + ex + dy, r + ex)

        c.create_polygon(contorno(3, 4), fill="#07070a", outline="", smooth=not grito)
        if e["borde"] == "doble" and not grito:
            c.create_polygon(contorno(ex=4), fill="", outline=self.acento, width=1, smooth=True)
        c.create_polygon([cx - 10, y2 - 1, cx + 10, y2 - 1, cx, y2 + COLA], fill=self.fondo, outline=self.acento, width=2)
        c.create_polygon(contorno(), fill=self.fondo, outline=self.acento, width=2, smooth=not grito)
        c.create_rectangle(cx - 8, y2 - 2, cx + 8, y2 + 1, fill=self.fondo, outline="")

        nx = x1 + PAD
        if self.avatar:
            c.create_oval(nx - 2, y1 + 6, nx + 30, y1 + 38, fill=theme.blend_color(self.acento, "#0b0b0f", 0.35), outline=self.acento, width=2)
            c.create_image(nx + 14, y1 + 22, image=self.avatar)
            nx += 38
        titulo = f"{self.nombre.upper()}  {e['adorno']}".strip()
        c.create_text(nx, y1 + (22 if self.avatar else 16), text=titulo, font=(e["fuente"], e["tam"] - 1, "bold"), fill=self.acento, anchor="w")
        c.create_line(x1 + PAD, y1 + cabecera - 2, x2 - PAD, y1 + cabecera - 2, fill=theme.blend_color(self.acento, "#0b0b0f", 0.45))

        self._id_texto = c.create_text(x1 + PAD, y1 + cabecera + 4, text=self.texto[:self._revelado], font=fuente,
                                       fill=theme.TEXT, width=MAXW, anchor="nw")
        if self.chat_abierto:
            c.create_window(x1 + PAD, y2 - PAD - 28, window=self.entry_chat, anchor="nw", width=ancho - 2 * PAD, height=28)

        c.config(width=W, height=H)
        self._ancho, self._alto = W, H
        self._reposicionar()

    def _reposicionar(self):
        sw = self.window.winfo_screenwidth()
        x = int(self.x_pos + 100 - self._ancho / 2)
        x = max(0, min(sw - self._ancho, x))
        y = max(0, int(self.y_pos + 10 - self._alto))
        self.globo.geometry(f"+{x}+{y}")

    def actualizar_posicion(self, x_pos, y_pos):
        self.x_pos, self.y_pos = x_pos, y_pos
        self._reposicionar()

    def _revelar(self):
        if self._job_revelar:
            self.window.after_cancel(self._job_revelar)

        def paso():
            if self._revelado >= len(self.texto):
                return
            self._revelado = min(len(self.texto), self._revelado + 2)
            self.canvas.itemconfig(self._id_texto, text=self.texto[:self._revelado])
            self._job_revelar = self.window.after(22, paso)

        paso()

    def _poner_texto(self, texto):
        self.texto = texto
        self._revelado = 0
        self._dibujar()
        self._revelar()

    def _mostrar(self, texto, ms):
        self._pensando = False
        self._poner_texto(texto)
        self.globo.deiconify()
        self.globo.lift()
        if self._job_ocultar:
            self.window.after_cancel(self._job_ocultar)
        if not self.chat_abierto:
            self._job_ocultar = self.window.after(ms + 25 * len(texto), self._ocultar)

    def _ocultar(self):
        if not self.chat_abierto:
            self.globo.withdraw()

    # ---------- interfaz que usa la mascota ----------
    def mostrar_comentario_autonomo(self, texto):
        if not self.chat_abierto:
            self._mostrar(texto, 7000)

    def avisar(self, texto, ms=15000):
        """Aviso que se muestra aunque el chat este abierto (pomodoro, recordatorios, comandos)."""
        self._mostrar(texto, ms)

    def conmutar(self):
        sound_manager.reproducir("chat")
        if self.chat_abierto:
            self.chat_abierto = False
            self.globo.withdraw()
            return
        self.chat_abierto = True
        self._poner_texto(self.texto or self.config.get("saludo", "¡Hola!"))
        self.globo.deiconify()
        self.globo.lift()
        self.on_estado_quieto()
        self.window.after(60, self.entry_chat.focus_force)

    def enviar_mensaje_usuario(self, event):
        msg = self.entry_chat.get().strip()
        if not msg:
            return
        self.entry_chat.delete(0, tk.END)
        if msg.startswith("/") and self.on_comando:
            self._poner_texto(self.on_comando(msg))
            return
        sound_manager.reproducir("chat")
        self._pensar()
        threading.Thread(target=self._procesar_conversacion_ia, args=(msg,), daemon=True).start()

    def _pensar(self):
        self._pensando = True
        self.texto = "· · ·"
        self._revelado = len(self.texto)
        self._dibujar()
        self._ciclo_pensar(0)

    def _ciclo_pensar(self, i):
        if not self._pensando:
            return
        self.canvas.itemconfig(self._id_texto, text=("·", "· ·", "· · ·")[i % 3])
        self.window.after(350, lambda: self._ciclo_pensar(i + 1))

    def _respuesta(self, texto):
        self._pensando = False
        self._poner_texto(texto)

    def _procesar_conversacion_ia(self, mensaje_usuario):
        try:
            texto = ai_manager.generar_texto(self.config["personalidad"], mensaje_usuario, 12)
        except Exception as e:
            print(f"Error en IA: {e}")
            texto = "Error..."
        self.window.after(0, lambda: self._respuesta(texto))

    def iniciar_monitoreo_ia(self):
        threading.Thread(target=self._bucle_monitoreo_ia, daemon=True).start()

    def _bucle_monitoreo_ia(self):
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
