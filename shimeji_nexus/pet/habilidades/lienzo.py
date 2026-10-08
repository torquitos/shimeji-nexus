import ctypes
import tkinter as tk


class Lienzo:
    """Ventana transparente mas grande que la mascota, por la que los clics pasan de largo,
    donde se dibujan los efectos grandes (proyectiles, ondas, el letrero)."""

    W, H = 1000, 600

    def __init__(self, master):
        self.win = tk.Toplevel(master)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.wm_attributes("-transparentcolor", "black")
        self.win.configure(bg="black")
        self.canvas = tk.Canvas(self.win, width=self.W, height=self.H, bg="black", bd=0, highlightthickness=0)
        self.canvas.pack()
        self.win.withdraw()
        self.visible = False
        self._clics_listos = False

    def _pasar_clics(self):
        try:
            self.win.update_idletasks()
            user32 = ctypes.windll.user32
            hwnd = user32.GetParent(self.win.winfo_id()) or self.win.winfo_id()
            user32.SetWindowLongW(hwnd, -20, user32.GetWindowLongW(hwnd, -20) | 0x80000 | 0x20)
        except Exception:
            pass

    def mostrar(self, cx, cy):
        self.win.geometry(f"{self.W}x{self.H}+{int(cx - self.W / 2)}+{int(cy - self.H / 2)}")
        if not self.visible:
            self.win.deiconify()
            self.win.lift()
            self.visible = True
            if not self._clics_listos:
                self._pasar_clics()
                self._clics_listos = True

    def ocultar(self):
        self.canvas.delete("fx")
        if self.visible:
            self.win.withdraw()
            self.visible = False
