def contorno_redondeado(x1, y1, x2, y2, r):
    """Puntos de un rectangulo de esquinas redondas para tk.Canvas.create_polygon(..., smooth=True)."""
    return [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
