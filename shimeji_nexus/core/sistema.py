"""Cosas de Windows: arrancar con el sistema, detectar pantalla completa y medir el consumo."""
import ctypes
import os
import sys
from ctypes import wintypes

from shimeji_nexus.core.paths import base_dir

CLAVE_RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"
NOMBRE_RUN = "ShimejiNexus"
IGNORAR = ("Progman", "WorkerW", "Shell_TrayWnd")


def _comando_inicio():
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    exe = pythonw if os.path.exists(pythonw) else sys.executable
    return f'"{exe}" "{os.path.join(base_dir(), "app_principal.py")}"'


def inicio_activo():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLAVE_RUN) as k:
            winreg.QueryValueEx(k, NOMBRE_RUN)
            return True
    except OSError:
        return False


def poner_inicio(activar):
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLAVE_RUN, 0, winreg.KEY_SET_VALUE) as k:
        if activar:
            winreg.SetValueEx(k, NOMBRE_RUN, 0, winreg.REG_SZ, _comando_inicio())
        else:
            try:
                winreg.DeleteValue(k, NOMBRE_RUN)
            except OSError:
                pass


class _InfoMonitor(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT), ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]


def pantalla_completa_activa():
    """True si la ventana en primer plano cubre entera su pantalla (juego, video a pantalla completa)."""
    try:
        u = ctypes.windll.user32
        hwnd = u.GetForegroundWindow()
        if not hwnd:
            return False
        clase = ctypes.create_unicode_buffer(64)
        u.GetClassNameW(hwnd, clase, 64)
        if clase.value in IGNORAR:
            return False
        if u.GetWindowLongW(hwnd, -16) & 0xC00000 == 0xC00000:
            return False  # tiene barra de titulo: una ventana maximizada, no pantalla completa
        r = wintypes.RECT()
        u.GetWindowRect(hwnd, ctypes.byref(r))
        info = _InfoMonitor()
        info.cbSize = ctypes.sizeof(info)
        u.GetMonitorInfoW(u.MonitorFromWindow(hwnd, 2), ctypes.byref(info))
        m = info.rcMonitor
        return r.left <= m.left and r.top <= m.top and r.right >= m.right and r.bottom >= m.bottom
    except Exception:
        return False


def atajo_pulsado():
    """Ctrl + Mayús + N, aunque la app no tenga el foco."""
    gks = ctypes.windll.user32.GetAsyncKeyState
    return all(gks(vk) & 0x8000 for vk in (0x11, 0x10, 0x4E))


def consumo(proceso=None):
    """(MB de RAM, % de CPU) de esta app y de todas las mascotas que lanzó."""
    import psutil
    proceso = proceso or psutil.Process()
    todos = [proceso] + proceso.children(recursive=True)
    ram = sum(p.memory_info().rss for p in todos if p.is_running()) / 1048576
    cpu = sum(p.cpu_percent(None) for p in todos if p.is_running()) / (psutil.cpu_count() or 1)
    return ram, cpu
