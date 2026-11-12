@echo off
cd /d "%~dp0"
echo ============================================
echo  Instalacion: Videos para el noticiero
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo No se encontro Python.
    echo Instalalo desde https://www.python.org/downloads/
    echo y marca la casilla "Add Python to PATH". Luego vuelve a ejecutar este archivo.
    echo.
    pause
    exit /b 1
)

echo [1/3] Instalando o actualizando yt-dlp...
python -m pip install -U -r requirements.txt
if errorlevel 1 (
    echo.
    echo No se pudo instalar yt-dlp. Revisa tu conexion a internet e intenta de nuevo.
    pause
    exit /b 1
)

echo.
echo [2/3] Revisando Deno...
where deno >nul 2>nul
if errorlevel 1 (
    winget install -e --id DenoLand.Deno --accept-source-agreements --accept-package-agreements
) else (
    echo Deno ya esta instalado.
)

echo.
echo [3/3] Revisando ffmpeg...
where ffmpeg >nul 2>nul
if errorlevel 1 (
    winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
) else (
    echo ffmpeg ya esta instalado.
)

echo.
echo ============================================
echo  Listo. Ahora abre la herramienta con iniciar.bat
echo  Si es la primera instalacion, cierra esta ventana antes.
echo ============================================
pause
