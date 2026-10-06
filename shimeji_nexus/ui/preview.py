from PIL import Image, ImageDraw, ImageFilter, ImageFont

from shimeji_nexus.ui import theme

_FUENTES = ("C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf")


def _fuente(px):
    for ruta in _FUENTES:
        try:
            return ImageFont.truetype(ruta, px)
        except OSError:
            continue
    return None


def _resplandor(ancho, alto, cx, cy, rx, ry, fuerza, curva=1.7):
    g = Image.radial_gradient("L").resize((rx * 2, ry * 2), Image.Resampling.BICUBIC)
    g = g.point(lambda v: int(255 * fuerza * ((255 - v) / 255) ** curva))
    mascara = Image.new("L", (ancho, alto), 0)
    mascara.paste(g, (cx - rx, cy - ry))
    return mascara


def _capa(ancho, alto, color):
    return Image.new("RGB", (ancho, alto), color)


def componer_hero(sprite, color_acento, ancho, alto, marca):
    """Portada del personaje: resplandor de su color, nombre como marca de agua,
    el sprite grande a la derecha con sombra, y oscurecido a la izquierda para el texto."""
    base = _capa(ancho, alto, theme.BG)
    cx, cy = int(ancho * 0.70), int(alto * 0.50)

    base = Image.composite(_capa(ancho, alto, color_acento), base,
                           _resplandor(ancho, alto, cx, cy, int(ancho * 0.62), int(alto * 0.58), 0.46))
    luz = theme.blend_color("#ffffff", color_acento, 0.35)
    base = Image.composite(_capa(ancho, alto, luz), base,
                           _resplandor(ancho, alto, cx, int(alto * 0.40), int(ancho * 0.22), int(alto * 0.30), 0.20, 2.0))

    fuente = _fuente(int(alto * 0.30))
    if fuente is not None and marca:
        capa = Image.new("L", (ancho, alto), 0)
        ImageDraw.Draw(capa).text((int(ancho * 0.99), int(alto * 0.985)), marca, font=fuente, fill=255, anchor="rb")
        base = Image.composite(_capa(ancho, alto, color_acento), base, capa.point(lambda v: int(v * 0.08)))

    vineta = Image.radial_gradient("L").resize((ancho, alto), Image.Resampling.BICUBIC)
    base = Image.composite(_capa(ancho, alto, (5, 5, 8)), base, vineta.point(lambda v: int(max(0, v - 140) / 115 * 170)))

    izquierda = Image.linear_gradient("L").rotate(90).resize((ancho, alto), Image.Resampling.BICUBIC)
    base = Image.composite(_capa(ancho, alto, theme.BG), base, izquierda.point(lambda v: int(max(0.0, 1 - v / 140) * 170)))

    if sprite is not None:
        x = cx - sprite.width // 2
        y = alto - sprite.height - 34
        sombra = Image.new("L", (ancho, alto), 0)
        rx, ry, cys = int(sprite.width * 0.45), 12, y + sprite.height - 4
        ImageDraw.Draw(sombra).ellipse((cx - rx, cys - ry, cx + rx, cys + ry), fill=190)
        sombra = sombra.filter(ImageFilter.GaussianBlur(9))
        base = Image.composite(_capa(ancho, alto, (4, 4, 8)), base, sombra)
        base.paste(sprite, (x, y), sprite)
    return base
