# ============================================================
# CloudVault - Funciones Comunes
# Libreria compartida por todos los scripts
# ============================================================

# --- Configuracion global ---
$Script:CLOUDVAULT_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Script:SETTINGS_FILE = Join-Path $CLOUDVAULT_ROOT "config\settings.json"
$Script:ENV_FILE = Join-Path $CLOUDVAULT_ROOT "config\.env"
$Script:LOG_DIR = Join-Path $CLOUDVAULT_ROOT "logs"

# --- Cargar configuracion ---
function Get-CloudVaultSettings {
    [CmdletBinding()]
    param()

    if (-not (Test-Path $Script:SETTINGS_FILE)) {
        Write-Error "Archivo de configuracion no encontrado: $Script:SETTINGS_FILE"
        Write-Error "Ejecuta setup.ps1 primero."
        exit 1
    }

    $settings = Get-Content $Script:SETTINGS_FILE -Raw | ConvertFrom-Json
    return $settings
}

function Get-Setting {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Path
    )

    $settings = Get-CloudVaultSettings
    $parts = $Path -split '\.'
    $current = $settings

    foreach ($part in $parts) {
        if ($null -eq $current.$part) {
            return $null
        }
        $current = $current.$part
    }

    return $current
}

function Set-Setting {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Path,
        [Parameter(Mandatory)]
        $Value
    )

    $settings = Get-CloudVaultSettings
    $json = $settings | ConvertTo-Json -Depth 10
    # Simple replacement for flat values
    Set-Content -Path $Script:SETTINGS_FILE -Value $json -Encoding UTF8
}

# --- Sistema ---
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Assert-Administrator {
    if (-not (Test-Administrator)) {
        Write-Host ""
        Write-Host "  ERROR: Este script requiere permisos de Administrador." -ForegroundColor Red
        Write-Host "  Clic derecho en PowerShell -> 'Ejecutar como administrador'" -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }
}

function Get-LocalIPAddress {
    $ip = (Get-NetIPAddress -AddressFamily IPv4 |
           Where-Object { $_.InterfaceAlias -notmatch "Loopback" -and $_.IPAddress -ne "127.0.0.1" } |
           Sort-Object -Property InterfaceMetric |
           Select-Object -First 1).IPAddress
    return $ip
}

function Get-DiskFreeSpaceGB {
    param([string]$Drive = "C")
    $disk = Get-PSDrive -Name $Drive -ErrorAction SilentlyContinue
    if ($disk) {
        return [math]::Round($disk.Free / 1GB, 2)
    }
    return 0
}

function Get-FolderSizeGB {
    param([string]$Path)
    if (Test-Path $Path) {
        $size = (Get-ChildItem -Path $Path -Recurse -ErrorAction SilentlyContinue |
                 Measure-Object -Property Length -Sum).Sum
        return [math]::Round($size / 1GB, 2)
    }
    return 0
}

# --- Docker ---
function Test-DockerRunning {
    try {
        $result = docker info 2>&1
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

function Wait-ForDocker {
    param([int]$TimeoutSeconds = 120)

    $elapsed = 0
    while (-not (Test-DockerRunning)) {
        if ($elapsed -ge $TimeoutSeconds) {
            return $false
        }
        Write-Host "  Esperando a Docker... ($elapsed s)" -ForegroundColor Gray
        Start-Sleep -Seconds 5
        $elapsed += 5
    }
    return $true
}

function Test-ContainerHealthy {
    param([string]$ContainerName)
    try {
        $status = docker inspect --format='{{.State.Health.Status}}' $ContainerName 2>&1
        return $status -eq "healthy"
    }
    catch {
        return $false
    }
}

function Test-ContainerRunning {
    param([string]$ContainerName)
    try {
        $status = docker inspect --format='{{.State.Running}}' $ContainerName 2>&1
        return $status -eq "true"
    }
    catch {
        return $false
    }
}

# --- Rclone ---
function Test-RcloneInstalled {
    try {
        $null = Get-Command rclone -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

function Test-RcloneRemoteExists {
    param([string]$RemoteName)
    if (-not (Test-RcloneInstalled)) { return $false }
    $remotes = rclone listremotes 2>&1
    return $remotes -match "^${RemoteName}:"
}

function Get-RcloneRemoteSpace {
    param([string]$RemoteName)
    try {
        $about = rclone about "${RemoteName}:" --json 2>&1 | ConvertFrom-Json
        return @{
            Total = [math]::Round($about.total / 1GB, 2)
            Used  = [math]::Round($about.used / 1GB, 2)
            Free  = [math]::Round($about.free / 1GB, 2)
        }
    }
    catch {
        return $null
    }
}

# --- Utilidades ---
function New-RandomPassword {
    param([int]$Length = 24)
    $chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&*'
    $password = -join (1..$Length | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })
    return $password
}

function Format-FileSize {
    param([long]$Bytes)
    if ($Bytes -ge 1GB) { return "{0:N2} GB" -f ($Bytes / 1GB) }
    if ($Bytes -ge 1MB) { return "{0:N2} MB" -f ($Bytes / 1MB) }
    if ($Bytes -ge 1KB) { return "{0:N2} KB" -f ($Bytes / 1KB) }
    return "$Bytes B"
}

function Show-Banner {
    param([string]$Title)
    $line = "=" * 60
    Write-Host ""
    Write-Host "  $line" -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor White
    Write-Host "  $line" -ForegroundColor Cyan
    Write-Host ""
}

function Show-Step {
    param(
        [int]$Number,
        [int]$Total,
        [string]$Message
    )
    Write-Host "  [$Number/$Total] $Message" -ForegroundColor Green
}

function Show-Success {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Show-Warning {
    param([string]$Message)
    Write-Host "  [!!] $Message" -ForegroundColor Yellow
}

function Show-Error {
    param([string]$Message)
    Write-Host "  [ERROR] $Message" -ForegroundColor Red
}

function Show-Info {
    param([string]$Message)
    Write-Host "  [i] $Message" -ForegroundColor Cyan
}

function Confirm-Action {
    param([string]$Message)
    $response = Read-Host "  $Message (S/N)"
    return $response -match '^[Ss]'
}

Export-ModuleMember -Function *
