import os
import threading
import webbrowser

import customtkinter as ctk

from shimeji_nexus.ai import client as ia
from shimeji_nexus.core import env_store
from shimeji_nexus.ui import theme
from shimeji_nexus.ui.ajustes.componentes import boton_primario, boton_secundario, campo, selector, seccion


class IAPanel:
    """Pagina de Inteligencia artificial: proveedor, clave de API y prueba de conexion."""

    def __init__(self, parent, win):
        self.win = win
        self._nombre_a_clave = {datos[0]: clave for clave, datos in ia.PROVEEDORES.items()}
        actual = os.getenv("AI_PROVIDER", "gemini").strip().lower()
        if actual not in ia.PROVEEDORES:
            actual = "gemini"
        self.var_proveedor = ctk.StringVar(value=ia.PROVEEDORES[actual][0])
        card = seccion(parent, "Proveedor", "Elige quién responde.")
        selector(card, self._nombre_a_clave, self.var_proveedor, self._al_cambiar_proveedor).pack(fill="x", padx=16, pady=(14, 10))
        self.lbl_guardada = ctk.CTkLabel(card, text="", font=theme.FONT_CAPTION, anchor="w", corner_radius=6, padx=8, pady=2)
        self.lbl_guardada.pack(anchor="w", padx=16, pady=(0, 14))
        self._construir_clave(seccion(parent, "Clave de API"))
        ctk.CTkLabel(parent, text="Tu clave se queda en este equipo y solo se envía al proveedor que elijas. "
                                  "Se aplica a las mascotas que invoques después de guardar.",
                     font=theme.FONT_CAPTION, text_color=theme.TEXT_DIM, anchor="w", justify="left", wraplength=470).pack(anchor="w", pady=(12, 8))
        self._al_cambiar_proveedor()

    def _construir_clave(self, card):
        fila = ctk.CTkFrame(card, fg_color="transparent")
        fila.pack(fill="x", padx=16, pady=(16, 10))
        self.entry_clave = campo(fila, show="•")
        self.entry_clave.pack(side="left", fill="x", expand=True)
        self.btn_ver = ctk.CTkButton(fila, text="Mostrar", width=76, height=36, corner_radius=8, fg_color=theme.SURFACE_SELECTED, hover_color=theme.TRACK,
                                     text_color=theme.TEXT_SOFT, font=theme.FONT_ROW, command=self._alternar_ver)
        self.btn_ver.pack(side="left", padx=(8, 0))
        botones = ctk.CTkFrame(card, fg_color="transparent")
        botones.pack(fill="x", padx=16)
        self.btn_probar = boton_primario(botones, "Probar conexión", self._probar, 150)
        self.btn_probar.pack(side="left")
        boton_secundario(botones, "Conseguir clave", self._abrir_pagina, 140).pack(side="left", padx=(8, 0))
        self.lbl_resultado = ctk.CTkLabel(card, text="", font=theme.FONT_BODY, anchor="w", justify="left", wraplength=440)
        self.lbl_resultado.pack(anchor="w", padx=16, pady=(10, 16))

    def _alternar_ver(self):
        oculta = self.entry_clave.cget("show") != ""
        self.entry_clave.configure(show="" if oculta else "•")
        self.btn_ver.configure(text="Ocultar" if oculta else "Mostrar")

    def _proveedor(self):
        return self._nombre_a_clave[self.var_proveedor.get()]

    def _clave_guardada(self, proveedor=None):
        return os.getenv(ia.PROVEEDORES[proveedor or self._proveedor()][1], "")

    def _al_cambiar_proveedor(self, _valor=None):
        guardada = self._clave_guardada()
        if guardada:
            self.lbl_guardada.configure(text=f"Clave guardada ({env_store.enmascarar(guardada)})", text_color=theme.SUCCESS, fg_color="#12261c")
        else:
            self.lbl_guardada.configure(text="Sin clave guardada", text_color=theme.TEXT_DIM, fg_color=theme.SURFACE_SELECTED)
        self.entry_clave.delete(0, "end")
        self.entry_clave.configure(placeholder_text="Pega una clave nueva para reemplazar la actual" if guardada else "Pega aquí tu clave de API")
        self.lbl_resultado.configure(text="")

    def _abrir_pagina(self):
        webbrowser.open(ia.PROVEEDORES[self._proveedor()][2])

    def _probar(self):
        proveedor = self._proveedor()
        clave = self.entry_clave.get().strip().strip("'\"") or self._clave_guardada(proveedor)
        if not clave:
            self.lbl_resultado.configure(text="Escribe o pega una clave primero.", text_color=theme.DANGER)
            return
        self.btn_probar.configure(state="disabled", text="Probando…")
        self.lbl_resultado.configure(text="", text_color=theme.TEXT_DIM)

        def trabajo():
            ok, mensaje = ia.probar_clave(proveedor, clave)
            try:
                self.win.after(0, lambda: self._mostrar_resultado(ok, mensaje))
            except Exception:
                pass

        threading.Thread(target=trabajo, daemon=True).start()

    def _mostrar_resultado(self, ok, mensaje):
        self.btn_probar.configure(state="normal", text="Probar conexión")
        self.lbl_resultado.configure(text=("✓  " if ok else "✕  ") + mensaje, text_color=theme.SUCCESS if ok else theme.DANGER)

    def guardar(self):
        proveedor = self._proveedor()
        env_store.guardar_proveedor(proveedor)
        env_store.guardar_clave(ia.PROVEEDORES[proveedor][1], self.entry_clave.get())
