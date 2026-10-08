"""Donde se abren las ventanas de la app cuando hay varios monitores: el launcher recuerda
su posicion y las ventanas hijas se centran sobre el."""
import ctypes
import os
import tkinter as tk

from shimeji_nexus.core import pantallas
from shimeji_nexus.core import settings as settings_manager
from shimeji_nexus.core.paths import base_dir


def _icono_vacio():
    """Icono transparente de 16 px: la barra de titulo queda limpia, sin logo."""
    from PIL import Image
    ruta = os.path.join(base_dir(), "cache", "vacio.ico")
    if not os.path.exists(ruta):
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        Image.new("RGBA", (16, 16), (0, 0, 0, 0)).save(ruta, sizes=[(16, 16)])
    return ruta


def _aplicar_marco(win):
    """Barra de titulo oscura y sin logo (la de Windows es clara y lleva el icono por defecto de customtkinter)."""
    try:
        win.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id()) or win.winfo_id()
        oscuro = ctypes.c_int(1)
        for atributo in (20, 19):
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, atributo, ctypes.byref(oscuro), ctypes.sizeof(oscuro))
        vacio = ctypes.windll.user32.LoadImageW(0, _icono_vacio(), 1, 16, 16, 0x10)
        ctypes.windll.user32.SendMessageW(hwnd, 0x80, 0, vacio)  # WM_SETICON, ICON_SMALL
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x37)  # repinta la barra con el tema nuevo
    except Exception:
        pass


def estilizar(win, ocultar=True):
    """Prepara una ventana: invisible mientras se construye (asi no se ve vacia ni blanca) y con la barra de titulo limpia.
    Al terminar de construirla hay que llamar a mostrar()."""
    if ocultar:
        win.attributes("-alpha", 0.0)  # invisible pero ya dibujandose, asi aparece completa y de golpe
    _aplicar_marco(win)
    win.after(260, lambda: _aplicar_marco(win))  # customtkinter pone su icono a los 200 ms


def mostrar(win, modal=False):
    win.update()
    win.after(90, lambda: (win.update(), win.attributes("-alpha", 1.0)))  # deja que customtkinter termine de dibujar antes de verla
    win.lift()
    if modal:
        win.grab_set()
    win.focus_force()


def geometria_launcher(ancho, alto):
    """'ANCHOxALTO' mas la posicion guardada, si su centro sigue cayendo dentro de algun monitor."""
    pos = settings_manager.cargar().get("ventana_launcher")
    if isinstance(pos, (list, tuple)) and len(pos) == 2:
        cx, cy = pos[0] + ancho / 2, pos[1] + alto / 2
        a = pantallas.area_en(cx, cy)
        if a.left <= cx <= a.right and a.top <= cy <= a.bottom:
            return f"{ancho}x{alto}+{pos[0]}+{pos[1]}"
    return f"{ancho}x{alto}"


def recordar_posicion(root):
    """Guarda la posicion de la ventana medio segundo despues de moverla."""
    pendiente = {"id": None}

    def guardar():
        pendiente["id"] = None
        try:
            if root.state() != "normal":
                return
            pos = [root.winfo_x(), root.winfo_y()]
        except tk.TclError:
            return
        ajustes = settings_manager.cargar()
        if ajustes.get("ventana_launcher") != pos:
            ajustes["ventana_launcher"] = pos
            settings_manager.guardar(ajustes)

    def al_mover(e):
        if e.widget is root:
            if pendiente["id"]:
                root.after_cancel(pendiente["id"])
            pendiente["id"] = root.after(500, guardar)

    root.bind("<Configure>", al_mover, add="+")


def centrar_sobre(win, parent, ancho, alto):
    """Abre `win` centrada sobre `parent`, sin salirse del monitor en que esta."""
    parent.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() - ancho) // 2
    y = parent.winfo_y() + (parent.winfo_height() - alto) // 2
    a = pantallas.area_en(x + ancho / 2, y + alto / 2)
    win.geometry(f"{ancho}x{alto}+{max(a.left, min(a.right - ancho, x))}+{max(a.top, min(a.bottom - alto, y))}")
