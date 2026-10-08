"""Piezas comunes de las ventanas de la app: secciones planas, filas, campos y botones.
El acento es siempre el de la marca; el color de cada personaje no se usa aqui."""
import customtkinter as ctk

from shimeji_nexus.ui import theme

ACENTO = theme.ACCENT_BRAND


def encabezado(parent, titulo, ayuda=None):
    ctk.CTkLabel(parent, text=titulo, font=theme.FONT_PIXEL_TITLE, text_color=theme.TEXT).pack(anchor="w")
    if ayuda:
        ctk.CTkLabel(parent, text=ayuda, font=theme.FONT_BODY, text_color=theme.TEXT_DIM, anchor="w", justify="left", wraplength=470).pack(anchor="w", pady=(2, 0))


def seccion(parent, titulo, ayuda=None):
    """Titulo de seccion y, debajo, una superficie plana que agrupa sus filas."""
    ctk.CTkLabel(parent, text=titulo, font=theme.FONT_PIXEL_SMALL, text_color=theme.ACCENT_2, anchor="w").pack(fill="x", pady=(24, 2 if ayuda else 8))
    if ayuda:
        ctk.CTkLabel(parent, text=ayuda, font=theme.FONT_CAPTION, text_color=theme.TEXT_DIM, anchor="w", justify="left", wraplength=470).pack(fill="x", pady=(0, 8))
    marco = ctk.CTkFrame(parent, fg_color=theme.SURFACE, corner_radius=12)
    marco.pack(fill="x")
    return marco


def separador(card):
    ctk.CTkFrame(card, fg_color=theme.DIVIDER, height=1).pack(fill="x", padx=16)


def _fila(card, alto=52):
    fila = ctk.CTkFrame(card, fg_color="transparent", height=alto)
    fila.pack(fill="x", padx=16, pady=6)
    return fila


def _textos(parent, titulo, ayuda):
    columna = ctk.CTkFrame(parent, fg_color="transparent")
    columna.pack(side="left", fill="x", expand=True)
    ctk.CTkLabel(columna, text=titulo, font=theme.FONT_ROW, text_color=theme.TEXT, anchor="w").pack(anchor="w")
    if ayuda:
        ctk.CTkLabel(columna, text=ayuda, font=theme.FONT_CAPTION, text_color=theme.TEXT_DIM, anchor="w", justify="left", wraplength=360).pack(anchor="w")
    return columna


def fila_switch(card, titulo, ayuda, variable):
    fila = _fila(card)
    _textos(fila, titulo, ayuda)
    ctk.CTkSwitch(fila, text="", variable=variable, onvalue=True, offvalue=False, width=44, progress_color=ACENTO,
                  button_color=theme.TEXT, button_hover_color=theme.TEXT, fg_color=theme.TRACK).pack(side="right")


def fila_slider(card, titulo, variable, minimo, maximo, formato, pasos=None):
    """Titulo, valor actual a la derecha y el deslizador debajo."""
    fila = _fila(card, 56)
    cabecera = ctk.CTkFrame(fila, fg_color="transparent")
    cabecera.pack(fill="x")
    ctk.CTkLabel(cabecera, text=titulo, font=theme.FONT_ROW, text_color=theme.TEXT, anchor="w").pack(side="left")
    valor = ctk.CTkLabel(cabecera, text=formato(variable.get()), font=theme.FONT_ROW, text_color=theme.TEXT)
    valor.pack(side="right")
    variable.trace_add("write", lambda *_: valor.configure(text=formato(variable.get())))
    ctk.CTkSlider(fila, from_=minimo, to=maximo, variable=variable, number_of_steps=pasos, height=14, progress_color=ACENTO,
                  button_color=theme.TEXT, button_hover_color=theme.TEXT, fg_color=theme.TRACK).pack(fill="x", pady=(8, 4))


def fila_comando(card, comando, texto):
    fila = _fila(card, 36)
    chip = ctk.CTkLabel(fila, text=comando, font=("Consolas", 12), text_color=theme.TEXT, fg_color=theme.SURFACE_SELECTED, corner_radius=6, padx=8, pady=2)
    chip.pack(side="left")
    ctk.CTkLabel(fila, text=texto, font=theme.FONT_CAPTION, text_color=theme.TEXT_DIM, anchor="w").pack(side="left", padx=(12, 0))


