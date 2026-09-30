import customtkinter as ctk

from shimeji_nexus.core import settings as settings_manager
from shimeji_nexus.ui import theme


class SettingsWindow:
    def __init__(self, parent):
        self.parent = parent
        self.win = ctk.CTkToplevel(parent)
        self.win.title("Configuración")
        self.win.geometry("420x480")
        self.win.configure(fg_color=theme.BG)
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        self.settings = settings_manager.cargar()

        main_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=28, pady=26)

        ctk.CTkLabel(main_frame, text="Configuración general", font=theme.FONT_DISPLAY, text_color=theme.TEXT).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(main_frame, text="Ajusta el comportamiento de tus mascotas", font=theme.FONT_CAPTION, text_color=theme.TEXT_FAINT).pack(anchor="w", pady=(0, 20))

        self.var_monitoreo = ctk.BooleanVar(value=self.settings.get("monitoreo_ia", True))
        self._crear_switch(main_frame, "Monitoreo de ventana activa", "Comenta la ventana activa cada 30s con IA", self.var_monitoreo)

        self.var_particulas = ctk.BooleanVar(value=self.settings.get("particulas", True))
        self._crear_switch(main_frame, "Efectos de partículas", "Aura mágica y estelas al interactuar", self.var_particulas)

        self.var_sonido = ctk.BooleanVar(value=self.settings.get("sonido", True))
        self._crear_switch(main_frame, "Sonidos de la aplicación", "Efectos de sonido al invocar y cerrar", self.var_sonido)

        ctk.CTkFrame(main_frame, fg_color=theme.BORDER, height=1).pack(fill="x", pady=(8, 20))

        self.var_transparencia = ctk.DoubleVar(value=self.settings.get("transparencia", 1.0))
        self._crear_slider(main_frame, "Transparencia de mascotas", self.var_transparencia, 0.3, 1.0)

        self.var_velocidad = ctk.DoubleVar(value=self.settings.get("velocidad", 1.0))
        self._crear_slider(main_frame, "Velocidad de animación", self.var_velocidad, 0.2, 3.0)

        ctk.CTkButton(
            main_frame, text="Guardar configuración", command=self.guardar,
            fg_color=theme.ACCENT_DEFAULT, hover_color=theme.blend_color("#ffffff", theme.ACCENT_DEFAULT, 0.15), text_color=theme.BG,
            font=theme.FONT_BODY_MEDIUM, corner_radius=12, height=42,
        ).pack(fill="x", pady=(24, 0))

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

    def _crear_slider(self, parent, titulo, variable, minimo, maximo):
        ctk.CTkLabel(parent, text=titulo, font=theme.FONT_BODY_MEDIUM, text_color=theme.TEXT, anchor="w").pack(anchor="w", pady=(4, 8))
        ctk.CTkSlider(
            parent, from_=minimo, to=maximo, variable=variable,
            progress_color=theme.ACCENT_DEFAULT, button_color=theme.TEXT, button_hover_color=theme.TEXT,
            fg_color=theme.BORDER, height=16,
        ).pack(fill="x", pady=(0, 16))

    def guardar(self):
        self.settings["monitoreo_ia"] = self.var_monitoreo.get()
        self.settings["particulas"] = self.var_particulas.get()
        self.settings["sonido"] = self.var_sonido.get()
        self.settings["transparencia"] = self.var_transparencia.get()
        self.settings["velocidad"] = self.var_velocidad.get()
        settings_manager.guardar(self.settings)
        self.win.destroy()
