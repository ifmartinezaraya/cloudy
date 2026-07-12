# ============================================================
# CloudVault - Restaurar desde Nube
# Uso: .\scripts\restore.ps1 [-DestPath "C:\Restore"] [-Provider mega]
# ============================================================

param(
    [string]$DestPath = "",
    [string]$Provider = "union",
    [switch]$ListOnly
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot

. (Join-Path $ROOT "scripts\lib\common.ps1")
. (Join-Path $ROOT "scripts\lib\logger.ps1")

Initialize-Logger
$settings = Get-CloudVaultSettings

Show-Banner "RESTAURAR DESDE NUBE CIFRADA"

# Verificar rclone
if (-not (Test-RcloneInstalled)) {
    Show-Error "Rclone no instalado."
    exit 1
}

# Determinar remote
$remote = switch ($Provider) {
    "union" { "$($settings.cloud.union_name):immich-backup" }
    "mega"  { "mega-cifrado:immich-backup" }
    "gdrive" { "gdrive-cifrado:immich-backup" }
    "onedrive" { "onedrive-cifrado:immich-backup" }
    default { "$($settings.cloud.union_name):immich-backup" }
}

# Listar contenido
if ($ListOnly) {
    Write-Host "  Contenido en la nube ($Provider):" -ForegroundColor White
    Write-Host ""
    rclone ls $remote --max-depth 2 2>&1 | Select-Object -First 50 | ForEach-Object {
        Write-Host "    $_" -ForegroundColor Gray
    }
    Write-Host ""
    exit 0
}

# Destino
if ([string]::IsNullOrEmpty($DestPath)) {
    $DestPath = Join-Path $ROOT "upload\library"
}

Write-Host "  Origen:  $remote" -ForegroundColor White
Write-Host "  Destino: $DestPath" -ForegroundColor White
Write-Host ""

# Verificar espacio
$freeGB = Get-DiskFreeSpaceGB
Write-Host "  Espacio libre: $freeGB GB" -ForegroundColor White
Write-Host ""

Show-Warning "ADVERTENCIA: Esto puede tomar MUCHO tiempo."
Show-Warning "Tu notebook debe estar conectado a internet y al cargador."
Write-Host ""

if (-not (Confirm-Action "Iniciar restauracion?")) {
    exit 0
}

# Crear destino
if (-not (Test-Path $DestPath)) {
    New-Item -ItemType Directory -Path $DestPath -Force | Out-Null
}

# Ejecutar restauracion
Write-Host ""
Show-Info "Descargando y descifrando archivos..."
Write-Host ""

$restoreArgs = @(
    "copy"
    $remote
    $DestPath
    "--transfers", $settings.sync.transfers
    "--checkers", $settings.sync.checkers
    "--progress"
    "--stats", "10s"
    "--retries", "10"
    "--low-level-retries", "20"
)

& rclone @restoreArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Show-Success "Restauracion completada!"
    Write-Host ""
    Write-Host "  Tus fotos estan en: $DestPath" -ForegroundColor Green
    Write-Host ""
    Show-Info "Si Immich esta corriendo, ve a Admin > Jobs > 'Scan External Library'"
    Write-Log -Level "INFO" -Message "Restauracion completada: $DestPath" -Component "Restore"
} else {
    Show-Warning "Restauracion parcial. Ejecuta de nuevo para reintentar."
    Write-Log -Level "WARN" -Message "Restauracion con errores (code: $LASTEXITCODE)" -Component "Restore"
}
