"""
Funciones de trabajo de la herramienta: descargar un video y armar un resumen
con segmentos al azar. No depende de la ventana; app.py la usa.
"""

import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# En Windows, evita que se abra una ventana negra por cada llamada a ffmpeg
_OCULTAR = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}


class ErrorHerramienta(Exception):
    """Error con un mensaje pensado para mostrarse tal cual al usuario."""


def requisitos_faltantes() -> list[str]:
    """Devuelve la lista de programas que faltan (vacía si todo está instalado)."""
    faltan = []
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        faltan.append("yt-dlp")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        faltan.append("ffmpeg")
    if not shutil.which("deno"):
        faltan.append("deno")
    return faltan


def _ejecutar(comando: list[str]) -> str:
    try:
        return subprocess.run(
            comando, capture_output=True, text=True, check=True,
            encoding="utf-8", errors="replace", **_OCULTAR,
        ).stdout
    except FileNotFoundError:
        raise ErrorHerramienta("No encontré ffmpeg. Ejecuta instalar.bat y vuelve a abrir la herramienta.")
    except subprocess.CalledProcessError as error:
        detalle = (error.stderr or "").strip().splitlines()[-1:] or ["sin detalle"]
        raise ErrorHerramienta(f"ffmpeg falló: {detalle[0]}")


def duracion_de(video: Path) -> float:
    salida = _ejecutar(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video)]
    ).strip()
    try:
        return float(salida)
    except ValueError:
        raise ErrorHerramienta(f"No pude leer la duración de: {video.name}")


def descargar(url: str, carpeta: Path, avisar=print) -> Path:
    """Descarga un video (YouTube, Facebook, etc.) en la carpeta indicada y devuelve su ruta."""
    try:
        import yt_dlp
    except ImportError:
        raise ErrorHerramienta("Falta yt-dlp. Ejecuta instalar.bat y vuelve a abrir la herramienta.")

    carpeta.mkdir(parents=True, exist_ok=True)
    hay_ffmpeg = shutil.which("ffmpeg") is not None
    ultimo = {"pct": -10}

    def progreso(d):
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            if total:
                pct = int(d.get("downloaded_bytes", 0) * 100 / total)
                if pct >= ultimo["pct"] + 10:
                    ultimo["pct"] = pct - pct % 10
                    avisar(f"  Descargando... {ultimo['pct']}%")
        elif d.get("status") == "finished":
            ultimo["pct"] = -10

    class Registro:
        def debug(self, msg): pass
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass

    opciones = {
        "outtmpl": str(carpeta / "%(title)s.%(ext)s"),
        "noplaylist": True,
        "windowsfilenames": True,
        "progress_hooks": [progreso],
        "logger": Registro(),
    }
    if hay_ffmpeg:
        opciones["format"] = "bestvideo+bestaudio/best"
        opciones["merge_output_format"] = "mp4"
    else:
        opciones["format"] = "best[ext=mp4]/best"
        avisar("Aviso: sin ffmpeg el video se descarga en calidad limitada.")

    avisar("Conectando con el sitio del video...")
    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
            descargas = info.get("requested_downloads") or []
            ruta = descargas[0]["filepath"] if descargas else ydl.prepare_filename(info)
    except yt_dlp.utils.DownloadError as error:
        raise ErrorHerramienta(
            f"No se pudo descargar: {error}\n"
            "Si el enlace es correcto, ejecuta instalar.bat para actualizar yt-dlp e intenta de nuevo."
        )
    avisar(f"Descargado: {Path(ruta).name}")
    return Path(ruta)


def crear_resumen(video: Path, duracion: float = 180, segmento: float = 10,
                  sin_audio: bool = False, mezclar: bool = False, avisar=print) -> Path:
    """Arma un video de `duracion` segundos con segmentos al azar de `video`.

    El video se divide en tramos iguales y se toma un punto al azar de cada uno,
    así los segmentos quedan repartidos por todo el video y no se enciman.
    """
    if not video.is_file():
        raise ErrorHerramienta(f"No encontré el archivo: {video}")
    if duracion <= 0 or segmento <= 0:
        raise ErrorHerramienta("La duración y el segmento deben ser mayores que cero.")

    total = duracion_de(video)
    if total <= duracion:
        raise ErrorHerramienta(
            f"El video dura {total:.0f} s; es más corto que el resumen pedido ({duracion:.0f} s)."
        )

    n = max(1, round(duracion / segmento))
    largo = duracion / n
    tramo = total / n
    inicios = [i * tramo + random.uniform(0, tramo - largo) for i in range(n)]
    if mezclar:
        random.shuffle(inicios)

    salida = video.with_name(f"{video.stem}_resumen.mp4")
    contador = 2
    while salida.exists():
        salida = video.with_name(f"{video.stem}_resumen_{contador}.mp4")
        contador += 1

    if sin_audio:
        audio = ["-an"]
    else:
        audio = ["-map", "0:a:0?", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2"]

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        lineas = []
        for i, inicio in enumerate(inicios, 1):
            parte = tmp / f"parte_{i:03d}.mp4"
            m, s = divmod(int(inicio), 60)
            h, m = divmod(m, 60)
            avisar(f"  Segmento {i} de {n} (minuto {h:02d}:{m:02d}:{s:02d})")
            _ejecutar(
                ["ffmpeg", "-v", "error", "-y", "-ss", f"{inicio:.3f}", "-i", str(video),
                 "-t", f"{largo:.3f}", "-map", "0:v:0", *audio,
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                 str(parte)]
            )
            ruta_segura = parte.as_posix().replace("'", "'\\''")
            lineas.append(f"file '{ruta_segura}'\n")

        lista = tmp / "lista.txt"
        lista.write_text("".join(lineas), encoding="utf-8")
        avisar("Uniendo segmentos...")
        _ejecutar(
            ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista),
             "-c", "copy", "-movflags", "+faststart", str(salida)]
        )

    avisar(f"Resumen listo: {salida.name} ({duracion_de(salida):.0f} s)")
    return salida
