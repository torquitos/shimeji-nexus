"""Convierte una hoja de sprites (8 columnas x 3 filas, fondo de un solo color) en frames sueltos
con fondo transparente, y los registra en el config.json del personaje.

Uso:  python herramientas/preparar_sprites.py <hoja.png> <carpeta_del_personaje> [--alto 176]

Filas esperadas: 1) caminar  2) quieto (4 frames) + saludo (4 frames)  3) habilidad (hasta 5 frames).
Necesita numpy y scipy (solo para esta herramienta; la app no los usa).
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageChops
from scipy import ndimage

COLUMNAS, FILAS, LADO = 8, 3, 200
SUELO = LADO - 8

ESTADOS = {
    "caminando": (0, range(0, 8), 8),
    "quieto": (1, range(0, 4), 3),
    "saludo": (1, range(4, 8), 6),
    "magia": (2, range(0, 5), 8),
}


def color_de_fondo(a):
    rosa = (a[..., 0] > 190) & (a[..., 2] > 190) & (a[..., 1] < 90)
    verde = (a[..., 1] > 190) & (a[..., 0] < 90) & (a[..., 2] < 90)
    candidatos = rosa if rosa.sum() >= verde.sum() else verde
    return np.median(a[candidatos], axis=0)


def recortar_celda(a, fondo, fila, col):
    ch, cw = a.shape[0] // FILAS, a.shape[1] // COLUMNAS
    y0, x0 = fila * ch, col * cw
    celda = a[y0 + 4:y0 + ch - 3, x0 + 5:x0 + cw - 5]
    dist = np.abs(celda - fondo).sum(axis=2)
    mascara = dist > 130
    # mata el tinte del color de fondo que queda mezclado en los bordes
    r, g, b = celda[..., 0], celda[..., 1], celda[..., 2]
    if fondo[1] < 100:
        mascara &= ~((r - g > 80) & (b - g > 80))
    else:
        mascara &= ~((g - r > 70) & (g - b > 70))
    etiquetas, n = ndimage.label(ndimage.binary_dilation(mascara, iterations=2))
    if n == 0:
        return None
    mayor = np.argmax(ndimage.sum(mascara, etiquetas, range(1, n + 1))) + 1
    caja = ndimage.find_objects(etiquetas)[mayor - 1]
    cy, cx = (caja[0].start + caja[0].stop) // 2, (caja[1].start + caja[1].stop) // 2
    cerca = np.zeros_like(mascara)
    for i, sl in enumerate(ndimage.find_objects(etiquetas), start=1):
        if i == mayor:
            cerca |= etiquetas == i
            continue
        sy, sx = (sl[0].start + sl[0].stop) // 2, (sl[1].start + sl[1].stop) // 2
        ancho_ok = (sl[1].stop - sl[1].start) < cw * 0.9 and (sl[0].stop - sl[0].start) < ch * 0.9
        # astilla de un efecto de la celda vecina: pequena y pegada al borde izquierdo o derecho
        toca_borde = sl[1].start == 0 or sl[1].stop >= celda.shape[1]
        if toca_borde and np.sum(mascara & (etiquetas == i)) < 0.2 * np.sum(mascara & (etiquetas == mayor)):
            continue
        if ancho_ok and abs(sy - cy) < ch * 0.5 and abs(sx - cx) < cw * 0.7:
            cerca |= etiquetas == i
    final = mascara & cerca
    rgba = np.dstack([celda.astype(np.uint8), (final * 255).astype(np.uint8)])
    return Image.fromarray(rgba, "RGBA")


def caja_visible(img):
    return img.getchannel("A").point(lambda v: 255 if v > 0 else 0).getbbox()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hoja")
    ap.add_argument("personaje")
    ap.add_argument("--alto", type=int, default=176, help="altura del personaje en el canvas de 200 px")
    ap.add_argument("--vel-caminar", type=float, default=4.0, help="pixeles por tick (35 ms) al caminar")
    args = ap.parse_args()

    a = np.array(Image.open(args.hoja).convert("RGB")).astype(float)
    fondo = color_de_fondo(a)
    print("color de fondo detectado:", tuple(int(v) for v in fondo))

    celdas = {}
    for estado, (fila, cols, _) in ESTADOS.items():
        for col in cols:
            img = recortar_celda(a, fondo, fila, col)
            if img is not None and caja_visible(img):
                celdas[(estado, col)] = img

    alturas = [caja_visible(celdas[("quieto", c)])[3] - caja_visible(celdas[("quieto", c)])[1] for c in range(4) if ("quieto", c) in celdas]
    escala = args.alto / float(np.median(alturas))
    print(f"escala unica: {escala:.3f} (altura de referencia {np.median(alturas):.0f}px)")

    salida = os.path.join(args.personaje, "anim")
    os.makedirs(salida, exist_ok=True)
    for viejo in os.listdir(salida):
        if viejo.endswith(".png"):
            os.remove(os.path.join(salida, viejo))
    config = {}
    for estado, (fila, cols, fps) in ESTADOS.items():
        frames = []
        for col in cols:
            img = celdas.get((estado, col))
            if img is None:
                continue
            x0, y0, x1, y1 = caja_visible(img)
            alto = y1 - y0
            cabeza = img.crop((x0, y0, x1, y0 + max(4, int(alto * 0.2)))).getchannel("A")
            hx0, _, hx1, _ = cabeza.getbbox()
            ancla_x = x0 + (hx0 + hx1) / 2
            nuevo = (max(1, round((x1 - x0) * escala)), max(1, round(alto * escala)))
            peq = img.crop((x0, y0, x1, y1)).resize(nuevo, Image.Resampling.NEAREST)
            datos = np.array(peq)
            datos[..., 3] = np.where(datos[..., 3] > 127, 255, 0)
            casi_negro = (datos[..., 3] > 0) & (datos[..., :3].astype(int).sum(axis=2) <= 24)
            datos[casi_negro, :3] = (12, 12, 16)  # el negro puro es el color transparente de la ventana
            peq = Image.fromarray(datos, "RGBA")
            lienzo = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
            px = int(round(LADO / 2 - (ancla_x - x0) * escala))
            lienzo.paste(peq, (px, SUELO - nuevo[1]), peq)
            frames.append(lienzo)
        if estado == "caminando" and len(frames) > 2:
            dif = ImageChops.difference(frames[0].convert("RGB"), frames[-1].convert("RGB")).convert("L")
            if np.asarray(dif).mean() < 8:
                frames.pop()
        archivos = []
        for i, f in enumerate(frames):
            nombre = f"{estado}_{i}.png"
            f.save(os.path.join(salida, nombre))
            archivos.append(f"anim/{nombre}")
        if archivos:
            config[estado] = {"frames": archivos, "fps": fps}
            if estado == "caminando":
                config[estado]["velocidad"] = args.vel_caminar
        print(f"{estado}: {len(archivos)} frames")

    ruta_cfg = os.path.join(args.personaje, "config.json")
    cfg = json.load(open(ruta_cfg, encoding="utf-8-sig"))
    cfg["animaciones"] = config
    json.dump(cfg, open(ruta_cfg, "w", encoding="utf-8"), indent=4, ensure_ascii=False)
    print("config.json actualizado")


if __name__ == "__main__":
    main()
