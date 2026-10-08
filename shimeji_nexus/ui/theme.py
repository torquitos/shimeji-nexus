"""Tema visual centralizado del launcher: paleta, tipografia y espaciado."""

# ---- Paleta base ----
BG = "#0b0b0f"
PANEL = "#101016"
CARD = "#171720"
CARD_HOVER = "#1d1d28"
BORDER = "#26262f"
BORDER_SOFT = "#1e1e27"
TEXT = "#eeeef2"
TEXT_SOFT = "#b8b8c6"
TEXT_DIM = "#a0a0b0"
TEXT_FAINT = "#5c5c6b"
SUCCESS = "#4caf7d"

# Superficies y cromo de las ventanas de la app (Ajustes, Nuevo personaje). El color del personaje
# solo vive en la portada; el resto usa este acento de marca.
SURFACE = "#14141b"
SURFACE_SELECTED = "#1a1a24"
FIELD = "#0d0d12"
DIVIDER = "#1c1c25"
TRACK = "#23232e"
ACCENT_BRAND = "#7c8cff"
DANGER = "#e0546e"

# Acento por defecto para personajes sin color_globo/color_texto propio
ACCENT_DEFAULT = "#5b9bd9"
ACCENT_SOFT_DEFAULT = "#5b9bd922"

# Paleta rotativa: colores oscuros/saturados (formato "color_texto" de config.json)
# asignados en orden a personajes nuevos que no eligen color propio.
PALETA_ROTATIVA_COLOR_TEXTO = [
    "#0D47A1",  # azul (Gojo)
    "#8B0000",  # rojo (Rias)
    "#E65100",  # naranja (Naruto)
    "#4A148C",  # violeta
    "#1B5E20",  # verde
    "#B71C1C",  # carmesí
    "#00695C",  # teal
    "#4E342E",  # marrón cálido
]


def siguiente_color_rotativo(cantidad_existente):
    """Devuelve el color_texto que le toca al (cantidad_existente + 1)-esimo personaje."""
    return PALETA_ROTATIVA_COLOR_TEXTO[cantidad_existente % len(PALETA_ROTATIVA_COLOR_TEXTO)]

# ---- Tipografia (Segoe UI, ya nativa de Windows) ----
FONT_FAMILY = "Segoe UI"
FONT_FAMILY_SEMIBOLD = "Segoe UI Semibold"

FONT_TITLE = (FONT_FAMILY_SEMIBOLD, 28)
FONT_DISPLAY = (FONT_FAMILY_SEMIBOLD, 22)
FONT_HEADING = (FONT_FAMILY_SEMIBOLD, 14)
FONT_BODY = (FONT_FAMILY, 12)
FONT_BODY_LARGE = (FONT_FAMILY, 13)
FONT_BODY_MEDIUM = (FONT_FAMILY, 12, "bold")
FONT_BUTTON = (FONT_FAMILY_SEMIBOLD, 16)
FONT_CAPTION = (FONT_FAMILY, 11)
FONT_SECTION = (FONT_FAMILY_SEMIBOLD, 13)
FONT_ROW = (FONT_FAMILY_SEMIBOLD, 12)
FONT_CAPTION_BOLD = (FONT_FAMILY, 10, "bold")

# Fuente pixel propia de la app (titulos). Si no se puede registrar, se usa Segoe UI.
ACCENT_2 = "#ffcf5c"


def _registrar_fuente_pixel():
    import ctypes
    import os
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "fuentes", "PixelifySans.ttf")
    try:
        if os.path.exists(ruta) and ctypes.windll.gdi32.AddFontResourceExW(ruta, 0x10, 0):
            return "Pixelify Sans"
    except Exception:
        pass
    return FONT_FAMILY_SEMIBOLD


FONT_PIXEL_FAMILY = _registrar_fuente_pixel()
FONT_PIXEL_TITLE = (FONT_PIXEL_FAMILY, 26)
FONT_PIXEL = (FONT_PIXEL_FAMILY, 18)
FONT_PIXEL_SMALL = (FONT_PIXEL_FAMILY, 15)

# ---- Espaciado ----
SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16
SPACE_XL = 24


def blend_color(color_hex, fondo_hex, porcentaje):
    """Mezcla color_hex sobre fondo_hex al porcentaje dado (0.0-1.0)."""
    c = color_hex.lstrip("#")
    f = fondo_hex.lstrip("#")
    cr, cg, cb = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    fr, fg, fb = int(f[0:2], 16), int(f[2:4], 16), int(f[4:6], 16)
    r = round(cr * porcentaje + fr * (1 - porcentaje))
    g = round(cg * porcentaje + fg * (1 - porcentaje))
    b = round(cb * porcentaje + fb * (1 - porcentaje))
    return f"#{r:02x}{g:02x}{b:02x}"


def acento_desde_color_texto(color_texto):
    """`color_texto` en config.json esta pensado para texto sobre fondo claro, por lo
    que suele ser oscuro. Conservamos su tono y lo llevamos a un acento vivo para dark UI."""
    import colorsys
    c = color_texto.lstrip("#")
    r, g, b = (int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, _, _ = colorsys.rgb_to_hsv(r, g, b)
    r, g, b = colorsys.hsv_to_rgb(h, 0.62, 0.92)
    return f"#{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}"
