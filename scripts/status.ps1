# ============================================================
# CloudVault - Estado del Sistema
# Uso: .\scripts\status.ps1 [-Detailed] [-Json]
# ============================================================

param(
    [switch]$Detailed,
    [switch]$Json
)

$ROOT = Split-Path -Parent $PSScriptRoot

. (Join-Path $ROOT "scripts\lib\common.ps1")
. (Join-Path $ROOT "scripts\lib\logger.ps1")
. (Join-Path $ROOT "scripts\lib\health.ps1")

Initialize-Logger

if (-not $Json) {
    Show-Banner "ESTADO DE CLOUDVAULT"
}

# Ejecutar health check
$health = Invoke-HealthCheck -Detailed:$Detailed -Silent:$Json

if ($Json) {
    $health | ConvertTo-Json -Depth 5
    exit 0
}

# Mostrar reporte visual
Show-HealthReport -Health $health

# Informacion adicional
$settings = Get-CloudVaultSettings
$localIP = Get-LocalIPAddress
$port = $settings.immich.port

Write-Host "  ACCESO" -ForegroundColor Yellow
Write-Host "  ──────" -ForegroundColor Yellow
Write-Host "    Web:     http://localhost:${port}"
Write-Host "    iPhone:  http://${localIP}:${port}"
Write-Host ""

# Espacio usado
$uploadPath = Join-Path $ROOT "upload"
if (Test-Path $uploadPath) {
    $uploadSize = Get-FolderSizeGB -Path $uploadPath
    $maxLocal = $settings.storage.max_local_usage_gb
    $usagePct = [math]::Round(($uploadSize / $maxLocal) * 100, 1)

    Write-Host "  ALMACENAMIENTO LOCAL" -ForegroundColor Yellow
    Write-Host "  ────────────────────" -ForegroundColor Yellow
    Write-Host "    Fotos/Videos: $uploadSize GB / $maxLocal GB ($usagePct%)"

    # Barra visual
    $barWidth = 40
    $filledWidth = [math]::Min([math]::Round($usagePct / 100 * $barWidth), $barWidth)
    $emptyWidth = $barWidth - $filledWidth
    $barColor = if ($usagePct -ge 90) { "Red" } elseif ($usagePct -ge 70) { "Yellow" } else { "Green" }

    Write-Host "    [" -NoNewline
    Write-Host ("█" * $filledWidth) -NoNewline -ForegroundColor $barColor
    Write-Host ("░" * $emptyWidth) -NoNewline
    Write-Host "]"
    Write-Host ""
}

# Ultimo sync
$logsDir = Join-Path $ROOT "logs"
if (Test-Path $logsDir) {
    $lastSync = Get-ChildItem $logsDir -Filter "sync-*.log" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1

    Write-Host "  ULTIMA SINCRONIZACION" -ForegroundColor Yellow
    Write-Host "  ─────────────────────" -ForegroundColor Yellow

    if ($lastSync) {
        $lastSyncTime = $lastSync.LastWriteTime
        $ago = (Get-Date) - $lastSyncTime
        $agoStr = if ($ago.TotalHours -lt 1) { "$([math]::Round($ago.TotalMinutes)) min" }
                  elseif ($ago.TotalDays -lt 1) { "$([math]::Round($ago.TotalHours, 1)) horas" }
                  else { "$([math]::Round($ago.TotalDays, 1)) dias" }

        Write-Host "    Ultimo: $($lastSyncTime.ToString('yyyy-MM-dd HH:mm')) (hace $agoStr)"

        # Ultima linea del log
        $lastLine = Get-Content $lastSync.FullName -Tail 3 | Where-Object { $_ -match "===" } | Select-Object -Last 1
        if ($lastLine) {
            Write-Host "    Estado: $lastLine" -ForegroundColor Gray
        }
    } else {
        Write-Host "    No se ha ejecutado ninguna sincronizacion aun." -ForegroundColor Gray
    }
    Write-Host ""
}

# Tarea programada
Write-Host "  SYNC PROGRAMADO" -ForegroundColor Yellow
Write-Host "  ───────────────" -ForegroundColor Yellow
$taskName = $settings.sync.task_name
$taskInfo = schtasks /query /tn $taskName /fo csv 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "    Tarea: $taskName" -ForegroundColor Green
    Write-Host "    Horario: Diario a las $($settings.sync.schedule)"
    $dryRunStatus = if ($settings.sync.dry_run) { "SIMULACION (dry-run)" } else { "ACTIVO" }
    Write-Host "    Modo: $dryRunStatus"
} else {
    Write-Host "    No programado" -ForegroundColor Gray
    Write-Host "    Ejecuta: .\scripts\schedule-sync.ps1" -ForegroundColor Gray
}
Write-Host ""
