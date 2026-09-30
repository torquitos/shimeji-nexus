import math
import os
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


def asegurar_sonidos():
    if not os.path.exists(SOUNDS_DIR):
        os.makedirs(SOUNDS_DIR, exist_ok=True)
    for nombre, frecuencias in SOUNDS.items():
        ruta = os.path.join(SOUNDS_DIR, f"{nombre}.wav")
        if not os.path.exists(ruta):
            _generar_wav(frecuencias, ruta)


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
