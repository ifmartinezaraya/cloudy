# ============================================================
# CloudVault - Sistema de Logging
# Logs rotativos con niveles, timestamps y exportacion
# ============================================================

$Script:LOG_DIR = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "logs"
$Script:LOG_LEVELS = @{ DEBUG = 0; INFO = 1; WARN = 2; ERROR = 3; FATAL = 4 }
$Script:CURRENT_LOG_LEVEL = "INFO"
$Script:MAX_LOG_SIZE_MB = 10
$Script:MAX_LOG_FILES = 30

function Initialize-Logger {
    param(
        [string]$LogLevel = "INFO",
        [string]$LogDir = $Script:LOG_DIR
    )

    $Script:LOG_DIR = $LogDir
    $Script:CURRENT_LOG_LEVEL = $LogLevel

    if (-not (Test-Path $Script:LOG_DIR)) {
        New-Item -ItemType Directory -Path $Script:LOG_DIR -Force | Out-Null
    }

    # Rotar logs viejos
    Invoke-LogRotation
}

function Write-Log {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateSet("DEBUG", "INFO", "WARN", "ERROR", "FATAL")]
        [string]$Level,

        [Parameter(Mandatory)]
        [string]$Message,

        [string]$Component = "General",
        [string]$LogFile = ""
    )

    # Verificar nivel minimo
    if ($Script:LOG_LEVELS[$Level] -lt $Script:LOG_LEVELS[$Script:CURRENT_LOG_LEVEL]) {
        return
    }

    # Crear directorio si no existe
    if (-not (Test-Path $Script:LOG_DIR)) {
        New-Item -ItemType Directory -Path $Script:LOG_DIR -Force | Out-Null
    }

    # Determinar archivo de log
    if ([string]::IsNullOrEmpty($LogFile)) {
        $LogFile = Join-Path $Script:LOG_DIR "cloudvault-$(Get-Date -Format 'yyyy-MM-dd').log"
    }

    # Formato del log
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    $entry = "[$timestamp] [$Level] [$Component] $Message"

    # Escribir al archivo
    Add-Content -Path $LogFile -Value $entry -Encoding UTF8

    # Tambien mostrar en consola si es WARN+
    switch ($Level) {
        "WARN"  { Write-Host "  [WARN] $Message" -ForegroundColor Yellow }
        "ERROR" { Write-Host "  [ERROR] $Message" -ForegroundColor Red }
        "FATAL" { Write-Host "  [FATAL] $Message" -ForegroundColor DarkRed }
    }
}

function Write-SyncLog {
    param(
        [Parameter(Mandatory)]
        [string]$Message,

        [string]$Level = "INFO"
    )

    $logFile = Join-Path $Script:LOG_DIR "sync-$(Get-Date -Format 'yyyy-MM-dd').log"
    Write-Log -Level $Level -Message $Message -Component "Sync" -LogFile $logFile
}

function Invoke-LogRotation {
    if (-not (Test-Path $Script:LOG_DIR)) { return }

    # Eliminar logs mayores a MAX_LOG_FILES dias
    $cutoffDate = (Get-Date).AddDays(-$Script:MAX_LOG_FILES)
    Get-ChildItem -Path $Script:LOG_DIR -Filter "*.log" |
        Where-Object { $_.LastWriteTime -lt $cutoffDate } |
        Remove-Item -Force

    # Comprimir logs mayores a MAX_LOG_SIZE_MB
    Get-ChildItem -Path $Script:LOG_DIR -Filter "*.log" |
        Where-Object { $_.Length -gt ($Script:MAX_LOG_SIZE_MB * 1MB) } |
        ForEach-Object {
            $archiveName = $_.FullName + ".zip"
            if (-not (Test-Path $archiveName)) {
                Compress-Archive -Path $_.FullName -DestinationPath $archiveName -Force
                Remove-Item $_.FullName -Force
            }
        }
}

function Get-RecentLogs {
    param(
        [int]$Lines = 50,
        [string]$Level = "INFO",
        [string]$Component = ""
    )

    $todayLog = Join-Path $Script:LOG_DIR "cloudvault-$(Get-Date -Format 'yyyy-MM-dd').log"

    if (-not (Test-Path $todayLog)) {
        Write-Host "  No hay logs de hoy." -ForegroundColor Gray
        return
    }

    $logs = Get-Content $todayLog -Tail $Lines

    if (-not [string]::IsNullOrEmpty($Component)) {
        $logs = $logs | Where-Object { $_ -match "\[$Component\]" }
    }

    $minLevel = $Script:LOG_LEVELS[$Level]
    $logs | Where-Object {
        $_ -match '\[(DEBUG|INFO|WARN|ERROR|FATAL)\]' -and
        $Script:LOG_LEVELS[$Matches[1]] -ge $minLevel
    }
}

Export-ModuleMember -Function *
