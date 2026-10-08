"""Constantes y carga de la habilidad de un personaje."""
from shimeji_nexus.ui.theme import acento_desde_color_texto, blend_color

FORMAS = ("orbitar", "brasas", "espiral", "rayo")

# Linea de tiempo de una habilidad, en ticks de 35 ms (76 ticks = 2.7 s)
CARGA, DISPARO, IMPACTO, TOTAL = 28, 22, 22, 76


def cargar_habilidad(config):
    """Habilidad del personaje (config.json -> 'habilidad'). Si falta, un efecto generico
    con el color de acento del personaje."""
    h = dict(config.get("habilidad") or {})
    color = config.get("color_texto")
    acento = acento_desde_color_texto(color) if color else "#5b9bd9"
    h.setdefault("nombre", "Aura mágica")
    h.setdefault("descripcion", "Una técnica de energía propia de este personaje.")
    h.setdefault("forma", "brasas")
    h.setdefault("colores", [acento, blend_color("#ffffff", acento, 0.5), blend_color("#000000", acento, 0.6)])
    if h["forma"] not in FORMAS:
        h["forma"] = "brasas"
    return h
