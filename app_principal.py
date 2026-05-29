import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import subprocess
import json

# Truco para indicarle a Windows que agrupe este programa de forma independiente a Python
try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ShimejiNexus.MultiAgentHub.v2")
except:
    pass

class LauncherPremiumAnime:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SHIMEJI NEXUS - MULTI-AGENT HUB")
        self.root.geometry("720x520")
        self.root.configure(bg="#0A0A0C")
        self.root.resizable(False, False)

        # Crear y aplicar icono invisible automáticamente
        try:
            from PIL import Image
            img_invisible = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
            ruta_icono = "temp_invisible.ico"
            img_invisible.save(ruta_icono, format="ICO")
            self.root.iconbitmap(ruta_icono)
        except Exception as e:
            print("Error creando icono:", e)



        # ---- PANEL IZQUIERDO ----
        self.panel_izq = tk.Frame(self.root, bg="#16161D", width=250)
        self.panel_izq.pack(side="left", fill="y", padx=15, pady=15)
        self.panel_izq.pack_propagate(False)

        lbl_lista = tk.Label(
            self.panel_izq, text="⚡ SHIMEJI NEXUS ACTIVE", 
            fg="#FF3366", bg="#16161D", font=("Segoe UI", 11, "bold")
        )

        lbl_lista.pack(pady=15)

        self.box = tk.Listbox(
            self.panel_izq, bg="#1E1E24", fg="#E1E1E6", 
            font=("Segoe UI", 11), bd=0, highlightthickness=1,
            highlightbackground="#29292E", highlightcolor="#FF3366",
            selectbackground="#FF3366", selectforeground="white"
        )
        self.box.pack(fill="both", expand=True, padx=10, pady=5)
        self.box.bind("<<ListboxSelect>>", self.cambiar_seleccion_personaje)

        # ---- PANEL DERECHO ----
        self.panel_der = tk.Frame(self.root, bg="#0F0F12")
        self.panel_der.pack(side="right", fill="both", expand=True, padx=15, pady=15)

        self.lbl_nombre_personaje = tk.Label(
            self.panel_der, text="Selecciona un Personaje", 
            fg="white", bg="#0F0F12", font=("Segoe UI", 16, "bold")
        )
        self.lbl_nombre_personaje.pack(pady=10)

        self.canvas_preview = tk.Canvas(self.panel_der, width=150, height=150, bg="#16161D", bd=0, highlightthickness=1, highlightbackground="#FF3366")
        self.canvas_preview.pack(pady=10)

        self.lbl_desc = tk.Label(
            self.panel_der, text="Toca un personaje de la lista de la izquierda para ver sus detalles de Inteligencia Artificial.",
            fg="#8C8C9A", bg="#0F0F12", font=("Segoe UI", 9), wraplength=350, justify="center"
        )
        self.lbl_desc.pack(pady=10)

        # ---- SECCIÓN DE BOTONES ----
        self.frame_botones = tk.Frame(self.panel_der, bg="#0F0F12")
        self.frame_botones.pack(side="bottom", fill="x", pady=15)

        self.btn_invocar = tk.Button(
            self.frame_botones, text="🚀 INVOCAR EN PANTALLA", bg="#FF3366", fg="white",
            font=("Segoe UI", 11, "bold"), activebackground="#E62E5C", activeforeground="white",
            bd=0, cursor="hand2", command=self.lanzar, state="disabled"
        )
        self.btn_invocar.pack(fill="x", pady=5, ipady=8)

        self.btn_limpiar = tk.Button(
            self.frame_botones, text="🧹 LIMPIAR PANTALLA (CERRAR MASCOTAS)", bg="#29292E", fg="#FF3366",
            font=("Segoe UI", 10, "bold"), activebackground="#1E1E24", activeforeground="white",
            bd=0, cursor="hand2", command=self.matar_procesos
        )
        self.btn_limpiar.pack(fill="x", pady=5, ipady=5)

        self.personajes_datos = {}
        self.escanear_personajes()
        self.root.mainloop()

    def escanear_personajes(self):
        self.box.delete(0, tk.END)
        ruta = "personajes"
        if not os.path.exists(ruta):
            os.makedirs(ruta)
        
        for carpeta in os.listdir(ruta):
            conf = os.path.join(ruta, carpeta, "config.json")
            if os.path.isdir(os.path.join(ruta, carpeta)) and os.path.exists(conf):
                with open(conf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    display_name = f" ❤️  {data['nombre']}"
                    self.box.insert(tk.END, display_name)
                    self.personajes_datos[display_name] = {
                        "folder": carpeta,
                        "nombre": data['nombre'],
                        "personalidad": data['personalidad'],
                        "img_path": os.path.join(ruta, carpeta, "rias.png")
                    }

    def cambiar_seleccion_personaje(self, event):
        seleccion = self.box.curselection()
        if not seleccion: return
        
        item = self.box.get(seleccion)
        info = self.personajes_datos[item]

        self.lbl_nombre_personaje.config(text=info["nombre"])
        self.lbl_desc.config(text=info["personalidad"])
        self.btn_invocar.config(state="normal")

        if os.path.exists(info["img_path"]):
            try:
                img = Image.open(info["img_path"]).convert("RGBA")
                datas = img.getdata()
                newData = []
                for p in datas:
                    if p[0] > 240 and p[1] > 240 and p[2] > 240:
                        newData.append((0, 0, 0, 0))
                    else:
                        newData.append(p)
                img.putdata(newData)
                img = img.resize((120, 120), Image.Resampling.NEAREST)
                
                self.img_tk = ImageTk.PhotoImage(img)
                self.canvas_preview.delete("all")
                self.canvas_preview.create_image(75, 75, image=self.img_tk)
            except Exception as e:
                print(e)

    def lanzar(self):
        seleccion = self.box.curselection()
        if not seleccion: return
        
        item = self.box.get(seleccion)
        folder = self.personajes_datos[item]["folder"]
        ruta_envio = f"personajes/{folder}"

        comando = f'python -c "from mascota_motor import MascotaLogica; MascotaLogica(\'{ruta_envio}\')"'
        subprocess.Popen(comando, shell=True)

    def matar_procesos(self):
        try:
            import os
            # Cierra de forma agresiva cualquier proceso de python que tenga abierto el motor de la mascota
            os.system('wmic process where "commandline like \'%mascota_motor%\'" delete')
            messagebox.showinfo("Limpieza", "¡Pantalla limpia! Mascotas removidas de la memoria con éxito.")
        except Exception as e:
            print(e)



if __name__ == "__main__":
    LauncherPremiumAnime()
