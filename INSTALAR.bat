@echo off
:: ============================================================
:: CloudVault - INSTALADOR COMPLETO
:: Solo haz doble clic y espera!
:: ============================================================

echo.
echo   ============================================
echo        CLOUDVAULT - INSTALANDO TODO
echo        Solo espera, no toques nada!
echo   ============================================
echo.

:: Ir a la carpeta donde esta este archivo
cd /d "%~dp0"

:: Copiar archivos necesarios a la raiz
echo   [1/6] Preparando archivos...
if not exist "docker-compose.yml" copy config\docker-compose.yml . >nul 2>&1
if not exist ".env" (
    echo IMMICH_VERSION=release> .env
    echo DB_PASSWORD=CloudVault2024Seguro!>> .env
    echo DB_USERNAME=postgres>> .env
    echo DB_DATABASE_NAME=immich>> .env
    echo DB_DATA_LOCATION=./postgres>> .env
    echo UPLOAD_LOCATION=./upload>> .env
    echo IMMICH_PORT=2283>> .env
    echo TZ=America/Santiago>> .env
    echo MACHINE_LEARNING_ENABLED=true>> .env
)
if not exist "upload" mkdir upload
if not exist "postgres" mkdir postgres
echo         Archivos listos!
echo.

:: Verificar Docker
echo   [2/6] Verificando Docker...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   [!] Docker no esta corriendo. Intentando abrir...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" 2>nul
    echo   Esperando 60 segundos a que Docker inicie...
    timeout /t 60 /nobreak >nul
    docker info >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo   [ERROR] Docker no pudo iniciar.
        echo   Abre Docker Desktop manualmente, espera a que este listo,
        echo   y luego haz doble clic en este archivo de nuevo.
        echo.
        pause
        exit /b 1
    )
)
echo         Docker OK!
echo.

:: Descargar e iniciar Immich
echo   [3/6] Descargando Immich (primera vez tarda 5-15 min)...
echo         No cierres esta ventana!
echo.
docker compose pull
echo.
echo   [4/6] Iniciando servicios...
docker compose up -d
echo.

:: Esperar a que este listo
echo   [5/6] Esperando a que Immich este listo...
set intentos=0
:esperar
timeout /t 10 /nobreak >nul
set /a intentos+=1
curl -s http://localhost:2283/api/server-info/ping >nul 2>&1
if %errorlevel% equ 0 goto listo
if %intentos% lss 18 (
    echo         Todavia iniciando... (intento %intentos%/18)
    goto esperar
)
echo         Immich esta iniciando, puede tardar un poco mas...
goto abrir

:listo
echo         Immich esta listo!
echo.

:abrir
:: Instalar Python y dependencias del GUI
echo   [6/6] Preparando interfaz grafica...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    pip install -r gui\requirements.txt --quiet 2>nul
    python gui\assets\generate_icon.py >nul 2>&1
)

:: Abrir Immich en el navegador
echo.
echo   ============================================
echo         CLOUDVAULT INSTALADO!
echo   ============================================
echo.
echo   Abriendo Immich en tu navegador...
echo.
echo   CREA TU CUENTA:
echo     Email: tu email
echo     Password: una contrasena segura
echo.
echo   PARA TU IPHONE:
echo     1. Descarga "Immich" de la App Store
echo     2. Server URL: http://TU_IP:2283
echo        (busca tu IP en Configuracion WiFi del iPhone)
echo.
start http://localhost:2283
echo.
echo   Para abrir CloudVault despues: doble clic en ABRIR.bat
echo.
pause
