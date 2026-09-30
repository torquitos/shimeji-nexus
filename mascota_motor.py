import json
import sys

from shimeji_nexus.audio import sound_manager
from shimeji_nexus.pet.pet import MascotaLogica

if __name__ == "__main__":
    sound_manager.asegurar_sonidos()
    if len(sys.argv) > 1:
        ruta = sys.argv[1]
        pos = None
        extra = {}
        if len(sys.argv) > 2:
            try:
                pos = json.loads(sys.argv[2])
            except Exception:
                pos = None
        if len(sys.argv) > 3:
            try:
                extra = json.loads(sys.argv[3])
            except Exception:
                extra = {}
        MascotaLogica(ruta, pos_inicial=pos, args=extra)
    else:
        print("Uso: python mascota_motor.py <ruta_personaje> [pos_json] [args_json]")
