# ============================================================
# CloudVault - Configurar Nubes Cifradas
# Uso: .\scripts\configure-cloud.ps1 [-Provider mega|gdrive|onedrive]
# ============================================================

param(
    [ValidateSet("mega", "gdrive", "onedrive", "all")]
    [string]$Provider = "all"
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot

. (Join-Path $ROOT "scripts\lib\common.ps1")
. (Join-Path $ROOT "scripts\lib\logger.ps1")

Initialize-Logger
Show-Banner "CONFIGURAR ALMACENAMIENTO EN NUBE CIFRADO"

# Verificar rclone
if (-not (Test-RcloneInstalled)) {
    Show-Error "Rclone no esta instalado."
    Show-Info "Ejecuta: winget install Rclone.Rclone"
    exit 1
}
Show-Success "Rclone detectado"

# Cargar settings
$settings = Get-CloudVaultSettings
$providers = $settings.cloud.providers

Write-Host ""
Write-Host "  Se configuraran las nubes con cifrado:" -ForegroundColor White
Write-Host "    Algoritmo: AES-256" -ForegroundColor Gray
Write-Host "    Nombres de archivo: Cifrados" -ForegroundColor Gray
Write-Host "    Nombres de carpeta: Cifrados" -ForegroundColor Gray
Write-Host ""

# Pedir contrasena maestra de cifrado
Write-Host "  CONTRASENA DE CIFRADO" -ForegroundColor Yellow
Write-Host "  ─────────────────────" -ForegroundColor Yellow
Write-Host "  Esta contrasena protege TODAS tus fotos." -ForegroundColor White
Write-Host "  Sin ella, tus archivos son IRRECUPERABLES." -ForegroundColor Red
Write-Host ""

$cryptPass = Read-Host "  Ingresa tu contrasena de cifrado" -AsSecureString
$cryptPassConfirm = Read-Host "  Confirma la contrasena" -AsSecureString

$pass1 = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($cryptPass))
$pass2 = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($cryptPassConfirm))

if ($pass1 -ne $pass2) {
    Show-Error "Las contrasenas no coinciden. Intenta de nuevo."
    exit 1
}

# Salt password (segunda capa)
$saltPass = New-RandomPassword -Length 16
Write-Host ""
Show-Info "Guardando configuracion de cifrado..."
Write-Host ""

# Configurar cada proveedor
$step = 1
$totalSteps = ($providers | Where-Object { $_.enabled }).Count + 1

foreach ($prov in $providers) {
    if (-not $prov.enabled) { continue }
    if ($Provider -ne "all" -and $prov.name -notlike "*$Provider*") { continue }

    Show-Step $step $totalSteps "Configurando $($prov.name)..."

    switch ($prov.type) {
        "mega" {
            Write-Host "    Email de Mega.nz: " -NoNewline
            $megaUser = Read-Host
            $megaPass = Read-Host "    Contrasena de Mega.nz" -AsSecureString
            $megaPassPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
                [Runtime.InteropServices.Marshal]::SecureStringToBSTR($megaPass))

            # Crear remote raw
            $env:RCLONE_CONFIG_MEGA_RAW_TYPE = "mega"
            rclone config create $prov.remote_name mega `
                user $megaUser pass $megaPassPlain 2>&1 | Out-Null
        }
        "drive" {
            Show-Info "Se abrira el navegador para autorizar Google Drive..."
            rclone config create $prov.remote_name drive 2>&1 | Out-Null
        }
        "onedrive" {
            Show-Info "Se abrira el navegador para autorizar OneDrive..."
            rclone config create $prov.remote_name onedrive 2>&1 | Out-Null
        }
    }

    # Crear capa de cifrado
    $remotePath = "$($prov.remote_name):$($prov.folder)"
    rclone config create $prov.crypt_name crypt `
        remote $remotePath `
        filename_encryption standard `
        directory_name_encryption true `
        password $pass1 `
        password2 $saltPass 2>&1 | Out-Null

    Show-Success "$($prov.name) configurado con cifrado AES-256"
    $step++
}

# Crear union
Show-Step $step $totalSteps "Creando union de nubes..."
$upstreams = ($providers | Where-Object { $_.enabled } |
    ForEach-Object { "$($_.crypt_name):" }) -join " "

$unionName = $settings.cloud.union_name
rclone config create $unionName union `
    upstreams $upstreams `
    action_policy $settings.cloud.union_policy.action `
    create_policy $settings.cloud.union_policy.create `
    search_policy $settings.cloud.union_policy.search 2>&1 | Out-Null

Show-Success "Union '$unionName' creada"

# Verificar
Write-Host ""
Show-Info "Verificando conexion a las nubes..."
$verifyOk = $true

foreach ($prov in $providers) {
    if (-not $prov.enabled) { continue }
    try {
        rclone lsd "$($prov.crypt_name):" 2>&1 | Out-Null
        Write-Host "    [OK] $($prov.name)" -ForegroundColor Green
    }
    catch {
        Write-Host "    [!!] $($prov.name) - fallo" -ForegroundColor Red
        $verifyOk = $false
    }
}

Write-Host ""
if ($verifyOk) {
    Show-Success "Todas las nubes configuradas correctamente!"
    Write-Host ""
    Write-Host "  Espacio total disponible (cifrado):" -ForegroundColor White
    $totalGB = ($providers | Where-Object { $_.enabled } |
        Measure-Object -Property capacity_gb -Sum).Sum
    Write-Host "    ~$totalGB GB distribuidos en $($providers.Count) nubes" -ForegroundColor Cyan
} else {
    Show-Warning "Algunas nubes no se pudieron verificar."
    Show-Info "Ejecuta este script de nuevo para los que fallaron."
}

Write-Host ""
Show-Info "IMPORTANTE: Guarda tu contrasena de cifrado en un lugar seguro!"
Show-Info "Sin ella, tus fotos seran IRRECUPERABLES."
Write-Host ""

Write-Log -Level "INFO" -Message "Nubes cifradas configuradas" -Component "Cloud"
