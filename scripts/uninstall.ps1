# ============================================================
# CloudVault - Desinstalar
# Uso: .\scripts\uninstall.ps1 [-KeepData] [-KeepCloud]
# ============================================================

param(
    [switch]$KeepData,
    [switch]$KeepCloud
)

$ROOT = Split-Path -Parent $PSScriptRoot

. (Join-Path $ROOT "scripts\lib\common.ps1")
. (Join-Path $ROOT "scripts\lib\logger.ps1")

Initialize-Logger
Assert-Administrator

Show-Banner "DESINSTALAR CLOUDVAULT"

Write-Host "  Esto eliminara:" -ForegroundColor Red
Write-Host "    - Contenedores Docker de CloudVault" -ForegroundColor White
Write-Host "    - Imagenes Docker descargadas" -ForegroundColor White
Write-Host "    - Tarea programada de sincronizacion" -ForegroundColor White
if (-not $KeepData) {
    Write-Host "    - TODAS las fotos y datos locales" -ForegroundColor Red
}
if (-not $KeepCloud) {
    Write-Host "    - Configuracion de Rclone (nubes)" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "  NO se eliminara:" -ForegroundColor Green
Write-Host "    - Docker Desktop" -ForegroundColor Gray
Write-Host "    - Rclone" -ForegroundColor Gray
Write-Host "    - Archivos en las nubes (Mega/GDrive/OneDrive)" -ForegroundColor Gray
Write-Host ""

if (-not (Confirm-Action "SEGURO que deseas desinstalar CloudVault?")) {
    exit 0
}

$confirm2 = Read-Host "  Escribe 'ELIMINAR' para confirmar"
if ($confirm2 -ne "ELIMINAR") {
    Show-Info "Cancelado."
    exit 0
}

Write-Host ""

# 1. Detener servicios
Show-Step 1 5 "Deteniendo servicios..."
Set-Location $ROOT
docker compose down --remove-orphans --volumes 2>&1 | Out-Null
Show-Success "Servicios detenidos"

# 2. Eliminar imagenes
Show-Step 2 5 "Eliminando imagenes Docker..."
docker rmi $(docker images "ghcr.io/immich-app/*" -q) 2>&1 | Out-Null
docker rmi $(docker images "tensorchord/pgvecto-rs*" -q) 2>&1 | Out-Null
docker rmi $(docker images "redis*" -q) 2>&1 | Out-Null
Show-Success "Imagenes eliminadas"

# 3. Eliminar tarea programada
Show-Step 3 5 "Eliminando tarea programada..."
$settings = Get-CloudVaultSettings
schtasks /delete /tn $settings.sync.task_name /f 2>&1 | Out-Null
Show-Success "Tarea eliminada"

# 4. Eliminar datos locales
if (-not $KeepData) {
    Show-Step 4 5 "Eliminando datos locales..."
    $foldersToDelete = @("upload", "postgres", "logs")
    foreach ($folder in $foldersToDelete) {
        $path = Join-Path $ROOT $folder
        if (Test-Path $path) {
            Remove-Item $path -Recurse -Force
        }
    }
    Show-Success "Datos locales eliminados"
} else {
    Show-Step 4 5 "Conservando datos locales (--KeepData)"
}

# 5. Limpiar rclone config
if (-not $KeepCloud) {
    Show-Step 5 5 "Limpiando configuracion de nubes..."
    $remotes = @("mega-raw", "mega-cifrado", "gdrive-raw", "gdrive-cifrado",
                 "onedrive-raw", "onedrive-cifrado", "cloudvault-union")
    foreach ($remote in $remotes) {
        rclone config delete $remote 2>&1 | Out-Null
    }
    Show-Success "Configuracion de nubes eliminada"
} else {
    Show-Step 5 5 "Conservando config de nubes (--KeepCloud)"
}

Write-Host ""
Show-Success "CloudVault desinstalado."
Write-Host ""
Write-Host "  NOTA: Tus fotos EN LAS NUBES siguen ahi." -ForegroundColor Yellow
Write-Host "  Para eliminarlas tambien, hazlo manualmente en" -ForegroundColor Yellow
Write-Host "  Mega.nz / Google Drive / OneDrive." -ForegroundColor Yellow
Write-Host ""

Write-Log -Level "INFO" -Message "CloudVault desinstalado" -Component "Uninstall"
