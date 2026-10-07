import os
import threading
import webbrowser

import customtkinter as ctk

from shimeji_nexus.ai import client as ia
from shimeji_nexus.core import env_store
from shimeji_nexus.core import settings as settings_manager
from shimeji_nexus.ui import theme

TAB_GENERAL = "General"
TAB_IA = "Inteligencia artificial"


class SettingsWindow:
    def __init__(self, parent):
        self.parent = parent
        self.win = ctk.CTkToplevel(parent)
        self.win.title("Configuración")
        self.win.geometry("470x740")
        self.win.configure(fg_color=theme.BG)
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        self.settings = settings_manager.cargar()

        ctk.CTkButton(
            self.win, text="Guardar configuración", command=self.guardar,
            fg_color=theme.ACCENT_DEFAULT, hover_color=theme.blend_color("#ffffff", theme.ACCENT_DEFAULT, 0.15), text_color=theme.BG,
            font=theme.FONT_BODY_MEDIUM, corner_radius=12, height=44,
        ).pack(side="bottom", fill="x", padx=28, pady=(8, 24))

        self.tabs = ctk.CTkTabview(
            self.win, fg_color=theme.BG, segmented_button_fg_color=theme.PANEL,
            segmented_button_selected_color=theme.ACCENT_DEFAULT, segmented_button_selected_hover_color=theme.ACCENT_DEFAULT,
            segmented_button_unselected_color=theme.PANEL, segmented_button_unselected_hover_color=theme.CARD,
            text_color=theme.TEXT, corner_radius=12,
        )
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(20, 0))
        self._tab_general(self.tabs.add(TAB_GENERAL))
        self._tab_ia(self.tabs.add(TAB_IA))

    # ---------- General ----------
    def _tab_general(self, tab):
        marco = ctk.CTkScrollableFrame(tab, fg_color="transparent", scrollbar_button_color=theme.BG, scrollbar_button_hover_color=theme.BORDER)
        marco.pack(fill="both", expand=True)

        ctk.CTkLabel(marco, text="Comportamiento", font=theme.FONT_DISPLAY, text_color=theme.TEXT).pack(anchor="w", pady=(4, 2))
        ctk.CTkLabel(marco, text="Ajusta cómo se mueven y reaccionan tus mascotas", font=theme.FONT_CAPTION, text_color=theme.TEXT_FAINT).pack(anchor="w", pady=(0, 14))

        self.var_monitoreo = ctk.BooleanVar(value=self.settings.get("monitoreo_ia", True))
        self._crear_switch(marco, "Monitoreo de ventana activa", "Comenta la ventana activa cada 30s con IA", self.var_monitoreo)
        self.var_particulas = ctk.BooleanVar(value=self.settings.get("particulas", True))
        self._crear_switch(marco, "Efectos de partículas", "Habilidades y estelas al interactuar", self.var_particulas)
        self.var_sonido = ctk.BooleanVar(value=self.settings.get("sonido", True))
        self._crear_switch(marco, "Sonidos de la aplicación", "Efectos de sonido al invocar y cerrar", self.var_sonido)
        self.var_hab_auto = ctk.BooleanVar(value=self.settings.get("habilidad_auto", True))
        self._crear_switch(marco, "Habilidades automáticas", "Cada 2 a 5 min usan su habilidad solos", self.var_hab_auto)

        ctk.CTkFrame(marco, fg_color=theme.BORDER, height=1).pack(fill="x", pady=(8, 16))

        self.var_transparencia = ctk.DoubleVar(value=self.settings.get("transparencia", 1.0))
        self._crear_slider(marco, "Transparencia de mascotas", self.var_transparencia, 0.3, 1.0)
        self.var_velocidad = ctk.DoubleVar(value=self.settings.get("velocidad", 1.0))
        self._crear_slider(marco, "Velocidad de animación", self.var_velocidad, 0.2, 3.0)
        self.var_trabajo = ctk.DoubleVar(value=self.settings.get("pomodoro_trabajo", 25))
        self._crear_slider(marco, "Pomodoro: minutos de trabajo", self.var_trabajo, 5, 60, 55)
        self.var_descanso = ctk.DoubleVar(value=self.settings.get("pomodoro_descanso", 5))
        self._crear_slider(marco, "Pomodoro: minutos de descanso", self.var_descanso, 1, 30, 29)

    # ---------- Inteligencia artificial ----------
    def _tab_ia(self, tab):
        marco = ctk.CTkFrame(tab, fg_color="transparent")
        marco.pack(fill="both", expand=True, padx=4)

        ctk.CTkLabel(marco, text="Tu propia IA", font=theme.FONT_DISPLAY, text_color=theme.TEXT).pack(anchor="w", pady=(4, 2))
        ctk.CTkLabel(marco, text="Las mascotas usan tu clave para conversar y comentar", font=theme.FONT_CAPTION, text_color=theme.TEXT_FAINT).pack(anchor="w", pady=(0, 16))

        self._nombre_a_clave = {datos[0]: clave for clave, datos in ia.PROVEEDORES.items()}
        actual = os.getenv("AI_PROVIDER", "gemini").strip().lower()
        if actual not in ia.PROVEEDORES:
            actual = "gemini"
        self.var_proveedor = ctk.StringVar(value=ia.PROVEEDORES[actual][0])

        ctk.CTkLabel(marco, text="Proveedor", font=theme.FONT_BODY_MEDIUM, text_color=theme.TEXT, anchor="w").pack(anchor="w", pady=(0, 6))
        ctk.CTkSegmentedButton(
            marco, values=list(self._nombre_a_clave), variable=self.var_proveedor, command=self._al_cambiar_proveedor,
            selected_color=theme.ACCENT_DEFAULT, selected_hover_color=theme.ACCENT_DEFAULT, unselected_color=theme.CARD,
            unselected_hover_color=theme.CARD_HOVER, fg_color=theme.CARD, text_color=theme.TEXT, height=36,
        ).pack(fill="x", pady=(0, 18))

        ctk.CTkLabel(marco, text="Clave de API", font=theme.FONT_BODY_MEDIUM, text_color=theme.TEXT, anchor="w").pack(anchor="w", pady=(0, 6))
        self.entry_clave = ctk.CTkEntry(
            marco, show="•", height=42, corner_radius=10, fg_color=theme.CARD, border_color=theme.BORDER,
            text_color=theme.TEXT, font=theme.FONT_BODY,
        )
        self.entry_clave.pack(fill="x")
        self.lbl_guardada = ctk.CTkLabel(marco, text="", font=theme.FONT_CAPTION, text_color=theme.TEXT_FAINT, anchor="w")
        self.lbl_guardada.pack(anchor="w", pady=(6, 14))

        fila = ctk.CTkFrame(marco, fg_color="transparent")
        fila.pack(fill="x")
        self.btn_probar = ctk.CTkButton(
            fila, text="Probar conexión", command=self._probar, height=40, corner_radius=10,
            fg_color=theme.CARD, hover_color=theme.CARD_HOVER, text_color=theme.TEXT,
            border_width=1, border_color=theme.BORDER, font=theme.FONT_BODY_MEDIUM,
        )
        self.btn_probar.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            fila, text="Conseguir una clave", command=self._abrir_pagina, height=40, corner_radius=10,
            fg_color="transparent", hover_color=theme.CARD, text_color=theme.TEXT_SOFT,
            border_width=1, border_color=theme.BORDER, font=theme.FONT_BODY_MEDIUM,
        ).pack(side="left", fill="x", expand=True)

        self.lbl_resultado = ctk.CTkLabel(marco, text="", font=theme.FONT_BODY, anchor="w", justify="left", wraplength=380)
        self.lbl_resultado.pack(anchor="w", pady=(14, 0))

        ctk.CTkLabel(
            marco, text="La clave se guarda solo en el archivo .env de este equipo y se envía únicamente al proveedor que elijas. "
                        "Se aplica a las mascotas que invoques después de guardar.",
            font=theme.FONT_CAPTION, text_color=theme.TEXT_FAINT, anchor="w", justify="left", wraplength=380,
        ).pack(anchor="w", pady=(18, 0))
        self._al_cambiar_proveedor(self.var_proveedor.get())

    def _proveedor(self):
        return self._nombre_a_clave[self.var_proveedor.get()]

    def _clave_guardada(self, proveedor=None):
        return os.getenv(ia.PROVEEDORES[proveedor or self._proveedor()][1], "")

    def _al_cambiar_proveedor(self, _valor=None):
        guardada = self._clave_guardada()
        self.lbl_guardada.configure(
            text=f"Clave guardada: {env_store.enmascarar(guardada)}" if guardada else "Todavía no hay una clave guardada para este proveedor",
            text_color=theme.SUCCESS if guardada else theme.TEXT_FAINT)
        self.entry_clave.delete(0, "end")
        self.entry_clave.configure(placeholder_text="Escribe una clave nueva para reemplazarla" if guardada else "Pega aquí tu clave")
        self.lbl_resultado.configure(text="")

    def _abrir_pagina(self):
        webbrowser.open(ia.PROVEEDORES[self._proveedor()][2])

    def _probar(self):
        proveedor = self._proveedor()
        clave = self.entry_clave.get().strip().strip("'\"") or self._clave_guardada(proveedor)
        if not clave:
            self.lbl_resultado.configure(text="Escribe o pega una clave primero.", text_color=theme.DANGER)
            return
        self.btn_probar.configure(state="disabled", text="Probando...")
        self.lbl_resultado.configure(text="", text_color=theme.TEXT_DIM)

        def trabajo():
            ok, mensaje = ia.probar_clave(proveedor, clave)
            try:
                self.win.after(0, lambda: self._mostrar_resultado(ok, mensaje))
            except Exception:
                pass

        threading.Thread(target=trabajo, daemon=True).start()

    def _mostrar_resultado(self, ok, mensaje):
        self.btn_probar.configure(state="normal", text="Probar conexión")
        self.lbl_resultado.configure(text=("✓  " if ok else "✕  ") + mensaje, text_color=theme.SUCCESS if ok else theme.DANGER)

    # ---------- comunes ----------
    def _crear_switch(self, parent, titulo, subtitulo, variable):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=6)
        text_col = ctk.CTkFrame(row, fg_color="transparent")
        text_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(text_col, text=titulo, font=theme.FONT_BODY_MEDIUM, text_color=theme.TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(text_col, text=subtitulo, font=theme.FONT_CAPTION, text_color=theme.TEXT_FAINT, anchor="w").pack(anchor="w")
        ctk.CTkSwitch(
            row, text="", variable=variable, onvalue=True, offvalue=False,
            progress_color=theme.ACCENT_DEFAULT, button_color=theme.TEXT, button_hover_color=theme.TEXT,
        ).pack(side="right")

    def _crear_slider(self, parent, titulo, variable, minimo, maximo, pasos=None):
        ctk.CTkLabel(parent, text=titulo, font=theme.FONT_BODY_MEDIUM, text_color=theme.TEXT, anchor="w").pack(anchor="w", pady=(4, 8))
        ctk.CTkSlider(
            parent, from_=minimo, to=maximo, variable=variable,
            progress_color=theme.ACCENT_DEFAULT, button_color=theme.TEXT, button_hover_color=theme.TEXT,
            fg_color=theme.BORDER, height=16, number_of_steps=pasos,
        ).pack(fill="x", pady=(0, 16))

    def guardar(self):
        self.settings["monitoreo_ia"] = self.var_monitoreo.get()
        self.settings["particulas"] = self.var_particulas.get()
        self.settings["sonido"] = self.var_sonido.get()
        self.settings["habilidad_auto"] = self.var_hab_auto.get()
        self.settings["transparencia"] = self.var_transparencia.get()
        self.settings["velocidad"] = self.var_velocidad.get()
        self.settings["pomodoro_trabajo"] = int(round(self.var_trabajo.get()))
        self.settings["pomodoro_descanso"] = int(round(self.var_descanso.get()))
        settings_manager.guardar(self.settings)

        proveedor = self._proveedor()
        env_store.guardar_proveedor(proveedor)
        env_store.guardar_clave(ia.PROVEEDORES[proveedor][1], self.entry_clave.get())
        self.win.destroy()
