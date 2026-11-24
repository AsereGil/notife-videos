"""
Videos para NotiFE: descarga un video de YouTube o Facebook (o usa uno de la computadora)
y arma un resumen con segmentos al azar.

Para abrir la ventana: doble clic en iniciar.bat  (o:  python app.py)
"""

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import video

CARPETA_INICIAL = Path.home() / "Downloads" / "YouTube"


class Ventana(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Videos para NotiFE")
        self.minsize(620, 600)
        self.mensajes = queue.Queue()
        self.ultima_carpeta = None

        self.enlace = tk.StringVar()
        self.archivo = tk.StringVar()
        self.carpeta = tk.StringVar(value=str(CARPETA_INICIAL))
        self.solo_audio = tk.BooleanVar(value=False)
        self.hacer_resumen = tk.BooleanVar(value=True)
        self.duracion = tk.StringVar(value="180")
        self.segmento = tk.StringVar(value="10")
        self.sin_audio = tk.BooleanVar(value=True)
        self.mezclar = tk.BooleanVar(value=False)

        self._construir()
        self.after(100, self._leer_mensajes)
        self.after(300, self._revisar_requisitos)

    # ---------- interfaz ----------
    def _construir(self):
        marco = ttk.Frame(self, padding=16)
        marco.pack(fill="both", expand=True)
        marco.columnconfigure(0, weight=1)

        origen = ttk.LabelFrame(marco, text="1. Video de origen", padding=10)
        origen.grid(row=0, column=0, sticky="ew")
        origen.columnconfigure(0, weight=1)
        ttk.Label(origen, text="Enlace del video (YouTube o Facebook):").grid(row=0, column=0, sticky="w")
        ttk.Entry(origen, textvariable=self.enlace).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 8))
        ttk.Label(origen, text="...o un video que ya está en esta computadora:").grid(row=2, column=0, sticky="w")
        ttk.Entry(origen, textvariable=self.archivo).grid(row=3, column=0, sticky="ew", pady=2)
        ttk.Button(origen, text="Elegir...", command=self._elegir_archivo).grid(row=3, column=1, padx=(6, 0))

        destino = ttk.LabelFrame(marco, text="2. Dónde guardar las descargas", padding=10)
        destino.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        destino.columnconfigure(0, weight=1)
        ttk.Entry(destino, textvariable=self.carpeta).grid(row=0, column=0, sticky="ew")
        ttk.Button(destino, text="Cambiar...", command=self._elegir_carpeta).grid(row=0, column=1, padx=(6, 0))
        ttk.Checkbutton(destino, text="Solo audio: guardar únicamente el sonido en MP3 (sin video ni resumen)",
                        variable=self.solo_audio, command=self._alternar_audio).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        resumen = ttk.LabelFrame(marco, text="3. Resumen con segmentos al azar", padding=10)
        self.marco_resumen = resumen
        resumen.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        ttk.Checkbutton(resumen, text="Armar resumen (si no, solo se descarga el video)",
                        variable=self.hacer_resumen).grid(row=0, column=0, columnspan=4, sticky="w")
        ttk.Label(resumen, text="Duración total (segundos):").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(resumen, textvariable=self.duracion, width=7).grid(row=1, column=1, sticky="w", padx=6, pady=(8, 0))
        ttk.Label(resumen, text="Cada segmento (segundos):").grid(row=1, column=2, sticky="w", padx=(16, 0), pady=(8, 0))
        ttk.Entry(resumen, textvariable=self.segmento, width=7).grid(row=1, column=3, sticky="w", padx=6, pady=(8, 0))
        ttk.Checkbutton(resumen, text="Sin sonido (también al solo descargar)",
                        variable=self.sin_audio).grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Checkbutton(resumen, text="Segmentos en orden aleatorio",
                        variable=self.mezclar).grid(row=2, column=2, columnspan=2, sticky="w", padx=(16, 0), pady=(8, 0))

        botones = ttk.Frame(marco)
        botones.grid(row=3, column=0, sticky="ew", pady=12)
        self.boton = ttk.Button(botones, text="Comenzar", command=self._comenzar)
        self.boton.pack(side="left")
        self.boton_carpeta = ttk.Button(botones, text="Abrir carpeta del resultado",
                                        command=self._abrir_carpeta, state="disabled")
        self.boton_carpeta.pack(side="left", padx=8)
        self.barra = ttk.Progressbar(botones, mode="indeterminate", length=160)
        self.barra.pack(side="right")

        marco.rowconfigure(4, weight=1)
        caja = ttk.Frame(marco)
        caja.grid(row=4, column=0, sticky="nsew")
        caja.columnconfigure(0, weight=1)
        caja.rowconfigure(0, weight=1)
        self.registro = tk.Text(caja, height=10, state="disabled", wrap="word")
        self.registro.grid(row=0, column=0, sticky="nsew")
        barra_v = ttk.Scrollbar(caja, command=self.registro.yview)
        barra_v.grid(row=0, column=1, sticky="ns")
        self.registro.configure(yscrollcommand=barra_v.set)

    def _alternar_audio(self):
        """Con 'solo audio' no hay resumen: se desactivan esas opciones."""
        estado = "disabled" if self.solo_audio.get() else "normal"
        for control in self.marco_resumen.winfo_children():
            try:
                control.configure(state=estado)
            except tk.TclError:
                pass

    def _elegir_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Elegir video",
            filetypes=[("Videos", "*.mp4 *.mkv *.mov *.webm *.avi *.m4v"), ("Todos los archivos", "*.*")],
        )
        if ruta:
            self.archivo.set(ruta)
            self.enlace.set("")

    def _elegir_carpeta(self):
        ruta = filedialog.askdirectory(title="Carpeta para las descargas")
        if ruta:
            self.carpeta.set(ruta)

    def _abrir_carpeta(self):
        if not self.ultima_carpeta:
            return
        if sys.platform == "win32":
            os.startfile(self.ultima_carpeta)
        elif sys.platform == "darwin":
            subprocess.run(["open", self.ultima_carpeta])
        else:
            subprocess.run(["xdg-open", self.ultima_carpeta])

    def _escribir(self, texto: str):
        self.registro.configure(state="normal")
        self.registro.insert("end", texto + "\n")
        self.registro.see("end")
        self.registro.configure(state="disabled")

    def _revisar_requisitos(self):
        faltan = video.requisitos_faltantes()
        if faltan:
            self._escribir(
                "Falta instalar: " + ", ".join(faltan) + ".\n"
                "Cierra esta ventana, ejecuta instalar.bat y vuelve a abrirla."
            )
        else:
            self._escribir("Todo listo. Pega un enlace o elige un video y presiona Comenzar.")

    # ---------- trabajo ----------
    def _comenzar(self):
        enlace = self.enlace.get().strip()
        archivo = self.archivo.get().strip().strip('"')
        if not enlace and not archivo:
            messagebox.showwarning("Falta el video", "Pega un enlace de YouTube o Facebook, o elige un video de la computadora.")
            return
        if not enlace and not self.hacer_resumen.get() and not self.solo_audio.get() and not self.sin_audio.get():
            messagebox.showwarning("Nada que hacer", "Elegiste un video local sin resumen ni cambios. Activa el resumen, Sin sonido o Solo audio, o pega un enlace.")
            return
        try:
            duracion = float(self.duracion.get().replace(",", "."))
            segmento = float(self.segmento.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Revisa los números", "La duración y el segmento deben ser números, por ejemplo 180 y 10.")
            return

        trabajo = {
            "enlace": enlace, "archivo": archivo, "carpeta": Path(self.carpeta.get().strip()),
            "solo_audio": self.solo_audio.get(),
            "resumen": self.hacer_resumen.get() and not self.solo_audio.get(), "duracion": duracion, "segmento": segmento,
            "sin_audio": self.sin_audio.get(), "mezclar": self.mezclar.get(),
        }
        self.boton.configure(state="disabled")
        self.barra.start(12)
        self._escribir("-" * 40)
        threading.Thread(target=self._trabajar, args=(trabajo,), daemon=True).start()

    def _trabajar(self, t: dict):
        avisar = lambda texto: self.mensajes.put(("texto", texto))
        try:
            if t["enlace"]:
                origen = video.descargar(t["enlace"], t["carpeta"], avisar, solo_audio=t["solo_audio"],
                                         sin_audio=t["sin_audio"] and not t["resumen"])
            else:
                origen = Path(t["archivo"])
            resultado = origen
            if t["solo_audio"] and not t["enlace"]:
                resultado = video.extraer_audio(origen, avisar)
            elif t["sin_audio"] and not t["resumen"] and not t["enlace"]:
                resultado = video.quitar_audio(origen, avisar)
            if t["resumen"]:
                avisar("Armando el resumen...")
                resultado = video.crear_resumen(
                    origen, t["duracion"], t["segmento"], t["sin_audio"], t["mezclar"], avisar
                )
            self.mensajes.put(("fin", str(resultado)))
        except video.ErrorHerramienta as error:
            self.mensajes.put(("error", str(error)))
        except Exception as error:  # cualquier otro fallo: mostrarlo en vez de cerrar la ventana
            self.mensajes.put(("error", f"Error inesperado: {error}"))

    def _leer_mensajes(self):
        try:
            while True:
                tipo, texto = self.mensajes.get_nowait()
                if tipo == "texto":
                    self._escribir(texto)
                else:
                    self.barra.stop()
                    self.boton.configure(state="normal")
                    if tipo == "fin":
                        self.ultima_carpeta = str(Path(texto).parent)
                        self.boton_carpeta.configure(state="normal")
                        self._escribir(f"Terminado. Archivo: {texto}")
                    else:
                        self._escribir(f"ERROR: {texto}")
        except queue.Empty:
            pass
        self.after(100, self._leer_mensajes)


if __name__ == "__main__":
    Ventana().mainloop()
