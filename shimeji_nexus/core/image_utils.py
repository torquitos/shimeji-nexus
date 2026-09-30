from PIL import Image


def cargar_con_transparencia(ruta_img, size):
    """Abre una imagen, la redimensiona y vuelve transparente el fondo blanco."""
    img = Image.open(ruta_img).convert("RGBA")
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    data = img.getdata()
    new_data = []
    for p in data:
        if p[0] > 240 and p[1] > 240 and p[2] > 240:
            new_data.append((0, 0, 0, 0))
        else:
            new_data.append(p)
    img.putdata(new_data)
    return img