def fila_atajo(card, titulo, ayuda, teclas):
    fila = _fila(card)
    _textos(fila, titulo, ayuda)
    for i, tecla in enumerate(reversed(teclas)):
        if i:
            ctk.CTkLabel(fila, text="+", font=theme.FONT_CAPTION, text_color=theme.TEXT_DIM).pack(side="right", padx=3)
        ctk.CTkLabel(fila, text=tecla, font=("Consolas", 12, "bold"), text_color=theme.TEXT, fg_color=theme.SURFACE_SELECTED,
                     corner_radius=5, padx=8, pady=3).pack(side="right")


class FilaConsumo:
    """RAM y CPU reales de la app y sus mascotas, con barras que se actualizan solas."""

    def __init__(self, card, ventana):
        from shimeji_nexus.core import sistema
        self.sistema, self.ventana = sistema, ventana
        fila = _fila(card, 50)
        self.etiquetas, self.barras = [], []
        for _ in range(2):
            col = ctk.CTkFrame(fila, fg_color="transparent")
            col.pack(side="left", fill="x", expand=True, padx=(0, 16))
            self.etiquetas.append(ctk.CTkLabel(col, text="", font=theme.FONT_ROW, text_color=theme.TEXT, anchor="w"))
            self.etiquetas[-1].pack(anchor="w")
            self.barras.append(ctk.CTkProgressBar(col, height=6, fg_color=theme.TRACK, progress_color=theme.SUCCESS))
            self.barras[-1].pack(fill="x", pady=(6, 0))
        self.sistema.consumo()
        ventana.after(1200, self._medir)

    def _medir(self):
        try:
            ram, cpu = self.sistema.consumo()
            self.etiquetas[0].configure(text=f"RAM · {ram:.0f} MB")
            self.etiquetas[1].configure(text=f"CPU · {cpu:.0f} %".replace(".", ","))
            self.barras[0].set(min(1, ram / 600))
            self.barras[1].set(min(1, cpu / 25))
            self.ventana.after(2000, self._medir)
        except Exception:
            pass


def campo(parent, **extra):
    """Campo de texto: sin borde visible en reposo; el borde de acento aparece al enfocarlo."""
    entrada = ctk.CTkEntry(parent, fg_color=theme.FIELD, border_color=theme.DIVIDER, border_width=1, text_color=theme.TEXT, corner_radius=8,
                           height=36, font=theme.FONT_BODY, placeholder_text_color=theme.TEXT_FAINT, **extra)
    interno = getattr(entrada, "_entry", entrada)
    interno.bind("<FocusIn>", lambda e: entrada.configure(border_color=ACENTO), add="+")
    interno.bind("<FocusOut>", lambda e: entrada.configure(border_color=theme.DIVIDER), add="+")
    return entrada


def boton_primario(parent, texto, comando, ancho=130):
    return ctk.CTkButton(parent, text=texto, command=comando, width=ancho, height=40, corner_radius=8, fg_color=ACENTO,
                         hover_color=theme.blend_color("#ffffff", ACENTO, 0.14), text_color=theme.BG, font=theme.FONT_ROW)


def boton_secundario(parent, texto, comando, ancho=100):
    return ctk.CTkButton(parent, text=texto, command=comando, width=ancho, height=40, corner_radius=8, fg_color=theme.SURFACE_SELECTED,
                         hover_color=theme.TRACK, text_color=theme.TEXT_SOFT, font=theme.FONT_ROW)


def selector(parent, valores, variable, comando=None):
    return ctk.CTkSegmentedButton(parent, values=list(valores), variable=variable, command=comando, height=32, corner_radius=8,
                                  selected_color=theme.TRACK, selected_hover_color=theme.TRACK, unselected_color=theme.FIELD,
                                  unselected_hover_color=theme.SURFACE_SELECTED, fg_color=theme.FIELD, text_color=theme.TEXT, font=theme.FONT_ROW)
