@echo off
:: ============================================================
:: CloudVault - ABRIR
:: Doble clic para iniciar todo
:: ============================================================

cd /d "%~dp0"

:: Verificar Docker
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo   Abriendo Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" 2>nul
    echo   Esperando 45 segundos...
    timeout /t 45 /nobreak >nul
)

:: Iniciar servicios
docker compose up -d 2>nul

:: Abrir navegador
timeout /t 10 /nobreak >nul
start http://localhost:2283

echo.
echo   CloudVault esta corriendo!
echo   Navegador abierto en: http://localhost:2283
echo.
pause
