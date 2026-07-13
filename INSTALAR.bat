@echo off
:: ============================================================
:: CloudVault - INSTALADOR FACIL
:: Solo haz doble clic en este archivo!
:: ============================================================

echo.
echo   ============================================
echo        CLOUDVAULT - INSTALADOR FACIL
echo        Tu Nube Personal Cifrada
echo   ============================================
echo.
echo   Este instalador va a:
echo     1. Verificar que Docker este corriendo
echo     2. Instalar Python si hace falta
echo     3. Configurar todo automaticamente
echo.
echo   Presiona cualquier tecla para empezar...
pause >nul

:: Detectar donde estamos
cd /d "%~dp0"
echo.
echo   [*] Carpeta detectada: %CD%
echo.

:: Verificar Docker
echo   [1/5] Verificando Docker Desktop...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   [ERROR] Docker Desktop no esta corriendo!
    echo.
    echo   Abre Docker Desktop y espera a que diga
    echo   "Engine running", luego ejecuta este archivo de nuevo.
    echo.
    pause
    exit /b 1
)
echo         Docker OK!
echo.

:: Verificar Python
echo   [2/5] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   [!] Python no encontrado. Instalando...
    echo.
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo.
        echo   [ERROR] No se pudo instalar Python automaticamente.
        echo   Descargalo de: https://www.python.org/downloads/
        echo   IMPORTANTE: Marca "Add Python to PATH" al instalar.
        echo.
        pause
        exit /b 1
    )
    :: Refrescar PATH
    set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts"
)
echo         Python OK!
echo.

:: Verificar pip y instalar dependencias del GUI
echo   [3/5] Instalando dependencias de la interfaz...
pip install -r gui\requirements.txt --quiet 2>nul
if %errorlevel% neq 0 (
    python -m pip install -r gui\requirements.txt --quiet
)
echo         Dependencias OK!
echo.

:: Generar icono
echo   [4/5] Generando icono de nube...
python gui\assets\generate_icon.py 2>nul
echo         Icono OK!
echo.

:: Configurar PowerShell y ejecutar setup
echo   [5/5] Iniciando configuracion principal...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"

echo.
echo   ============================================
echo        INSTALACION COMPLETADA!
echo   ============================================
echo.
echo   Para abrir CloudVault:
echo     - Doble clic en ABRIR.bat
echo     - O ejecuta: python gui\app.py
echo.
echo   Para conectar tu iPhone:
echo     1. Descarga "Immich" de la App Store
echo     2. Usa la URL que aparecio arriba
echo.
pause
