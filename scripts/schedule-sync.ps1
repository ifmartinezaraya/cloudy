# ============================================================
# CloudVault - Programar Sincronizacion Automatica
# Uso: .\scripts\schedule-sync.ps1 [-Time "02:00"] [-Remove]
# ============================================================

param(
    [string]$Time = "",
    [switch]$Remove
)

$ROOT = Split-Path -Parent $PSScriptRoot

. (Join-Path $ROOT "scripts\lib\common.ps1")
. (Join-Path $ROOT "scripts\lib\logger.ps1")

Initialize-Logger
Assert-Administrator

$settings = Get-CloudVaultSettings
$taskName = $settings.sync.task_name

if ([string]::IsNullOrEmpty($Time)) {
    $Time = $settings.sync.schedule
}

Show-Banner "PROGRAMAR SINCRONIZACION AUTOMATICA"

if ($Remove) {
    Show-Info "Eliminando tarea programada..."
    schtasks /delete /tn $taskName /f 2>&1 | Out-Null
    Show-Success "Tarea '$taskName' eliminada"
    Write-Log -Level "INFO" -Message "Tarea sync eliminada" -Component "Schedule"
    exit 0
}

# Verificar si ya existe
$existing = schtasks /query /tn $taskName 2>&1
if ($LASTEXITCODE -eq 0) {
    Show-Warning "Ya existe una tarea '$taskName'"
    if (-not (Confirm-Action "Deseas reemplazarla?")) {
        exit 0
    }
    schtasks /delete /tn $taskName /f 2>&1 | Out-Null
}

# Crear script wrapper (para que Task Scheduler ejecute PowerShell)
$wrapperScript = Join-Path $ROOT "scripts\_sync-wrapper.ps1"
$wrapperContent = @"
# Auto-generado por CloudVault - No editar
Set-Location "$ROOT"
& "$ROOT\scripts\sync-cloud.ps1"
"@
Set-Content $wrapperScript $wrapperContent -Encoding UTF8

# Crear tarea
$action = "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$wrapperScript`""

schtasks /create `
    /tn $taskName `
    /tr $action `
    /sc daily `
    /st $Time `
    /rl HIGHEST `
    /f

if ($LASTEXITCODE -eq 0) {
    Show-Success "Tarea programada creada!"
    Write-Host ""
    Write-Host "  Nombre:    $taskName" -ForegroundColor White
    Write-Host "  Horario:   Todos los dias a las $Time" -ForegroundColor White
    Write-Host "  Script:    $wrapperScript" -ForegroundColor White
    Write-Host ""
    Write-Host "  Para ejecutar ahora:" -ForegroundColor Gray
    Write-Host "    schtasks /run /tn `"$taskName`"" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Para cambiar la hora:" -ForegroundColor Gray
    Write-Host "    .\scripts\schedule-sync.ps1 -Time `"03:30`"" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Para eliminar:" -ForegroundColor Gray
    Write-Host "    .\scripts\schedule-sync.ps1 -Remove" -ForegroundColor Gray
    Write-Host ""

    Write-Log -Level "INFO" -Message "Tarea sync programada: $Time diario" -Component "Schedule"
} else {
    Show-Error "No se pudo crear la tarea. Verifica permisos de administrador."
}
