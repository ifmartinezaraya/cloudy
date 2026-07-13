@echo off
:: ============================================================
:: CloudVault - ABRIR LA APP
:: Solo haz doble clic!
:: ============================================================

cd /d "%~dp0"

:: Verificar Docker
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   Abriendo Docker Desktop, espera un momento...
    echo.
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    timeout /t 30 /nobreak >nul
)

:: Iniciar servicios
echo   Iniciando CloudVault...
docker compose up -d 2>nul

:: Abrir la app
start "" python "%~dp0gui\app.py"
