import math

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

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


# Escenario de cristal donde flota el personaje (x0, y0, x1, y1) y su radio de esquina
ESCENARIO = (350, 34, 664, 586)
RADIO = 22


def posicion_sprite(sprite, ancho, alto):
    """Esquina superior izquierda donde va el sprite: centrado en el escenario, apoyado sobre su suelo."""
    x0, y0, x1, y1 = ESCENARIO
    return (x0 + x1) // 2 - sprite.width // 2, y1 - sprite.height - 36


def _mascara_redondeada(ancho, alto, caja, radio):
    k = 3
    m = Image.new("L", (ancho * k, alto * k), 0)
    ImageDraw.Draw(m).rounded_rectangle([v * k for v in caja], radius=radio * k, fill=255)
    return m.resize((ancho, alto), Image.Resampling.LANCZOS)


def _emblema_fondo(ancho, alto, caja, color):
    """Anillos y marcas concentricas muy tenues, centrados en el escenario."""
    k = 2
    x0, y0, x1, y1 = caja
    cx, cy = ((x0 + x1) / 2) * k, (y0 + (y1 - y0) * 0.46) * k
    capa = Image.new("L", (ancho * k, alto * k), 0)
    d = ImageDraw.Draw(capa)
    for r, w in ((128, 3), (100, 2), (72, 2)):
        d.ellipse((cx - r * k, cy - r * k, cx + r * k, cy + r * k), outline=255, width=w * k)
    for i in range(48):
        a = i * math.pi / 24
        r0, r1 = 128 * k, (146 if i % 4 == 0 else 138) * k
        d.line((cx + r0 * math.cos(a), cy + r0 * math.sin(a), cx + r1 * math.cos(a), cy + r1 * math.sin(a)), fill=255, width=2 * k)
    pts = [(cx + 100 * k * math.cos(-math.pi / 2 + i * 2 * math.pi / 3), cy + 100 * k * math.sin(-math.pi / 2 + i * 2 * math.pi / 3)) for i in range(3)]
    d.polygon(pts, outline=255, width=2 * k)
    return capa.resize((ancho, alto), Image.Resampling.LANCZOS).point(lambda v: int(v * 0.30))


def componer_hero(sprite, color_acento, ancho, alto, marca, con_sprite=True):
    """Portada del personaje: resplandor de su color, nombre como marca de agua,
    el sprite grande a la derecha con sombra, y oscurecido a la izquierda para el texto."""
    base = _capa(ancho, alto, theme.BG)
    cx, cy = (ESCENARIO[0] + ESCENARIO[2]) // 2, int(alto * 0.50)

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

    base = _escenario(base, color_acento, ancho, alto)

    if sprite is not None:
        x, y = posicion_sprite(sprite, ancho, alto)
        sombra = Image.new("L", (ancho, alto), 0)
        rx, ry, cys = int(sprite.width * 0.42), 11, y + sprite.height - 2
        ImageDraw.Draw(sombra).ellipse((cx - rx, cys - ry, cx + rx, cys + ry), fill=200)
        sombra = sombra.filter(ImageFilter.GaussianBlur(8))
        base = Image.composite(_capa(ancho, alto, (3, 3, 6)), base, sombra)
        aro = Image.new("L", (ancho, alto), 0)
        ImageDraw.Draw(aro).ellipse((cx - rx - 26, cys - ry - 4, cx + rx + 26, cys + ry + 8), outline=255, width=1)
        base = Image.composite(_capa(ancho, alto, color_acento), base, aro.point(lambda v: int(v * 0.22)))
        if con_sprite:
            base.paste(sprite, (x, y), sprite)
    return base


def _escenario(base, color, ancho, alto):
    """Panel de cristal: relleno claro tenue, emblema, luz superior y borde fino del color del personaje."""
    caja = ESCENARIO
    forma = _mascara_redondeada(ancho, alto, caja, RADIO)
    base = Image.composite(_capa(ancho, alto, "#ffffff"), base, forma.point(lambda v: int(v * 0.05)))
    cx = (caja[0] + caja[2]) // 2
    emb = ImageChops.multiply(_emblema_fondo(ancho, alto, caja, color), forma)
    base = Image.composite(_capa(ancho, alto, color), base, emb)
    luz = ImageChops.multiply(_resplandor(ancho, alto, cx, caja[1] + 40, 170, 150, 0.22, 1.5), forma)
    base = Image.composite(_capa(ancho, alto, theme.blend_color("#ffffff", color, 0.4)), base, luz)
    interior = _mascara_redondeada(ancho, alto, (caja[0] + 1, caja[1] + 1, caja[2] - 1, caja[3] - 1), RADIO - 1)
    borde = ImageChops.subtract(forma, interior)
    return Image.composite(_capa(ancho, alto, theme.blend_color(color, "#ffffff", 0.55)), base, borde.point(lambda v: int(v * 0.30)))
