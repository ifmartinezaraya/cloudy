# ============================================================
# CloudVault - Detener Servicios
# Uso: .\scripts\stop-services.ps1 [-Force] [-Quiet]
# ============================================================

param(
    [switch]$Force,
    [switch]$Quiet
)

$ROOT = Split-Path -Parent $PSScriptRoot

# Cargar librerias
. (Join-Path $ROOT "scripts\lib\common.ps1")
. (Join-Path $ROOT "scripts\lib\logger.ps1")

Initialize-Logger

if (-not $Quiet) {
    Show-Banner "DETENIENDO CLOUDVAULT"
}

# Verificar si hay sync en progreso
$syncLock = Join-Path $ROOT "logs\.sync-lock"
if ((Test-Path $syncLock) -and -not $Force) {
    Show-Warning "Hay una sincronizacion en progreso."
    if (-not (Confirm-Action "Deseas detener de todas formas?")) {
        exit 0
    }
}

if (-not $Quiet) { Show-Step 1 2 "Deteniendo contenedores..." }

Set-Location $ROOT

if ($Force) {
    docker compose down --remove-orphans 2>&1 | ForEach-Object {
        if (-not $Quiet) { Write-Host "    $_" -ForegroundColor Gray }
    }
} else {
    docker compose stop 2>&1 | ForEach-Object {
        if (-not $Quiet) { Write-Host "    $_" -ForegroundColor Gray }
    }
}

if (-not $Quiet) { Show-Success "Contenedores detenidos" }

if (-not $Quiet) { Show-Step 2 2 "Verificando..." }
$running = docker compose ps --status running -q 2>&1
if ([string]::IsNullOrEmpty($running)) {
    if (-not $Quiet) { Show-Success "Todos los servicios detenidos" }
} else {
    if (-not $Quiet) { Show-Warning "Algunos contenedores aun estan corriendo" }
}

Write-Host ""
Write-Log -Level "INFO" -Message "Servicios detenidos" -Component "Stop"
