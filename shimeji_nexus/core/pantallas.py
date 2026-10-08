"""Monitores del escritorio en coordenadas del escritorio virtual:
el monitor secundario puede tener x o y negativas si esta a la izquierda o arriba del principal."""
import ctypes
import time
from collections import namedtuple
from ctypes import wintypes

Area = namedtuple("Area", "left top right bottom")

_cache = (0.0, [])


class _InfoMonitor(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT), ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]


def _enumerar():
    areas = []

    def al_encontrar(hmon, _dc, _rect, _datos):
        info = _InfoMonitor()
        info.cbSize = ctypes.sizeof(_InfoMonitor)
        if ctypes.windll.user32.GetMonitorInfoW(hmon, ctypes.byref(info)):
            w = info.rcMonitor
            areas.append(Area(w.left, w.top, w.right, w.bottom))
        return 1

    firma = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
    try:
        ctypes.windll.user32.EnumDisplayMonitors(None, None, firma(al_encontrar), 0)
    except Exception:
        pass
    if not areas:
        areas.append(Area(0, 0, ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1)))
    return areas


def monitores():
    """Areas de trabajo de todos los monitores (se refresca cada 2 s por si se conecta o quita uno)."""
    global _cache
    if time.time() - _cache[0] > 2:
        _cache = (time.time(), _enumerar())
    return _cache[1]


def area_en(x, y):
    """Area del monitor que contiene el punto; si cae entre monitores, la del mas cercano."""
    mejor, mejor_d = None, float("inf")
    for a in monitores():
        dx = max(a.left - x, 0, x - a.right)
        dy = max(a.top - y, 0, y - a.bottom)
        if dx * dx + dy * dy < mejor_d:
            mejor, mejor_d = a, dx * dx + dy * dy
    return mejor


def limites_x():
    """Borde izquierdo y derecho de todo el escritorio, para poder caminar de un monitor a otro."""
    areas = monitores()
    return min(a.left for a in areas), max(a.right for a in areas)
