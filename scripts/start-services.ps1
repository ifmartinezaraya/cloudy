# ============================================================
# CloudVault - Iniciar Servicios
# Uso: .\scripts\start-services.ps1 [-WaitForHealthy] [-Quiet]
# ============================================================

param(
    [switch]$WaitForHealthy,
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot

# Cargar librerias
. (Join-Path $ROOT "scripts\lib\common.ps1")
. (Join-Path $ROOT "scripts\lib\logger.ps1")

Initialize-Logger

if (-not $Quiet) {
    Show-Banner "INICIANDO CLOUDVAULT"
}

# 1. Verificar Docker
if (-not $Quiet) { Show-Step 1 4 "Verificando Docker..." }
if (-not (Test-DockerRunning)) {
    if (-not $Quiet) { Show-Info "Docker no esta corriendo. Intentando iniciar..." }

    # Intentar iniciar Docker Desktop
    $dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerPath) {
        Start-Process $dockerPath -WindowStyle Hidden
    }

    $ready = Wait-ForDocker -TimeoutSeconds 120
    if (-not $ready) {
        Show-Error "Docker no se pudo iniciar. Abrelo manualmente."
        Write-Log -Level "ERROR" -Message "Docker no disponible al intentar iniciar servicios" -Component "Start"
        exit 1
    }
}
if (-not $Quiet) { Show-Success "Docker OK" }

# 2. Verificar archivos necesarios
if (-not $Quiet) { Show-Step 2 4 "Verificando configuracion..." }
$composeFile = Join-Path $ROOT "docker-compose.yml"
$envFile = Join-Path $ROOT ".env"

if (-not (Test-Path $composeFile)) {
    # Copiar desde config si no existe en raiz
    $configCompose = Join-Path $ROOT "config\docker-compose.yml"
    if (Test-Path $configCompose) {
        Copy-Item $configCompose $composeFile
    } else {
        Show-Error "docker-compose.yml no encontrado. Ejecuta setup.ps1 primero."
        exit 1
    }
}
if (-not (Test-Path $envFile)) {
    $configEnv = Join-Path $ROOT "config\.env"
    if (Test-Path $configEnv) {
        Copy-Item $configEnv $envFile
    } else {
        Show-Error ".env no encontrado. Ejecuta setup.ps1 primero."
        exit 1
    }
}
if (-not $Quiet) { Show-Success "Configuracion OK" }

# 3. Iniciar servicios
if (-not $Quiet) { Show-Step 3 4 "Iniciando contenedores..." }
Set-Location $ROOT
docker compose up -d 2>&1 | ForEach-Object {
    if (-not $Quiet) { Write-Host "    $_" -ForegroundColor Gray }
}

if ($LASTEXITCODE -ne 0) {
    Show-Error "Error al iniciar contenedores"
    Write-Log -Level "ERROR" -Message "docker compose up fallo con codigo $LASTEXITCODE" -Component "Start"
    exit 1
}
if (-not $Quiet) { Show-Success "Contenedores iniciados" }

# 4. Esperar a que este saludable (opcional)
if ($WaitForHealthy -or (-not $Quiet)) {
    if (-not $Quiet) { Show-Step 4 4 "Esperando que los servicios esten listos..." }

    $settings = Get-CloudVaultSettings
    $port = $settings.immich.port
    $maxWait = 180  # 3 minutos
    $elapsed = 0
    $ready = $false

    while ($elapsed -lt $maxWait -and -not $ready) {
        Start-Sleep -Seconds 5
        $elapsed += 5
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:${port}/api/server-info/ping" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
            if ($response.StatusCode -eq 200) { $ready = $true }
        }
        catch {}
        if (-not $ready -and -not $Quiet -and ($elapsed % 15 -eq 0)) {
            Write-Host "    Todavia iniciando... ($elapsed s)" -ForegroundColor Gray
        }
    }

    if ($ready) {
        if (-not $Quiet) { Show-Success "Immich respondiendo en puerto $port" }
    } else {
        if (-not $Quiet) { Show-Warning "Immich aun no responde (puede tardar mas la primera vez)" }
    }
}

# Resultado final
$localIP = Get-LocalIPAddress
$port = (Get-CloudVaultSettings).immich.port

if (-not $Quiet) {
    Write-Host ""
    Write-Host "  CloudVault esta corriendo!" -ForegroundColor Green
    Write-Host ""
    Write-Host "    Local:   http://localhost:${port}" -ForegroundColor White
    Write-Host "    iPhone:  http://${localIP}:${port}" -ForegroundColor White
    Write-Host ""
}

Write-Log -Level "INFO" -Message "Servicios iniciados correctamente" -Component "Start"
