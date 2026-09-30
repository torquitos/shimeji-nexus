import threading
import time
import tkinter as tk

import pygetwindow as gw

from shimeji_nexus.ai import client as ai_manager
from shimeji_nexus.audio import sound_manager


class ChatBubble:
    """Globo de chat: texto, entry de usuario, comentarios autónomos y monitoreo de IA."""

    def __init__(self, window, config, x_pos, y_pos, on_estado_quieto):
        self.window = window
        self.config = config
        self.chat_abierto = False
        self.on_estado_quieto = on_estado_quieto

        self.globo = tk.Toplevel(window)
        self.globo.overrideredirect(True)
        self.globo.attributes("-topmost", True)
        self.globo.config(bg="#16161D", bd=2, relief="solid", highlightbackground="#FF3366")
        self.globo_lbl = tk.Label(self.globo, text=config.get("saludo", "¡Hola!"), bg="#16161D", fg="#E1E1E6", font=("Segoe UI", 10, "bold"), wraplength=220, justify="center")
        self.globo_lbl.pack(padx=12, pady=10)
        self.entry_chat = tk.Entry(self.globo, bg="#24242D", fg="white", bd=0, insertbackground="white", font=("Segoe UI", 10), highlightthickness=1, highlightbackground="#FF3366")
        self.entry_chat.pack(padx=12, pady=8, fill="x")
        self.entry_chat.bind("<Return>", self.enviar_mensaje_usuario)

        self.actualizar_posicion(x_pos, y_pos)

    def actualizar_posicion(self, x_pos, y_pos):
        self.globo.geometry(f"+{x_pos - 20}+{int(y_pos - 120)}")

    def conmutar(self):
        sound_manager.reproducir("chat")
        if self.chat_abierto:
            self.globo.withdraw()
            self.chat_abierto = False
        else:
            self.globo.deiconify()
            self.chat_abierto = True
            self.on_estado_quieto()
            self.entry_chat.focus_set()

    def enviar_mensaje_usuario(self, event):
        msg = self.entry_chat.get().strip()
        if not msg:
            return
        self.entry_chat.delete(0, tk.END)
        self.globo_lbl.config(text="Pensando...")
        sound_manager.reproducir("chat")
        threading.Thread(target=self._procesar_conversacion_ia, args=(msg,), daemon=True).start()

    def _procesar_conversacion_ia(self, mensaje_usuario):
        try:
            texto = ai_manager.generar_texto(self.config["personalidad"], mensaje_usuario, 12)
            self.window.after(0, lambda: self.globo_lbl.config(text=texto))
        except Exception as e:
            print(f"Error en IA: {e}")
            self.window.after(0, lambda: self.globo_lbl.config(text="Error..."))

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

    def mostrar_comentario_autonomo(self, texto):
        if not self.chat_abierto:
            self.globo_lbl.config(text=texto)
            self.globo.deiconify()
            self.window.after(7000, lambda: self.globo.withdraw() if not self.chat_abierto else None)
