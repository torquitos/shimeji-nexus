"""Prompt para pedirle a una IA de imagenes (ChatGPT, Gemini...) la hoja de sprites de un personaje,
en el formato exacto que espera herramientas/preparar_sprites.py."""


def generar(nombre, serie="", descripcion=""):
    de = f" de {serie}" if serie else ""
    aspecto = f" Aspecto fiel al personaje: {descripcion.strip()}." if descripcion.strip() else ""
    return (
        f"Crea UNA sola imagen: una hoja de sprites en pixel art de {nombre}{de}, para usarla como mascota de escritorio.{aspecto}\n\n"
        "FORMATO (muy importante):\n"
        "- Imagen de 1376x768 px con una cuadricula de 8 columnas x 3 filas (cada celda de 172x256 px).\n"
        "- Fondo plano de un solo color verde puro #00FF00, sin degradados, sin sombras en el suelo y sin cuadricula visible.\n"
        "- En cada celda el personaje completo, de cuerpo entero, sin cortarse ni tocar los bordes de la celda. "
        "Mismo tamano y los pies en la misma linea en todas las celdas.\n"
        "- Estilo chibi pixel art de 32 bits, contorno oscuro, colores fieles al personaje. "
        "No uses el color verde ni el negro puro en el personaje.\n\n"
        "CONTENIDO:\n"
        "- Fila 1 (8 celdas): ciclo de caminar de PERFIL mirando a la derecha. 8 poses distintas y consecutivas "
        "(contacto, bajada, paso, subida...), cada una con las piernas y brazos en una posicion diferente.\n"
        "- Fila 2, celdas 1 a 4: de pie, quieto, de frente, con una leve respiracion entre una y otra.\n"
        "- Fila 2, celdas 5 a 8: saludando con la mano, de frente.\n"
        "- Fila 3, celdas 1 a 5: lanzando su tecnica o poder mas famoso, en 5 pasos: preparacion, carga, disparo, "
        "extension y final. Todo el efecto debe quedar DENTRO de su celda.\n\n"
        "Entregame solo la imagen, sin texto ni marcos."
    )
