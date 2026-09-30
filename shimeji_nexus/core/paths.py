import os
import sys


def base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # paths.py vive en <root>/shimeji_nexus/core/paths.py -> subir 3 niveles a <root>
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
