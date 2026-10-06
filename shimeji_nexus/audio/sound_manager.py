import math
import os
import random
import struct
import threading
import wave

from shimeji_nexus.core.paths import base_dir

SOUNDS_DIR = os.path.join(base_dir(), "assets", "sounds")

SOUNDS = {
    "invoke": (523, 659, 784, 1047),
    "close": (784, 659, 523),
    "magic": (1047, 1319, 1568),
    "chat": (880, 1109),
    "error": (220, 165),
}


def _generar_wav(frecuencias, ruta, duracion_nota=0.12, sample_rate=44100):
    muestras = []
    for freq in frecuencias:
        frames = int(sample_rate * duracion_nota)
        for i in range(frames):
            t = i / sample_rate
            valor = int(16000 * math.sin(2 * math.pi * freq * t))
            muestras.append(valor)
    with wave.open(ruta, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(muestras)}h", *muestras))


FORMAS_HABILIDAD = ("orbitar", "brasas", "espiral")


def _generar_habilidad(forma, ruta, sr=22050):
    """Un segundo de carga que sube y un impacto. El timbre cambia segun la forma de la habilidad."""
    rnd = random.Random(7)
    carga, total = int(sr * 1.0), int(sr * 2.6)
    m = [0.0] * total
    fase = 0.0
    env = 0.0
    lp = 0.0
    for i in range(carga):
        t = i / carga
        if forma == "orbitar":
            fase += 2 * math.pi * (180 + 760 * t ** 1.6) / sr
            m[i] = (0.35 + 0.4 * t) * (math.sin(fase) + 0.4 * math.sin(2.01 * fase))
        elif forma == "brasas":
            if rnd.random() < 0.02 + 0.25 * t:
                env = rnd.uniform(0.5, 1.0)
            env *= 0.85
            m[i] = env * (rnd.random() * 2 - 1) + 0.35 * t * math.sin(2 * math.pi * 55 * i / sr)
        else:
            fase += 2 * math.pi * (260 + 600 * t) * (1 + 0.06 * math.sin(2 * math.pi * 14 * i / sr)) / sr
            m[i] = (0.35 + 0.45 * t) * math.sin(fase)
    for j in range(total - carga):
        t = j / sr
        ruido = rnd.random() * 2 - 1
        if forma == "orbitar":
            m[carga + j] = (0.9 * math.sin(2 * math.pi * (70 - 25 * min(t, 1)) * t) * math.exp(-3.0 * t)
                            + 0.5 * ruido * math.exp(-9 * t) + 0.25 * math.sin(2 * math.pi * 1320 * t) * math.exp(-2.2 * t))
        elif forma == "brasas":
            lp += 0.08 * (ruido - lp)
            m[carga + j] = 2.2 * lp * math.exp(-2.0 * t) + 0.9 * math.sin(2 * math.pi * 55 * t) * math.exp(-3.0 * t)
        else:
            m[carga + j] = (0.8 * math.sin(2 * math.pi * (140 - 80 * min(t, 1)) * t) * math.exp(-4.0 * t)
                            + 0.7 * ruido * math.exp(-6 * t) + 0.2 * math.sin(2 * math.pi * 900 * t) * math.exp(-3.0 * t))
    pico = max(abs(v) for v in m) or 1.0
    datos = [int(v / pico * 0.8 * 32767) for v in m]
    with wave.open(ruta, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(struct.pack(f"<{len(datos)}h", *datos))


def asegurar_sonidos():
    if not os.path.exists(SOUNDS_DIR):
        os.makedirs(SOUNDS_DIR, exist_ok=True)
    for nombre, frecuencias in SOUNDS.items():
        ruta = os.path.join(SOUNDS_DIR, f"{nombre}.wav")
        if not os.path.exists(ruta):
            _generar_wav(frecuencias, ruta)
    for forma in FORMAS_HABILIDAD:
        ruta = os.path.join(SOUNDS_DIR, f"hab_{forma}.wav")
        if not os.path.exists(ruta):
            _generar_habilidad(forma, ruta)


def reproducir(nombre):
    ruta = os.path.join(SOUNDS_DIR, f"{nombre}.wav")
    if not os.path.exists(ruta):
        return
    threading.Thread(target=_reproducir_audio, args=(ruta,), daemon=True).start()


def _reproducir_audio(ruta):
    try:
        import pygame
        pygame.mixer.init()
        s = pygame.mixer.Sound(ruta)
        s.play()
    except Exception:
        pass
