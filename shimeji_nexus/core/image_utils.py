from PIL import Image, ImageChops, ImageDraw, ImageFilter

_MARCADOR = (255, 0, 255)


def _bbox_contenido(img_rgb, tolerancia=28):
    fondo = Image.new("RGB", img_rgb.size, img_rgb.getpixel((0, 0)))
    diff = ImageChops.difference(img_rgb, fondo).convert("L").point(lambda v: 255 if v > tolerancia else 0)
    return diff.getbbox()


def _recortar_contenido(img_rgb, margen=6):
    bbox = _bbox_contenido(img_rgb)
    if not bbox:
        return img_rgb
    x0, y0, x1, y1 = bbox
    return img_rgb.crop((max(0, x0 - margen), max(0, y0 - margen), min(img_rgb.width, x1 + margen), min(img_rgb.height, y1 + margen)))


def _rellenar_huecos_cerrados(rgb, fondo, tolerancia=6, minimo=60):
    """Huecos de fondo rodeados por el personaje (un mechon, entre el brazo y el torso).
    Tolerancia estricta y tamano minimo para no tocar brillos pequenos ni el pelo claro."""
    w, h = rgb.size
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            px = rgb.getpixel((x, y))
            if px == _MARCADOR or sum(abs(px[i] - fondo[i]) for i in range(3)) > tolerancia:
                continue
            prueba = rgb.copy()
            ImageDraw.floodfill(prueba, (x, y), _MARCADOR, thresh=tolerancia)
            cambiados = ImageChops.difference(prueba, rgb).convert("L").point(lambda v: 255 if v else 0)
            if cambiados.histogram()[255] >= minimo:
                rgb = prueba
    return rgb


def _quitar_fondo(img_rgb, tolerancia=70):
    """Hace transparente solo el fondo claro conectado a las esquinas, para no
    borrar el relleno claro del personaje (pelo, ropa blanca) que queda dentro del contorno."""
    rgb = img_rgb.copy()
    w, h = rgb.size
    fondo = img_rgb.getpixel((0, 0))
    perimetro = [(x, 0) for x in range(0, w, 3)] + [(x, h - 1) for x in range(0, w, 3)]
    perimetro += [(0, y) for y in range(0, h, 3)] + [(w - 1, y) for y in range(0, h, 3)]
    for semilla in perimetro:
        px = rgb.getpixel(semilla)
        if px == _MARCADOR or sum(abs(px[i] - fondo[i]) for i in range(3)) > tolerancia:
            continue
        ImageDraw.floodfill(rgb, semilla, _MARCADOR, thresh=tolerancia)
    rgb = _rellenar_huecos_cerrados(rgb, fondo)
    r, g, b = rgb.split()
    es_fondo = ImageChops.multiply(
        ImageChops.multiply(r.point(lambda v: 255 if v == 255 else 0), g.point(lambda v: 255 if v == 0 else 0)),
        b.point(lambda v: 255 if v == 255 else 0),
    )
    # Quita el borde de 1px claro que deja el reescalado entre el fondo y el contorno oscuro
    r0, g0, b0 = img_rgb.split()
    claro = ImageChops.darker(ImageChops.darker(r0, g0), b0).point(lambda v: 255 if v > 150 else 0)
    cerca_fondo = es_fondo.filter(ImageFilter.MaxFilter(3))
    es_fondo = ImageChops.lighter(es_fondo, ImageChops.multiply(cerca_fondo, claro))
    salida = img_rgb.convert("RGBA")
    salida.putalpha(ImageChops.invert(es_fondo))
    return salida


def cargar_sprite(ruta_img, alto):
    """Sprite recortado al contenido, de la altura pedida y con fondo transparente."""
    img = _recortar_contenido(Image.open(ruta_img).convert("RGB"))
    ancho = max(1, round(img.width * alto / img.height))
    img = img.resize((ancho, alto), Image.Resampling.BOX)
    return _quitar_fondo(img)


def cargar_avatar(ruta_img, size):
    """Cabeza y torso del personaje en un cuadrado, para miniaturas."""
    img = _recortar_contenido(Image.open(ruta_img).convert("RGB"))
    lado = min(img.width, img.height)
    x0 = (img.width - lado) // 2
    img = img.crop((x0, 0, x0 + lado, lado)).resize((size, size), Image.Resampling.BOX)
    return _quitar_fondo(img)
