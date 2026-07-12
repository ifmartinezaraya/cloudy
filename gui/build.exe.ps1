# CloudVault GUI - Script de compilacion a ejecutable
# Genera CloudVault.exe usando PyInstaller
#
# Uso:
#   .\build.exe.ps1
#
# Requisitos:
#   - Python 3.9+
#   - pip install pyinstaller
#   - Las dependencias de requirements.txt instaladas

param(
    [switch]$Clean,
    [switch]$Debug
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  CloudVault GUI - Build Ejecutable" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

# Verificar Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python no encontrado. Instala Python 3.9+" -ForegroundColor Red
    exit 1
}

# Instalar dependencias
Write-Host ""
Write-Host "[*] Instalando dependencias..." -ForegroundColor Cyan
pip install -r "$ScriptDir\requirements.txt" --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Fallo la instalacion de dependencias" -ForegroundColor Red
    exit 1
}

# Instalar PyInstaller si no esta
Write-Host "[*] Verificando PyInstaller..." -ForegroundColor Cyan
pip install pyinstaller --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Fallo la instalacion de PyInstaller" -ForegroundColor Red
    exit 1
}

# Generar icono si no existe
$iconPath = "$ScriptDir\assets\cloud.ico"
if (-not (Test-Path $iconPath)) {
    Write-Host "[*] Generando icono..." -ForegroundColor Cyan
    python "$ScriptDir\assets\generate_icon.py"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[WARN] No se pudo generar el icono, continuando sin icono" -ForegroundColor Yellow
        $iconPath = $null
    }
}

# Limpiar build anterior si se solicita
if ($Clean) {
    Write-Host "[*] Limpiando build anterior..." -ForegroundColor Cyan
    Remove-Item -Path "$ScriptDir\dist" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$ScriptDir\build" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$ScriptDir\*.spec" -Force -ErrorAction SilentlyContinue
}

# Construir ejecutable
Write-Host ""
Write-Host "[*] Compilando CloudVault.exe..." -ForegroundColor Cyan
Write-Host ""

$pyinstallerArgs = @(
    "--onefile",
    "--windowed",
    "--name=CloudVault",
    "--add-data=assets;assets",
    "--hidden-import=customtkinter",
    "--hidden-import=pystray",
    "--hidden-import=PIL",
    "--hidden-import=gui.splash",
    "--hidden-import=gui.shortcuts",
    "--collect-all=customtkinter"
)

if ($iconPath -and (Test-Path $iconPath)) {
    $pyinstallerArgs += "--icon=$iconPath"
}

if ($Debug) {
    $pyinstallerArgs += "--debug=all"
    $pyinstallerArgs = $pyinstallerArgs | Where-Object { $_ -ne "--windowed" }
}

$pyinstallerArgs += "$ScriptDir\app.py"

Push-Location $ScriptDir
try {
    pyinstaller @pyinstallerArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] PyInstaller fallo" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}

# Verificar resultado
$exePath = "$ScriptDir\dist\CloudVault.exe"
if (Test-Path $exePath) {
    $size = (Get-Item $exePath).Length / 1MB
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  BUILD EXITOSO" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Ejecutable: $exePath" -ForegroundColor White
    Write-Host "  Tamano: $([math]::Round($size, 1)) MB" -ForegroundColor White
    Write-Host ""
    Write-Host "  Para ejecutar:" -ForegroundColor Gray
    Write-Host "    .\dist\CloudVault.exe" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "[ERROR] No se genero el ejecutable" -ForegroundColor Red
    exit 1
}
