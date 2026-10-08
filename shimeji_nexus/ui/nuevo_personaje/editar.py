import json
import os
from tkinter import messagebox

import customtkinter as ctk

from shimeji_nexus.core.memoria import Memoria
from shimeji_nexus.core.paths import base_dir
from shimeji_nexus.ui import theme, ventanas
from shimeji_nexus.ui.ajustes.componentes import boton_primario, boton_secundario, campo, encabezado, fila_switch, seccion
from shimeji_nexus.ui.theme import PALETA_ROTATIVA_COLOR_TEXTO, acento_desde_color_texto


class EditarPersonajeWindow:
    """Cambiar lo que se escribio al crear un personaje: nombre, saludo, personalidad, color, si habla y su tecnica."""

    def __init__(self, parent, launcher, info):
        self.launcher, self.info = launcher, info
        self.ruta = os.path.join(base_dir(), "personajes", info["folder"], "config.json")
        with open(self.ruta, encoding="utf-8-sig") as f:
            self.config = json.load(f)
        hab = self.config.get("habilidad") or {}
        self.win = ctk.CTkToplevel(parent)
        self.win.title(f"Editar a {info['nombre']}")
        ventanas.centrar_sobre(self.win, parent, 560, 780)
        self.win.configure(fg_color=theme.BG)
        ventanas.estilizar(self.win)
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.color = self.config.get("color_texto") or PALETA_ROTATIVA_COLOR_TEXTO[0]
        self.var_habla = ctk.BooleanVar(value=self.config.get("habla", True))
        pie = ctk.CTkFrame(self.win, fg_color="transparent")
        pie.pack(side="bottom", fill="x", padx=32, pady=(10, 28))
        boton_primario(pie, "Guardar", self.guardar, 110).pack(side="right")
        boton_secundario(pie, "Cancelar", self.win.destroy, 100).pack(side="right", padx=(0, 8))
        cuerpo = ctk.CTkScrollableFrame(self.win, fg_color="transparent", scrollbar_button_color=theme.BG, scrollbar_button_hover_color=theme.DIVIDER)
        cuerpo.pack(fill="both", expand=True, padx=(32, 18), pady=(28, 0))
        encabezado(cuerpo, "Editar personaje", "Los cambios se aplican la próxima vez que lo invoques.")
        card = seccion(cuerpo, "Quién es")
        self.nombre = self._campo(card, "Nombre", self.config["nombre"])
        self.saludo = self._campo(card, "Cómo saluda", self.config.get("saludo", ""))
        ctk.CTkLabel(card, text="Personalidad", font=theme.FONT_CAPTION, text_color=theme.TEXT_DIM).pack(anchor="w", padx=16, pady=(12, 4))
        self.personalidad = ctk.CTkTextbox(card, height=130, fg_color=theme.FIELD, border_color=theme.DIVIDER, border_width=1, corner_radius=8,
                                           text_color=theme.TEXT, font=theme.FONT_BODY, wrap="word")
        self.personalidad.pack(fill="x", padx=16, pady=(0, 14))
        self.personalidad.insert("1.0", self.config.get("personalidad", ""))
        card = seccion(cuerpo, "Color")
        self.muestras = ctk.CTkFrame(card, fg_color="transparent")
        self.muestras.pack(fill="x", padx=16, pady=14)
        self.botones_color = {}
        for i, c in enumerate(PALETA_ROTATIVA_COLOR_TEXTO):
            b = ctk.CTkButton(self.muestras, text="", width=34, height=34, corner_radius=17, fg_color=acento_desde_color_texto(c), hover_color=acento_desde_color_texto(c),
                              border_width=3, command=lambda c=c: self._elegir_color(c))
            b.grid(row=0, column=i, padx=(0, 8))
            self.botones_color[c] = b
        self._elegir_color(self.color)
        card = seccion(cuerpo, "Cómo se comporta")
        fila_switch(card, "Habla", "Si lo apagas solo maúlla o hace sonidos, sin chat ni IA.", self.var_habla)
        card = seccion(cuerpo, "Su técnica")
        self.tec_nombre = self._campo(card, "Nombre de la técnica", hab.get("nombre", ""))
        self.tec_desc = self._campo(card, "Descripción", hab.get("descripcion", ""))
        ctk.CTkFrame(card, fg_color="transparent", height=10).pack()
        ventanas.mostrar(self.win, modal=True)

    def _campo(self, card, titulo, valor):
        ctk.CTkLabel(card, text=titulo, font=theme.FONT_CAPTION, text_color=theme.TEXT_DIM).pack(anchor="w", padx=16, pady=(12, 4))
        entrada = campo(card)
        entrada.pack(fill="x", padx=16)
        entrada.insert(0, valor)
        return entrada

    def _elegir_color(self, color):
        self.color = color
        for c, b in self.botones_color.items():
            b.configure(border_color=theme.TEXT if c == color else theme.BG)

    def guardar(self):
        nombre = self.nombre.get().strip()
        if not nombre:
            return messagebox.showinfo("Falta algo", "El personaje necesita un nombre.", parent=self.win)
        viejo = self.config["nombre"]
        self.config.update(nombre=nombre, saludo=self.saludo.get().strip(), personalidad=self.personalidad.get("1.0", "end-1c").strip(),
                           color_texto=self.color)
        if self.var_habla.get():
            self.config.pop("habla", None)
        else:
            self.config["habla"] = False
        hab = dict(self.config.get("habilidad") or {})
        if self.tec_nombre.get().strip():
            hab["nombre"] = self.tec_nombre.get().strip()
        hab["descripcion"] = self.tec_desc.get().strip()
        if hab:
            self.config["habilidad"] = hab
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
        if nombre != viejo:
            Memoria(viejo).olvidar()
        self.launcher.cerrar_por_nombre(viejo)
        self.win.destroy()
        self.launcher.personaje_seleccionado = None
        self.launcher.escanear_personajes()
