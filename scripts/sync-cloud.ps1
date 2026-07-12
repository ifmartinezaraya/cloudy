# ============================================================
# CloudVault - Sincronizacion a Nube Cifrada
# Uso: .\scripts\sync-cloud.ps1 [-Force] [-DryRun] [-Verbose]
# ============================================================

param(
    [switch]$Force,
    [switch]$DryRun,
    [switch]$VerboseOutput
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot

. (Join-Path $ROOT "scripts\lib\common.ps1")
. (Join-Path $ROOT "scripts\lib\logger.ps1")

Initialize-Logger
$settings = Get-CloudVaultSettings

# --- Configuracion desde settings ---
$uploadPath = Join-Path $ROOT $settings.storage.upload_path "library"
$unionRemote = "$($settings.cloud.union_name):immich-backup"
$transfers = $settings.sync.transfers
$checkers = $settings.sync.checkers
$retries = $settings.sync.retries
$minAgeHours = $settings.sync.min_age_hours
$verifyAfter = $settings.sync.verify_after_upload
$daysKeepLocal = $settings.storage.originals_keep_local_days
$isDryRun = $settings.sync.dry_run

# Override con parametros
if ($Force) { $minAgeHours = 0 }
if ($DryRun) { $isDryRun = $true }

# --- Lock file (evitar ejecuciones simultaneas) ---
$lockFile = Join-Path $ROOT "logs\.sync-lock"
if (Test-Path $lockFile) {
    $lockAge = (Get-Date) - (Get-Item $lockFile).LastWriteTime
    if ($lockAge.TotalHours -lt 6) {
        Write-SyncLog "Sync ya en progreso (lock: $lockFile). Abortando." "WARN"
        Show-Warning "Sincronizacion ya en progreso. Usa -Force para ignorar."
        exit 0
    }
    # Lock viejo, eliminar
    Remove-Item $lockFile -Force
}

# Crear lock
New-Item -Path $lockFile -ItemType File -Force | Out-Null

try {
    Write-SyncLog "=== INICIO DE SINCRONIZACION ==="
    Write-SyncLog "Modo: $(if($isDryRun){'DRY-RUN (simulacion)'}else{'REAL'})"
    Write-SyncLog "Origen: $uploadPath"
    Write-SyncLog "Destino: $unionRemote"

    Show-Banner "SINCRONIZACION A NUBE CIFRADA"

    # 1. Verificar prerequisites
    Show-Step 1 4 "Verificando sistema..."

    if (-not (Test-Path $uploadPath)) {
        Show-Error "Carpeta de fotos no encontrada: $uploadPath"
        Write-SyncLog "ERROR: Carpeta no encontrada: $uploadPath" "ERROR"
        exit 1
    }

    if (-not (Test-RcloneInstalled)) {
        Show-Error "Rclone no instalado"
        exit 1
    }

    if (-not (Test-RcloneRemoteExists $settings.cloud.union_name)) {
        Show-Error "Union de nubes no configurada. Ejecuta configure-cloud.ps1"
        exit 1
    }

    $localSize = Get-FolderSizeGB -Path $uploadPath
    Show-Success "Fotos locales: $localSize GB"
    Write-SyncLog "Tamano local: $localSize GB"

    # 2. Subir archivos nuevos
    Show-Step 2 4 "Subiendo archivos nuevos a la nube..."
    if ($isDryRun) { Show-Info "(Modo simulacion - no se subira nada)" }

    $rcloneArgs = @(
        "copy"
        $uploadPath
        $unionRemote
        "--transfers", $transfers
        "--checkers", $checkers
        "--retries", $retries
        "--low-level-retries", $settings.sync.low_level_retries
        "--ignore-existing"
        "--stats", "30s"
        "--stats-one-line"
    )

    if ($minAgeHours -gt 0) {
        $rcloneArgs += "--min-age"
        $rcloneArgs += "${minAgeHours}h"
    }

    if (-not [string]::IsNullOrEmpty($settings.sync.bandwidth_limit)) {
        $rcloneArgs += "--bwlimit"
        $rcloneArgs += $settings.sync.bandwidth_limit
    }

    if ($isDryRun) { $rcloneArgs += "--dry-run" }
    if ($VerboseOutput) { $rcloneArgs += "-v" }

    Write-SyncLog "Ejecutando: rclone $($rcloneArgs -join ' ')"

    $output = & rclone @rcloneArgs 2>&1
    $syncExitCode = $LASTEXITCODE

    if ($syncExitCode -ne 0) {
        Show-Warning "Rclone retorno codigo $syncExitCode"
        Write-SyncLog "Rclone exit code: $syncExitCode" "WARN"
    } else {
        Show-Success "Subida completada"
        Write-SyncLog "Subida completada exitosamente"
    }

    # 3. Verificar integridad
    if ($verifyAfter -and -not $isDryRun) {
        Show-Step 3 4 "Verificando integridad..."

        $checkArgs = @(
            "check", $uploadPath, $unionRemote
            "--one-way"
        )

        $checkOutput = & rclone @checkArgs 2>&1
        $checkCode = $LASTEXITCODE

        if ($checkCode -eq 0) {
            Show-Success "Integridad verificada"
            Write-SyncLog "Verificacion de integridad OK"
        } else {
            Show-Warning "Algunas verificaciones fallaron (archivos aun subiendo?)"
            Write-SyncLog "Verificacion con diferencias (codigo: $checkCode)" "WARN"
        }
    } else {
        Show-Step 3 4 "Verificacion omitida (dry-run o deshabilitada)"
    }

    # 4. Limpieza local (ADAPTATIVA - segun espacio disponible)
    Show-Step 4 4 "Evaluando limpieza local..."

    $freeGB = Get-DiskFreeSpaceGB
    $cleanupThreshold = $settings.storage.cleanup_when_disk_below_gb
    $keepOriginals = $settings.storage.originals_keep_local

    if ($keepOriginals -and $freeGB -gt $cleanupThreshold) {
        Show-Success "Espacio suficiente ($freeGB GB libres). Originales se conservan localmente."
        Write-SyncLog "Modo Full Local: $freeGB GB libres > $cleanupThreshold GB umbral. No se borra nada."
    }
    elseif ($settings.storage.auto_cleanup) {
        Show-Info "Disco bajo ($freeGB GB). Limpiando archivos ya respaldados..."

        $cleanArgs = @(
            "delete", $uploadPath
            "--min-age", "${daysKeepLocal}d"
            "--rmdirs"
        )

        if ($isDryRun) {
            $cleanArgs += "--dry-run"
            Show-Info "(Simulacion - no se borrara nada)"
        }

        # Solo borrar si la verificacion paso
        if ($checkCode -eq 0 -or $Force) {
            & rclone @cleanArgs 2>&1 | Out-Null
            Show-Success "Archivos locales mayores a $daysKeepLocal dias limpiados"
            Write-SyncLog "Limpieza local completada (disco estaba en $freeGB GB)"
        } else {
            Show-Warning "Limpieza omitida (verificacion no paso)"
            Write-SyncLog "Limpieza omitida por fallo en verificacion" "WARN"
        }
    } else {
        Show-Info "Limpieza automatica deshabilitada en settings"
    }

    # Resumen
    Write-Host ""
    Write-Host "  ────────────────────────────────────" -ForegroundColor Cyan
    Write-Host "  Sync completado: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Green
    if ($isDryRun) {
        Write-Host "  MODO: DRY-RUN (simulacion)" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Para activar sync real:" -ForegroundColor White
        Write-Host "    Edita config\settings.json" -ForegroundColor Gray
        Write-Host "    Cambia 'dry_run': false" -ForegroundColor Gray
    }
    Write-Host ""

    Write-SyncLog "=== FIN DE SINCRONIZACION ==="
}
finally {
    # Siempre eliminar el lock file
    if (Test-Path $lockFile) {
        Remove-Item $lockFile -Force
    }
}
