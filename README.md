# Videos para NotiFE

Herramienta de escritorio para preparar video de fondo de NotiFE:

1. **Descarga** un video de YouTube o Facebook a partir de su enlace (o usa un video que ya esté en la computadora).
2. **Arma un resumen** con segmentos tomados al azar de distintas partes del video, por ejemplo 3 minutos en cortes de 10 segundos, con o sin sonido.

Todo corre en tu computadora; no se sube nada a ningún servidor.

## Instalación (una sola vez)

Necesitas Windows 10 u 11 y [Python](https://www.python.org/downloads/) (al instalarlo, marca **"Add Python to PATH"**).

1. Descarga este proyecto: botón verde **Code → Download ZIP**, y descomprímelo donde quieras.
2. Haz doble clic en **`instalar.bat`**. Instala lo necesario: yt-dlp, Deno y ffmpeg.
3. Cierra esa ventana cuando termine.

## Uso

1. Doble clic en **`iniciar.bat`**.
2. Pega el enlace del video (YouTube o Facebook), o elige un video de tu computadora.
3. Ajusta la duración total, la duración de cada segmento y si lo quieres sin sonido.
4. Presiona **Comenzar**. Al terminar, usa **Abrir carpeta del resultado**.

El video descargado se guarda en `Descargas\YouTube` (se puede cambiar) y el resumen queda junto a él con `_resumen` al final del nombre. Cada vez que lo ejecutas sale una selección distinta de segmentos.

## Si algo falla

| Problema | Solución |
| --- | --- |
| "No se pudo descargar" con un enlace correcto | YouTube y Facebook cambian seguido. Ejecuta `instalar.bat` otra vez para actualizar yt-dlp. |
| Un video de Facebook no se descarga | Solo funcionan los videos **públicos**. Los de grupos privados, perfiles restringidos o que piden iniciar sesión no se pueden descargar. |
| "Falta instalar: ..." al abrir | Ejecuta `instalar.bat`, ciérralo y vuelve a abrir la herramienta. |
| El resumen corta a media frase | Los cortes son al azar. Vuelve a generarlo o cambia la duración de los segmentos. |

## Uso responsable

Descargar un video no da derecho a difundirlo. Usa esta herramienta solo con material propio, con licencia libre o para el que NotiFE tenga permiso del titular.

## Archivos

- `app.py`: la ventana.
- `video.py`: descarga (yt-dlp) y armado del resumen (ffmpeg).
- `instalar.bat` / `iniciar.bat`: instalación y arranque en Windows.
