import os
import sys

from dotenv import load_dotenv

from shimeji_nexus.core.paths import base_dir


def main():
    load_dotenv(dotenv_path=os.path.join(base_dir(), ".env"))

    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ShimejiNexus.MultiAgentHub.v3")
    except Exception:
        pass

    if len(sys.argv) > 1 and sys.argv[1] == "--mascota":
        import json
        import tkinter as tk

        from shimeji_nexus.audio import sound_manager
        from shimeji_nexus.pet.pet import MascotaLogica

        sound_manager.asegurar_sonidos()
        ruta = sys.argv[2] if len(sys.argv) > 2 else None
        pos = None
        if len(sys.argv) > 3 and sys.argv[3]:
            try:
                parts = sys.argv[3].split(",")
                pos = (int(parts[0]), int(parts[1]))
            except Exception:
                pos = None
        extra = {}
        if len(sys.argv) > 4 and sys.argv[4]:
            try:
                parts = sys.argv[4].split(",")
                extra = {"monitoreo_ia": parts[0] == "true", "particulas": parts[1] == "true"}
            except Exception:
                extra = {}
        if ruta:
            if not os.path.isdir(ruta):
                print(f"ERROR: Ruta no valida: {ruta}")
                sys.exit(1)
            try:
                MascotaLogica(ruta, pos, extra)
            except Exception as e:
                import traceback
                traceback.print_exc()
                try:
                    root = tk.Tk()
                    root.withdraw()
                    root.title("Error")
                    tk.messagebox.showerror("Error Mascota", f"Error al cargar personaje:\n{e}")
                    root.destroy()
                except Exception:
                    pass
                sys.exit(1)
    else:
        from shimeji_nexus.ui.launcher import LauncherPremiumAnime
        LauncherPremiumAnime()


if __name__ == "__main__":
    main()
