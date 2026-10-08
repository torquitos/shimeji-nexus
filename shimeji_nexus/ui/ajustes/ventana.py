import customtkinter as ctk

from shimeji_nexus.core import settings as settings_manager
from shimeji_nexus.ui import theme
from shimeji_nexus.ui.ajustes.componentes import (ACENTO, boton_primario, boton_secundario, encabezado, fila_comando, fila_slider,
                                                  fila_switch, seccion, separador)
from shimeji_nexus.ui.ajustes.ia_panel import IAPanel

PAGINAS = ("General", "Productividad", "Inteligencia artificial")
AYUDA = {"Inteligencia artificial": "Sin clave, las mascotas solo repiten frases hechas."}
COMANDOS = (("/pomodoro [min]", "Empieza un pomodoro. Sin minutos, usa los de Ajustes."),
            ("/parar", "Detiene el pomodoro."),
            ("/tiempo", "Cuánto falta para el siguiente cambio."),
            ("/recordar <min> <texto>", "Te avisa de algo en unos minutos."))


class SettingsWindow:
    """Ajustes con navegacion lateral. Sus colores son los de la marca, no los del personaje."""

    def __init__(self, parent):
        self.settings = settings_manager.cargar()
        self.win = ctk.CTkToplevel(parent)
        self.win.title("Ajustes")
        self.win.geometry("800x620")
        self.win.configure(fg_color=theme.BG)
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()
        self._botones, self._barras, self._paginas, self._construidas, self.ia = {}, {}, {}, set(), None
        self._crear_variables()
        self._barra_lateral()
        self._pie()
        self.contenido = ctk.CTkFrame(self.win, fg_color="transparent")
        self.contenido.pack(side="top", fill="both", expand=True, padx=(8, 32), pady=(32, 0))
        for nombre in PAGINAS:
            self._paginas[nombre] = self._crear_pagina(nombre)
        self._mostrar("General")

    def _barra_lateral(self):
        lado = ctk.CTkFrame(self.win, width=200, fg_color=theme.PANEL, corner_radius=0)
        lado.pack(side="left", fill="y")
        lado.pack_propagate(False)
        ctk.CTkLabel(lado, text="Ajustes", font=theme.FONT_SECTION, text_color=theme.TEXT).pack(anchor="w", padx=24, pady=(34, 18))
        for nombre in PAGINAS:
            fila = ctk.CTkFrame(lado, fg_color="transparent", height=36)
            fila.pack(fill="x", padx=(8, 12), pady=1)
            fila.pack_propagate(False)
            self._barras[nombre] = ctk.CTkFrame(fila, width=3, height=18, corner_radius=2, fg_color=theme.PANEL)
            self._barras[nombre].pack(side="left", padx=(0, 6))
            self._botones[nombre] = ctk.CTkButton(fila, text=nombre, anchor="w", corner_radius=8, font=theme.FONT_ROW, fg_color="transparent",
                                                  hover_color=theme.SURFACE, text_color=theme.TEXT_DIM, command=lambda n=nombre: self._mostrar(n))
            self._botones[nombre].pack(side="left", fill="both", expand=True)

    def _pie(self):
        pie = ctk.CTkFrame(self.win, fg_color="transparent")
        pie.pack(side="bottom", fill="x", padx=(8, 32), pady=(10, 28))
        boton_primario(pie, "Guardar", self.guardar, 110).pack(side="right")
        boton_secundario(pie, "Cancelar", self.win.destroy, 100).pack(side="right", padx=(0, 8))

    def _crear_pagina(self, nombre):
        pagina = ctk.CTkScrollableFrame(self.contenido, fg_color="transparent", scrollbar_button_color=theme.BG, scrollbar_button_hover_color=theme.DIVIDER)
        encabezado(pagina, nombre, AYUDA.get(nombre))
        return pagina

    def _construir(self, nombre):
        """Cada pagina se construye al abrirla por primera vez, asi la ventana abre al instante."""
        if nombre in self._construidas:
            return
        self._construidas.add(nombre)
        pagina = self._paginas[nombre]
        if nombre == "General":
            self._pagina_general(pagina)
        elif nombre == "Productividad":
            self._pagina_productividad(pagina)
        else:
            self.ia = IAPanel(pagina, self.win)

    def _mostrar(self, nombre):
        self._construir(nombre)
        for n, pagina in self._paginas.items():
            pagina.pack_forget()
            activo = n == nombre
            self._botones[n].configure(fg_color=theme.SURFACE_SELECTED if activo else "transparent", text_color=theme.TEXT if activo else theme.TEXT_DIM)
            self._barras[n].configure(fg_color=ACENTO if activo else theme.PANEL)
        self._paginas[nombre].pack(fill="both", expand=True, padx=(18, 0))

    def _crear_variables(self):
        s = self.settings
        self.var_hab_auto = ctk.BooleanVar(value=s.get("habilidad_auto", True))
        self.var_monitoreo = ctk.BooleanVar(value=s.get("monitoreo_ia", True))
        self.var_particulas = ctk.BooleanVar(value=s.get("particulas", True))
        self.var_sonido = ctk.BooleanVar(value=s.get("sonido", True))
        self.var_velocidad = ctk.DoubleVar(value=s.get("velocidad", 1.0))
        self.var_transparencia = ctk.DoubleVar(value=s.get("transparencia", 1.0))
        self.var_trabajo = ctk.DoubleVar(value=s.get("pomodoro_trabajo", 25))
        self.var_descanso = ctk.DoubleVar(value=s.get("pomodoro_descanso", 5))

    def _pagina_general(self, pagina):
        card = seccion(pagina, "Comportamiento")
        fila_switch(card, "Técnicas espontáneas", "De vez en cuando, tus mascotas sueltan su técnica sin avisar.", self.var_hab_auto)
        separador(card)
        fila_switch(card, "Opinar sobre lo que hago", "Cada 30 s miran tu ventana y comentan. Usa tu IA.", self.var_monitoreo)
        separador(card)
        fila_slider(card, "Velocidad", self.var_velocidad, 0.2, 3.0, lambda v: f"{v:.1f}×".replace(".", ","))
        card = seccion(pagina, "Apariencia")
        fila_switch(card, "Efectos", "Auras y destellos al usar técnicas.", self.var_particulas)
        separador(card)
        fila_switch(card, "Sonido", "Al invocar, cerrar y lanzar técnicas.", self.var_sonido)
        separador(card)
        fila_slider(card, "Opacidad", self.var_transparencia, 0.3, 1.0, lambda v: f"{round(v * 100)} %")

    def _pagina_productividad(self, pagina):
        card = seccion(pagina, "Pomodoro", "Las mascotas te avisan al terminar cada fase.")
        fila_slider(card, "Trabajo", self.var_trabajo, 5, 60, lambda v: f"{round(v)} min", 55)
        separador(card)
        fila_slider(card, "Descanso", self.var_descanso, 1, 30, lambda v: f"{round(v)} min", 29)
        card = seccion(pagina, "Comandos del chat")
        for i, (comando, texto) in enumerate(COMANDOS):
            if i:
                separador(card)
            fila_comando(card, comando, texto)

    def guardar(self):
        s = self.settings
        s.update(habilidad_auto=self.var_hab_auto.get(), monitoreo_ia=self.var_monitoreo.get(), particulas=self.var_particulas.get(),
                 sonido=self.var_sonido.get(), velocidad=self.var_velocidad.get(), transparencia=self.var_transparencia.get(),
                 pomodoro_trabajo=int(round(self.var_trabajo.get())), pomodoro_descanso=int(round(self.var_descanso.get())))
        settings_manager.guardar(s)
        if self.ia is not None:
            self.ia.guardar()
        self.win.destroy()
