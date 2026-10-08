"""Reacciones de las mascotas a lo que haces, por reglas (sin IA, al instante y gratis).
`evaluar` decide, a partir de la ventana activa y la inactividad, que categoria de frase toca decir."""
import json
import os
import time

REGLAS = (
    ("reac_juego", ("steam", "epic games", "minecraft", "roblox", "valorant", "league of legends", "fortnite", "genshin", "battle.net")),
    ("reac_codigo", ("visual studio", "pycharm", "intellij", "sublime", "powershell", "cmd.exe", "símbolo del sistema", "terminal", "github", "stack overflow", "claude code")),
    ("reac_video", ("youtube", "netflix", "twitch", "crunchyroll", "disney+", "prime video", "vlc", "animeflv")),
    ("reac_musica", ("spotify", "soundcloud", "deezer", "youtube music")),
    ("reac_chat", ("whatsapp", "discord", "telegram", "slack", "messenger", "teams")),
    ("reac_redes", ("twitter", " / x", "facebook", "instagram", "tiktok", "reddit", "pinterest")),
    ("reac_doc", ("word", "docs", "notion", "excel", "sheets", "powerpoint", "slides", ".pdf", "obsidian")),
)

ENTRE_CATEGORIA = 150   # segundos antes de repetir una misma categoria
ENTRE_FRASES = 45       # silencio minimo entre dos reacciones de esta mascota
ENTRE_MASCOTAS = 25     # si otra mascota acaba de reaccionar, esta se calla
INACTIVO = 300          # 5 min sin tocar nada: se aburre
DESCANSO = 5400         # 90 min seguidos de actividad: sugiere una pausa


def categoria_de(titulo):
    t = (titulo or "").lower()
    for categoria, claves in REGLAS:
        if any(k in t for k in claves):
            return categoria
    return None


class Reacciones:
    def __init__(self, carpeta_compartida):
        self.archivo = os.path.join(carpeta_compartida, "reaccion.json")
        self.reaccionada = None       # categoria de ventana a la que ya reaccione y en la que sigue el usuario
        self.ult_por_categoria = {}
        self.ult_frase = 0.0
        self.ausente = False
        self.activo_desde = time.time()
        self.avisos = set()

    def _reservar(self, ahora):
        """Solo una mascota reacciona a la vez: la primera en llegar se queda con el turno."""
        try:
            with open(self.archivo, encoding="utf-8") as f:
                if ahora - json.load(f).get("t", 0) < ENTRE_MASCOTAS:
                    return False
        except (OSError, ValueError):
            pass
        try:
            with open(self.archivo + ".tmp", "w", encoding="utf-8") as f:
                json.dump({"t": ahora}, f)
            os.replace(self.archivo + ".tmp", self.archivo)
        except OSError:
            pass
        return True

    def _candidata(self, titulo, inactivo, ahora, hora):
        """(categoria, prioritaria) que tocaria decir, sin dar nada por dicho todavia."""
        if inactivo >= INACTIVO:
            return ("idle", True) if not self.ausente else (None, False)
        if self.ausente:
            return "vuelve", True
        if inactivo > 120:
            self.activo_desde = ahora
        if ahora - self.activo_desde >= DESCANSO and "descanso" not in self.avisos:
            return "descanso", False
        if 0 <= hora < 5 and "tarde" not in self.avisos:
            return "tarde", False
        actual = categoria_de(titulo)
        if actual and self.reaccionada is None and ahora - self.ult_por_categoria.get(actual, 0) >= ENTRE_CATEGORIA:
            return actual, False
        return None, False

    def _confirmar(self, categoria, titulo, ahora):
        if categoria == "idle":
            self.ausente = True
        elif categoria == "vuelve":
            self.ausente, self.activo_desde = False, ahora
            self.avisos.discard("descanso")
        elif categoria in ("descanso", "tarde"):
            self.avisos.add(categoria)
        else:
            self.reaccionada = categoria
            self.ult_por_categoria[categoria] = ahora

    def evaluar(self, titulo, inactivo, ahora=None, hora=None):
        """Categoria de frase a decir ahora ('reac_video', 'idle', 'vuelve'...) o None."""
        ahora = time.time() if ahora is None else ahora
        hora = time.localtime(ahora).tm_hour if hora is None else hora
        if categoria_de(titulo) != self.reaccionada:
            self.reaccionada = None   # se fue de la categoria a la que ya habia reaccionado
        categoria, prioritaria = self._candidata(titulo, inactivo, ahora, hora)
        if categoria and (prioritaria or ahora - self.ult_frase >= ENTRE_FRASES) and self._reservar(ahora):
            self.ult_frase = ahora
            self._confirmar(categoria, titulo, ahora)
            return categoria
        return None
