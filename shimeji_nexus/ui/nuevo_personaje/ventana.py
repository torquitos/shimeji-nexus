import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk

from shimeji_nexus.core import creador, prompt_hoja
from shimeji_nexus.ui import theme
from shimeji_nexus.ui.ajustes.componentes import ACENTO, boton_primario, boton_secundario, campo, encabezado, seccion, selector
from shimeji_nexus.ui.nuevo_personaje.vista_previa import VistaPrevia
from shimeji_nexus.ui.theme import acento_desde_color_texto

MODOS = ("Una imagen", "Hoja de sprites")
IMAGENES = [("Imágenes", "*.png *.jpg *.jpeg")]
SUGERENCIA = "Cuéntalo como si se lo explicaras a un amigo: es tímida, siempre tiene hambre y te regaña si trabajas tarde…"


class AddCharacterWindow:
    """Nuevo personaje en tres pasos, con la vista previa del resultado a la derecha."""

    def __init__(self, parent, launcher):
        self.launcher = launcher
        self.win = ctk.CTkToplevel(parent)
        self.win.title("Nuevo personaje")
        self.win.geometry("860x720")
        self.win.configure(fg_color=theme.BG)
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()
        self.var_imagen, self.var_hoja, self.var_retrato = ctk.StringVar(), ctk.StringVar(), ctk.StringVar()
        self.vista = VistaPrevia(self.win, acento_desde_color_texto(creador.siguiente_color()))
        self.vista.pack(side="right", fill="y")
        self._pie()
        self.form = ctk.CTkScrollableFrame(self.win, fg_color="transparent", scrollbar_button_color=theme.BG, scrollbar_button_hover_color=theme.DIVIDER)
        self.form.pack(side="top", fill="both", expand=True, padx=(32, 12), pady=(32, 0))
        encabezado(self.form, "Nuevo personaje", "Ponle nombre y una imagen. Lo demás se puede cambiar después.")
        self._quien(seccion(self.form, "1. ¿Quién es?"))
        self._imagenes(seccion(self.form, "2. Su imagen"))
        self._habla(seccion(self.form, "3. Cómo habla"))
        self._refrescar()

    # ---------- piezas ----------
    def _etiqueta(self, card, texto):
        ctk.CTkLabel(card, text=texto, font=theme.FONT_CAPTION, text_color=theme.TEXT_DIM, anchor="w").pack(anchor="w", padx=16, pady=(14, 4))

    def _campo(self, card, titulo, ejemplo):
        self._etiqueta(card, titulo)
        entrada = campo(card, placeholder_text=ejemplo)
        entrada.pack(fill="x", padx=16)
        entrada.bind("<KeyRelease>", lambda e: self._refrescar())
        return entrada

    def _quien(self, card):
        self.entry_nombre = self._campo(card, "Nombre", "Ej. Zero Two")
        self.entry_serie = self._campo(card, "Serie o anime (opcional)", "Ej. Darling in the Franxx")
        ctk.CTkFrame(card, fg_color="transparent", height=16).pack()

    def _imagenes(self, card):
        self.modo = ctk.StringVar(value=MODOS[0])
        selector(card, MODOS, self.modo, lambda _v: self._cambiar_modo()).pack(fill="x", padx=16, pady=(16, 0))
        self.panel_imagen = ctk.CTkFrame(card, fg_color="transparent")
        self._selector(self.panel_imagen, "Imagen del personaje", "PNG con fondo liso o transparente.", self.var_imagen)
        self.panel_hoja = ctk.CTkFrame(card, fg_color="transparent")
        self._selector(self.panel_hoja, "Hoja de sprites", "8 columnas × 3 filas, fondo verde.", self.var_hoja)
        self._selector(self.panel_hoja, "Retrato en alta resolución (opcional)", "Se usa en la portada y en el chat.", self.var_retrato)
        boton_secundario(self.panel_hoja, "Copiar prompt para generar la hoja", self._copiar_prompt, 260).pack(anchor="w", padx=16, pady=(16, 4))
        self.lbl_copiado = ctk.CTkLabel(self.panel_hoja, text="Pégalo en ChatGPT o Gemini, genera la imagen y súbela aquí.", font=theme.FONT_CAPTION,
                                        text_color=theme.TEXT_DIM, anchor="w", justify="left", wraplength=440)
        self.lbl_copiado.pack(anchor="w", padx=16, pady=(0, 6))
        self._cambiar_modo()

    def _selector(self, parent, titulo, ayuda, variable):
        self._etiqueta(parent, titulo)
        fila = ctk.CTkFrame(parent, fg_color="transparent")
        fila.pack(fill="x", padx=16)
        entrada = campo(fila, textvariable=variable, placeholder_text="Ninguna elegida")
        entrada.configure(state="readonly")
        entrada.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(fila, text="Elegir…", width=90, height=36, corner_radius=8, fg_color=theme.SURFACE_SELECTED, hover_color=theme.TRACK,
                      text_color=theme.TEXT_SOFT, font=theme.FONT_ROW, command=lambda: self._elegir(variable)).pack(side="left", padx=(8, 0))
        ctk.CTkLabel(parent, text=ayuda, font=theme.FONT_CAPTION, text_color=theme.TEXT_DIM, anchor="w").pack(anchor="w", padx=16, pady=(4, 0))

    def _habla(self, card):
        self.text_pers = ctk.CTkTextbox(card, height=92, fg_color=theme.FIELD, border_color=theme.DIVIDER, border_width=1, text_color=theme.TEXT,
                                        corner_radius=8, font=theme.FONT_BODY, wrap="word")
        self.text_pers.pack(fill="x", padx=16, pady=16)
        self._sugerencia = True
        self.text_pers.insert("1.0", SUGERENCIA)
        self.text_pers.configure(text_color=theme.TEXT_FAINT)
        interno = self.text_pers._textbox
        interno.bind("<FocusIn>", self._entrar_texto, add="+")
        interno.bind("<FocusOut>", self._salir_texto, add="+")

    def _entrar_texto(self, _e):
        self.text_pers.configure(border_color=ACENTO)
        if self._sugerencia:
            self.text_pers.delete("1.0", "end")
            self.text_pers.configure(text_color=theme.TEXT)
            self._sugerencia = False

    def _salir_texto(self, _e):
        self.text_pers.configure(border_color=theme.DIVIDER)
        if not self.text_pers.get("1.0", "end-1c").strip():
            self.text_pers.insert("1.0", SUGERENCIA)
            self.text_pers.configure(text_color=theme.TEXT_FAINT)
            self._sugerencia = True

    def _pie(self):
        pie = ctk.CTkFrame(self.win, fg_color="transparent")
        pie.pack(side="bottom", fill="x", padx=(32, 12), pady=(10, 28))
        self.btn_crear = boton_primario(pie, "Crear personaje", self.crear, 160)
        self.btn_crear.pack(side="right")
        boton_secundario(pie, "Cancelar", self.win.destroy, 100).pack(side="right", padx=(0, 8))

    # ---------- comportamiento ----------
    def _es_hoja(self):
        return self.modo.get() == MODOS[1]

    def _cambiar_modo(self):
        self.panel_imagen.pack_forget()
        self.panel_hoja.pack_forget()
        (self.panel_hoja if self._es_hoja() else self.panel_imagen).pack(fill="x", pady=(0, 16))
        self._refrescar()

    def _elegir(self, variable):
        ruta = filedialog.askopenfilename(title="Elegir imagen", filetypes=IMAGENES, parent=self.win)
        if ruta:
            variable.set(ruta)
            self._refrescar()

    def _pendiente(self):
        if not self.entry_nombre.get().strip():
            return "Ponle un nombre"
        if not (self.var_hoja.get() if self._es_hoja() else self.var_imagen.get()):
            return "Falta la imagen"
        return None

    def _refrescar(self):
        hoja = self._es_hoja()
        ruta = (self.var_retrato.get() or self.var_hoja.get()) if hoja else self.var_imagen.get()
        pendiente = self._pendiente()
        self.vista.actualizar(self.entry_nombre.get(), self.entry_serie.get(), hoja and not self.var_retrato.get(), ruta, pendiente)
        if pendiente:
            self.btn_crear.configure(fg_color=theme.SURFACE_SELECTED, hover_color=theme.SURFACE_SELECTED, text_color=theme.TEXT_FAINT)
        else:
            self.btn_crear.configure(fg_color=ACENTO, hover_color=theme.blend_color("#ffffff", ACENTO, 0.14), text_color=theme.BG)

    def _copiar_prompt(self):
        nombre = self.entry_nombre.get().strip() or "[nombre del personaje]"
        self.win.clipboard_clear()
        self.win.clipboard_append(prompt_hoja.generar(nombre, self.entry_serie.get().strip()))
        self.lbl_copiado.configure(text="Prompt copiado. Ya puedes pegarlo en ChatGPT o Gemini.", text_color=theme.SUCCESS)

    def crear(self):
        pendiente = self._pendiente()
        if pendiente:
            return messagebox.showinfo("Falta algo", pendiente + ".", parent=self.win)
        texto = "" if self._sugerencia else self.text_pers.get("1.0", "end-1c")
        datos = dict(nombre=self.entry_nombre.get(), serie=self.entry_serie.get().strip(), texto=texto)
        if self._es_hoja():
            datos.update(hoja=self.var_hoja.get(), retrato=self.var_retrato.get())
        else:
            datos.update(imagen=self.var_imagen.get())
        self.btn_crear.configure(state="disabled", text="Creando…")
        threading.Thread(target=self._trabajo, args=(datos,), daemon=True).start()

    def _trabajo(self, datos):
        try:
            creador.crear(**datos)
            resultado = None
        except creador.ErrorCreacion as e:
            resultado = str(e)
        self.win.after(0, lambda: self._terminar(datos["nombre"], resultado))

    def _terminar(self, nombre, error):
        self.btn_crear.configure(state="normal", text="Crear personaje")
        if error == "FALTAN_DEPENDENCIAS":
            return self._ofrecer_instalar()
        if error:
            return messagebox.showwarning("No se pudo crear", error, parent=self.win)
        messagebox.showinfo("Listo", f"{nombre.strip()} ya está en tu lista.", parent=self.win)
        self.launcher.escanear_personajes()
        self.win.destroy()

    def _ofrecer_instalar(self):
        if not messagebox.askyesno("Falta un componente", "Para procesar la hoja de sprites se necesitan 'numpy' y 'scipy' (solo para esta función).\n\n¿Instalarlos ahora?", parent=self.win):
            return
        self.btn_crear.configure(state="disabled", text="Instalando componentes…")

        def instalar():
            ok, msg = creador.instalar_dependencias()
            self.win.after(0, lambda: self._tras_instalar(ok, msg))

        threading.Thread(target=instalar, daemon=True).start()

    def _tras_instalar(self, ok, msg):
        self.btn_crear.configure(state="normal", text="Crear personaje")
        if ok:
            messagebox.showinfo("Listo", "Componentes instalados. Pulsa 'Crear personaje' otra vez.", parent=self.win)
        else:
            messagebox.showwarning("No se pudo instalar", msg, parent=self.win)
