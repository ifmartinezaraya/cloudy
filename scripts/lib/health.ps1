# ============================================================
# CloudVault - Health Checks
# Monitoreo de salud de todos los componentes
# ============================================================

. (Join-Path $PSScriptRoot "common.ps1")
. (Join-Path $PSScriptRoot "logger.ps1")

function Invoke-HealthCheck {
    [CmdletBinding()]
    param(
        [switch]$Detailed,
        [switch]$Silent
    )

    $results = @{
        Timestamp  = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Overall    = "HEALTHY"
        Components = @{}
    }

    # --- Docker ---
    $dockerOk = Test-DockerRunning
    $results.Components["Docker"] = @{
        Status  = if ($dockerOk) { "OK" } else { "FAIL" }
        Message = if ($dockerOk) { "Docker Engine corriendo" } else { "Docker no esta corriendo" }
    }

    # --- Contenedores ---
    $containers = @("cloudvault_server", "cloudvault_ml", "cloudvault_redis", "cloudvault_db")
    foreach ($container in $containers) {
        $running = Test-ContainerRunning -ContainerName $container
        $healthy = Test-ContainerHealthy -ContainerName $container
        $status = if ($healthy) { "HEALTHY" } elseif ($running) { "RUNNING" } else { "DOWN" }

        $results.Components[$container] = @{
            Status  = $status
            Message = switch ($status) {
                "HEALTHY" { "Saludable" }
                "RUNNING" { "Corriendo (sin healthcheck o iniciando)" }
                "DOWN"    { "No esta corriendo" }
            }
        }

        if ($status -eq "DOWN") { $results.Overall = "DEGRADED" }
    }

    # --- Disco ---
    $freeGB = Get-DiskFreeSpaceGB
    $settings = Get-CloudVaultSettings
    $warnThreshold = $settings.health.disk_warning_threshold_percent
    $critThreshold = $settings.health.disk_critical_threshold_percent

    $disk = Get-PSDrive -Name C
    $usedPercent = [math]::Round(($disk.Used / ($disk.Used + $disk.Free)) * 100, 1)

    $diskStatus = "OK"
    if ($usedPercent -ge $critThreshold) { $diskStatus = "CRITICAL"; $results.Overall = "CRITICAL" }
    elseif ($usedPercent -ge $warnThreshold) { $diskStatus = "WARNING"; if ($results.Overall -ne "CRITICAL") { $results.Overall = "WARNING" } }

    $results.Components["Disco"] = @{
        Status   = $diskStatus
        Message  = "Libre: ${freeGB} GB | Uso: ${usedPercent}%"
        FreeGB   = $freeGB
        UsedPct  = $usedPercent
    }

    # --- Rclone ---
    $rcloneOk = Test-RcloneInstalled
    $results.Components["Rclone"] = @{
        Status  = if ($rcloneOk) { "OK" } else { "NOT_INSTALLED" }
        Message = if ($rcloneOk) { "Instalado" } else { "No instalado" }
    }

    # --- Nubes (si rclone esta disponible) ---
    if ($rcloneOk -and $Detailed) {
        $providers = $settings.cloud.providers
        foreach ($provider in $providers) {
            if ($provider.enabled) {
                $remoteExists = Test-RcloneRemoteExists -RemoteName $provider.crypt_name
                $results.Components["Nube:$($provider.name)"] = @{
                    Status  = if ($remoteExists) { "OK" } else { "NOT_CONFIGURED" }
                    Message = if ($remoteExists) { "Configurado" } else { "No configurado" }
                }
            }
        }
    }

    # --- Immich Web ---
    try {
        $port = $settings.immich.port
        $response = Invoke-WebRequest -Uri "http://localhost:${port}/api/server-info/ping" -TimeoutSec 5 -ErrorAction Stop
        $immichOk = $response.StatusCode -eq 200
    }
    catch {
        $immichOk = $false
    }

    $results.Components["Immich Web"] = @{
        Status  = if ($immichOk) { "OK" } else { "UNREACHABLE" }
        Message = if ($immichOk) { "Respondiendo en puerto $port" } else { "No responde" }
    }

    # --- Log del resultado ---
    if (-not $Silent) {
        Write-Log -Level "INFO" -Message "Health check: $($results.Overall)" -Component "Health"
    }

    # --- Determinar overall si alguno fallo ---
    $failCount = ($results.Components.Values | Where-Object { $_.Status -in @("FAIL", "DOWN", "CRITICAL") }).Count
    if ($failCount -gt 0 -and $results.Overall -eq "HEALTHY") {
        $results.Overall = "DEGRADED"
    }

    return $results
}

function Show-HealthReport {
    param([hashtable]$Health)

    $overallColor = switch ($Health.Overall) {
        "HEALTHY"  { "Green" }
        "WARNING"  { "Yellow" }
        "DEGRADED" { "Yellow" }
        "CRITICAL" { "Red" }
        default    { "Gray" }
    }

    Write-Host ""
    Write-Host "  Estado General: " -NoNewline
    Write-Host $Health.Overall -ForegroundColor $overallColor
    Write-Host "  Timestamp: $($Health.Timestamp)"
    Write-Host ""
    Write-Host "  Componente              Estado          Detalle" -ForegroundColor White
    Write-Host "  ────────────────────────────────────────────────────────────"

    foreach ($key in $Health.Components.Keys | Sort-Object) {
        $comp = $Health.Components[$key]
        $statusColor = switch ($comp.Status) {
            "OK"             { "Green" }
            "HEALTHY"        { "Green" }
            "RUNNING"        { "Cyan" }
            "WARNING"        { "Yellow" }
            "NOT_CONFIGURED" { "Gray" }
            "NOT_INSTALLED"  { "Gray" }
            default          { "Red" }
        }

        $paddedName = $key.PadRight(22)
        $paddedStatus = $comp.Status.PadRight(16)

        Write-Host "  $paddedName" -NoNewline
        Write-Host "$paddedStatus" -NoNewline -ForegroundColor $statusColor
        Write-Host $comp.Message
    }
    Write-Host ""
}

Export-ModuleMember -Function *
