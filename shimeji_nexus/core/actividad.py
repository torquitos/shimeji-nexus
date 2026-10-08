"""Que esta haciendo el usuario: ventana activa y tiempo sin tocar teclado ni mouse."""
import ctypes

import pygetwindow as gw


class _UltimaEntrada(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]


def segundos_inactivo():
    try:
        info = _UltimaEntrada()
        info.cbSize = ctypes.sizeof(_UltimaEntrada)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info))
        return ((ctypes.windll.kernel32.GetTickCount() - info.dwTime) & 0xFFFFFFFF) / 1000.0
    except Exception:
        return 0.0


def titulo_ventana_activa():
    try:
        ventana = gw.getActiveWindow()
        return ventana.title if ventana else ""
    except Exception:
        return ""
