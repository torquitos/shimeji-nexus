import json
import os
import re
from tkinter import messagebox

import customtkinter as ctk

from shimeji_nexus.core.paths import base_dir
from shimeji_nexus.ui import theme
from shimeji_nexus.ui.theme import siguiente_color_rotativo


class AddCharacterWindow:
    def __init__(self, parent, launcher):
        self.parent = parent
        self.launcher = launcher
        self.win = ctk.CTkToplevel(parent)
        self.win.title("Agregar personaje")
        self.win.geometry("540x660")
        self.win.configure(fg_color=theme.BG)
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        self.rutas_img = {"quieto": ctk.StringVar(), "caminando": ctk.StringVar(), "saludo": ctk.StringVar()}

        main = ctk.CTkFrame(self.win, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=28, pady=26)

        ctk.CTkLabel(main, text="Nuevo personaje", font=theme.FONT_DISPLAY, text_color=theme.TEXT).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(main, text="Se le asignará un color de acento automáticamente", font=theme.FONT_CAPTION, text_color=theme.TEXT_FAINT).pack(anchor="w", pady=(0, 18))

        ctk.CTkLabel(main, text="Nombre del personaje", font=theme.FONT_CAPTION_BOLD, text_color=theme.TEXT_DIM, anchor="w").pack(anchor="w", pady=(0, 4))
        self.entry_nombre = ctk.CTkEntry(main, fg_color=theme.CARD, border_color=theme.BORDER, text_color=theme.TEXT, corner_radius=10, height=38, font=theme.FONT_BODY)
        self.entry_nombre.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(main, text="Anime / serie (opcional)", font=theme.FONT_CAPTION_BOLD, text_color=theme.TEXT_DIM, anchor="w").pack(anchor="w", pady=(0, 4))
        self.entry_anime = ctk.CTkEntry(main, fg_color=theme.CARD, border_color=theme.BORDER, text_color=theme.TEXT, corner_radius=10, height=38, font=theme.FONT_BODY)
        self.entry_anime.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(main, text="Imágenes del personaje", font=theme.FONT_CAPTION_BOLD, text_color=theme.TEXT_DIM, anchor="w").pack(anchor="w", pady=(0, 6))
        self._crear_selector_img(main, "Quieto (obligatorio)", "quieto")
        self._crear_selector_img(main, "Caminando (opcional)", "caminando")
        self._crear_selector_img(main, "Saludo (opcional)", "saludo")

        ctk.CTkLabel(main, text="Personalidad (opcional)", font=theme.FONT_CAPTION_BOLD, text_color=theme.TEXT_DIM, anchor="w").pack(anchor="w", pady=(14, 4))
        self.text_pers = ctk.CTkTextbox(main, height=90, fg_color=theme.CARD, border_color=theme.BORDER, border_width=1, text_color=theme.TEXT, corner_radius=10, font=theme.FONT_BODY)
        self.text_pers.pack(fill="x", pady=(0, 18))
        self.text_pers.insert("1.0", "Actúa como [personaje] de [anime]. Eres un personaje amigable y carismático.")

        ctk.CTkButton(
            main, text="Crear personaje", command=self.crear,
            fg_color=theme.ACCENT_DEFAULT, hover_color=theme.blend_color("#ffffff", theme.ACCENT_DEFAULT, 0.15),
            text_color=theme.BG, font=theme.FONT_BODY_MEDIUM, corner_radius=12, height=44,
        ).pack(fill="x", pady=(4, 0))

    def _crear_selector_img(self, parent, texto, key):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", pady=3)
        ctk.CTkLabel(f, text=texto, font=theme.FONT_CAPTION, text_color=theme.TEXT_DIM, width=170, anchor="w").pack(side="left")
        ctk.CTkLabel(f, textvariable=self.rutas_img[key], font=theme.FONT_CAPTION, text_color=theme.TEXT, anchor="w").pack(side="left", fill="x", expand=True, padx=8)
        ctk.CTkButton(
            f, text="Elegir...", width=70, command=lambda k=key: self._seleccionar(k),
            fg_color=theme.CARD, hover_color=theme.CARD_HOVER, text_color=theme.TEXT_DIM,
            border_width=1, border_color=theme.BORDER, corner_radius=8, font=theme.FONT_CAPTION,
        ).pack(side="right")

    def _seleccionar(self, key):
        from tkinter import filedialog
        ruta = filedialog.askopenfilename(title=f"Seleccionar imagen {key}", filetypes=[("PNG", "*.png"), ("Imagenes", "*.png *.jpg *.jpeg")])
        if ruta:
            self.rutas_img[key].set(ruta)

    def crear(self):
        import shutil
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Error", "El nombre es obligatorio.")
            return
        folder = re.sub(r"[^a-z0-9_]", "", nombre.lower().replace(" ", "_"))
        ruta_pj = os.path.join(base_dir(), "personajes", folder)
        if os.path.exists(ruta_pj):
            messagebox.showwarning("Error", "Ya existe un personaje con ese nombre.")
            return
        quieto_src = self.rutas_img["quieto"].get()
        if not quieto_src or not os.path.exists(quieto_src):
            messagebox.showwarning("Error", "La imagen Quieto es obligatoria.")
            return
        os.makedirs(ruta_pj, exist_ok=True)
        ruta_personajes = os.path.join(base_dir(), "personajes")
        cantidad_existente = len([d for d in os.listdir(ruta_personajes) if os.path.isdir(os.path.join(ruta_personajes, d))]) - 1
        color_texto_nuevo = siguiente_color_rotativo(max(cantidad_existente, 0))
        anime = self.entry_anime.get().strip()
        pers_text = self.text_pers.get("1.0", "end-1c").strip()
        if not pers_text or pers_text == "Actúa como [personaje] de [anime]. Eres un personaje amigable y carismático.":
            if anime:
                pers_text = f"Actúa como {nombre} de {anime}. Eres un personaje amigable, carismático y divertido. Hablas con energia y siempre animas al usuario."
            else:
                pers_text = f"Actúa como {nombre}. Eres un personaje amigable, carismático y divertido. Hablas con energia y siempre animas al usuario."
        img_names = {}
        for estado, key in [("quieto", "quieto"), ("caminando", "caminando"), ("saludo", "saludo")]:
            src = self.rutas_img[key].get()
            if src and os.path.exists(src):
                ext = os.path.splitext(src)[1] or ".png"
                dst = os.path.join(ruta_pj, f"{estado}{ext}")
                shutil.copy2(src, dst)
                img_names[estado] = f"{estado}{ext}"
        if "caminando" in img_names or "saludo" in img_names:
            config = {"nombre": nombre, "personalidad": pers_text,
                      "frames": {"quieto": img_names.get("quieto", "quieto.png"),
                                 "caminando": img_names.get("caminando", img_names.get("quieto", "quieto.png")),
                                 "saludo": img_names.get("saludo", img_names.get("quieto", "quieto.png"))},
                      "imagen": img_names.get("quieto", "quieto.png"),
                      "saludo": f"¡Hola! Soy {nombre}~",
                      "color_globo": "#E1E1E6", "color_texto": color_texto_nuevo}
        else:
            config = {"nombre": nombre, "personalidad": pers_text,
                      "imagen": img_names.get("quieto", "quieto.png"),
                      "saludo": f"¡Hola! Soy {nombre}~",
                      "color_globo": "#E1E1E6", "color_texto": color_texto_nuevo}
        with open(os.path.join(ruta_pj, "config.json"), "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        messagebox.showinfo("Creado", f"{nombre} agregado correctamente.")
        self.launcher.escanear_personajes()
        self.win.destroy()
