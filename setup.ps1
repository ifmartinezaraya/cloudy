# ============================================================
# CloudVault - Instalador Principal
# Ejecutar como: powershell -ExecutionPolicy RemoteSigned .\setup.ps1
# ============================================================

#Requires -Version 5.1

param(
    [switch]$Unattended,
    [string]$ConfigFile = ""
)

$ErrorActionPreference = "Stop"
$CLOUDVAULT_ROOT = $PSScriptRoot

# Cargar librerias
. (Join-Path $CLOUDVAULT_ROOT "scripts\lib\common.ps1")
. (Join-Path $CLOUDVAULT_ROOT "scripts\lib\logger.ps1")

# --- BANNER ---
Clear-Host
Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║                                                          ║" -ForegroundColor Cyan
Write-Host "  ║            CLOUDVAULT - INSTALADOR v1.0                  ║" -ForegroundColor Cyan
Write-Host "  ║         Tu Nube Personal Cifrada de Fotos                ║" -ForegroundColor Cyan
Write-Host "  ║                                                          ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Este asistente configurara:" -ForegroundColor White
Write-Host "    - Immich (servidor de fotos inteligente)" -ForegroundColor Gray
Write-Host "    - Cifrado AES-256 para almacenamiento en nube" -ForegroundColor Gray
Write-Host "    - Sincronizacion automatica a Mega/Google/OneDrive" -ForegroundColor Gray
Write-Host "    - Respaldo automatico desde tu iPhone" -ForegroundColor Gray
Write-Host ""
Write-Host "  Tiempo estimado: 15-30 minutos" -ForegroundColor Yellow
Write-Host ""

# --- PRE-CHECKS ---
Show-Banner "VERIFICACION DEL SISTEMA"

# 1. Verificar administrador
Show-Step 1 6 "Permisos de administrador..."
if (-not (Test-Administrator)) {
    Show-Error "Necesitas ejecutar como Administrador"
    Show-Info "Clic derecho en PowerShell > 'Ejecutar como administrador'"
    exit 1
}
Show-Success "Permisos OK"

# 2. Verificar version de Windows
Show-Step 2 6 "Version de Windows..."
$osVersion = [System.Environment]::OSVersion.Version
if ($osVersion.Major -lt 10) {
    Show-Error "Se requiere Windows 10 o superior"
    exit 1
}
$osBuild = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion" -ErrorAction SilentlyContinue).CurrentBuild
Show-Success "Windows Build $osBuild"

# 3. Verificar espacio
Show-Step 3 6 "Espacio en disco..."
$freeGB = Get-DiskFreeSpaceGB
if ($freeGB -lt 30) {
    Show-Warning "Solo tienes $freeGB GB libres. Se recomiendan al menos 30 GB."
    if (-not $Unattended) {
        if (-not (Confirm-Action "Deseas continuar de todas formas?")) {
            exit 0
        }
    }
} else {
    Show-Success "$freeGB GB libres"
}

# 4. Verificar RAM
Show-Step 4 6 "Memoria RAM..."
$ramGB = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
if ($ramGB -lt 4) {
    Show-Warning "Tienes $ramGB GB de RAM. Immich ML podria ser lento."
} else {
    Show-Success "$ramGB GB de RAM"
}

# 5. Verificar internet
Show-Step 5 6 "Conexion a internet..."
try {
    $null = Invoke-WebRequest -Uri "https://github.com" -TimeoutSec 10 -UseBasicParsing
    Show-Success "Internet OK"
}
catch {
    Show-Error "Sin conexion a internet. Se requiere para descargar componentes."
    exit 1
}

# 6. Verificar virtualizacion
Show-Step 6 6 "Virtualizacion (VT-x)..."
$virtEnabled = (Get-CimInstance Win32_Processor).VirtualizationFirmwareEnabled
if (-not $virtEnabled) {
    Show-Warning "Virtualizacion puede no estar habilitada en BIOS"
    Show-Info "Si Docker falla, activa 'Intel VT-x' o 'AMD-V' en la BIOS"
}
else {
    Show-Success "Virtualizacion habilitada"
}

Write-Host ""
Write-Host "  Sistema verificado correctamente!" -ForegroundColor Green
Write-Host ""

# --- CONFIGURACION INTERACTIVA ---
if (-not $Unattended) {
    Show-Banner "CONFIGURACION"

    # Zona horaria
    Write-Host "  Selecciona tu zona horaria:" -ForegroundColor White
    Write-Host "    1) Mexico       (America/Mexico_City)"
    Write-Host "    2) Colombia     (America/Bogota)"
    Write-Host "    3) Peru         (America/Lima)"
    Write-Host "    4) Chile        (America/Santiago)"
    Write-Host "    5) Argentina    (America/Argentina/Buenos_Aires)"
    Write-Host "    6) Espana       (Europe/Madrid)"
    Write-Host "    7) Otra (ingresarla manualmente)"
    Write-Host ""

    $tzChoice = Read-Host "  Opcion (1-7)"
    $timezone = switch ($tzChoice) {
        "1" { "America/Mexico_City" }
        "2" { "America/Bogota" }
        "3" { "America/Lima" }
        "4" { "America/Santiago" }
        "5" { "America/Argentina/Buenos_Aires" }
        "6" { "Europe/Madrid" }
        "7" { Read-Host "  Ingresa la zona horaria (ej: America/Lima)" }
        default { "America/Santiago" }
    }
    Write-Host "  Zona horaria: $timezone" -ForegroundColor Green
    Write-Host ""

    # Contrasena DB
    Write-Host "  Generando contrasena segura para la base de datos..." -ForegroundColor White
    $dbPassword = New-RandomPassword -Length 32
    Show-Success "Contrasena generada (se guardara en .env)"
    Write-Host ""

    # Puerto
    $port = Read-Host "  Puerto para Immich (Enter para 2283)"
    if ([string]::IsNullOrEmpty($port)) { $port = "2283" }
    Write-Host ""

    # Nubes
    Write-Host "  Que nubes gratuitas deseas usar?" -ForegroundColor White
    Write-Host "    Cada una requiere una cuenta gratis creada previamente." -ForegroundColor Gray
    Write-Host ""

    $useMega = Confirm-Action "Usar Mega.nz? (20 GB gratis)"
    $useGDrive = Confirm-Action "Usar Google Drive? (15 GB gratis)"
    $useOneDrive = Confirm-Action "Usar OneDrive? (5 GB gratis)"
    Write-Host ""

    if (-not ($useMega -or $useGDrive -or $useOneDrive)) {
        Show-Warning "No seleccionaste ninguna nube. Solo se guardara localmente."
        Show-Info "Puedes configurar nubes despues con: .\scripts\configure-cloud.ps1"
    }
}
else {
    # Valores por defecto para instalacion desatendida
    $timezone = "America/Santiago"
    $dbPassword = New-RandomPassword -Length 32
    $port = "2283"
    $useMega = $true
    $useGDrive = $true
    $useOneDrive = $true
}

# --- INSTALAR DEPENDENCIAS ---
Show-Banner "INSTALANDO DEPENDENCIAS"

# Docker Desktop
Show-Step 1 3 "Docker Desktop..."
$dockerInstalled = $null -ne (Get-Command docker -ErrorAction SilentlyContinue)
if ($dockerInstalled) {
    Show-Success "Docker ya esta instalado"
} else {
    Show-Info "Instalando Docker Desktop..."
    try {
        winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
        Show-Success "Docker instalado. REINICIA el PC y ejecuta setup.ps1 de nuevo."
        Show-Warning "Despues del reinicio, abre Docker Desktop y espera a que este listo."
        pause
        exit 0
    }
    catch {
        Show-Error "No se pudo instalar Docker automaticamente."
        Show-Info "Descargalo de: https://www.docker.com/products/docker-desktop/"
        pause
        exit 1
    }
}

# Verificar Docker corriendo
Show-Step 2 3 "Docker Engine..."
if (-not (Test-DockerRunning)) {
    Show-Warning "Docker no esta corriendo. Intentando iniciar..."
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Hidden
    $dockerReady = Wait-ForDocker -TimeoutSeconds 120
    if (-not $dockerReady) {
        Show-Error "Docker no se pudo iniciar. Abrelo manualmente y ejecuta setup.ps1 de nuevo."
        pause
        exit 1
    }
}
Show-Success "Docker Engine corriendo"

# Rclone
Show-Step 3 3 "Rclone..."
$rcloneInstalled = Test-RcloneInstalled
if ($rcloneInstalled) {
    Show-Success "Rclone ya esta instalado"
} else {
    Show-Info "Instalando Rclone..."
    try {
        winget install Rclone.Rclone --accept-package-agreements --accept-source-agreements
        # Refrescar PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        Show-Success "Rclone instalado"
    }
    catch {
        Show-Warning "No se pudo instalar Rclone con winget."
        Show-Info "Descargalo de: https://rclone.org/downloads/"
    }
}

# --- GENERAR ARCHIVOS DE CONFIGURACION ---
Show-Banner "GENERANDO CONFIGURACION"

# Crear estructura de carpetas
Show-Step 1 4 "Creando estructura de carpetas..."
$folders = @("upload", "upload\library", "upload\thumbs", "upload\profile", "postgres", "logs")
foreach ($folder in $folders) {
    $fullPath = Join-Path $CLOUDVAULT_ROOT $folder
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
    }
}
Show-Success "Carpetas creadas"

# Generar .env
Show-Step 2 4 "Generando archivo .env..."
$envContent = @"
# CloudVault - Generado automaticamente el $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# NO COMPARTAS ESTE ARCHIVO

IMMICH_VERSION=release
DB_PASSWORD=$dbPassword
DB_USERNAME=postgres
DB_DATABASE_NAME=immich
DB_DATA_LOCATION=./postgres
UPLOAD_LOCATION=./upload
IMMICH_PORT=$port
TZ=$timezone
MACHINE_LEARNING_ENABLED=true
"@

Set-Content -Path (Join-Path $CLOUDVAULT_ROOT "config\.env") -Value $envContent -Encoding UTF8
Show-Success "Archivo .env generado"

# Actualizar settings.json con las selecciones del usuario
Show-Step 3 4 "Actualizando configuracion..."
$settingsPath = Join-Path $CLOUDVAULT_ROOT "config\settings.json"
$settings = Get-Content $settingsPath -Raw | ConvertFrom-Json

# Actualizar providers habilitados
foreach ($provider in $settings.cloud.providers) {
    switch ($provider.name) {
        "mega"         { $provider.enabled = $useMega }
        "google-drive" { $provider.enabled = $useGDrive }
        "onedrive"     { $provider.enabled = $useOneDrive }
    }
}

$settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8
Show-Success "Configuracion actualizada"

# Copiar docker-compose al directorio raiz (Docker lo necesita ahi)
Show-Step 4 4 "Preparando Docker Compose..."
Copy-Item (Join-Path $CLOUDVAULT_ROOT "config\docker-compose.yml") (Join-Path $CLOUDVAULT_ROOT "docker-compose.yml") -Force
Copy-Item (Join-Path $CLOUDVAULT_ROOT "config\.env") (Join-Path $CLOUDVAULT_ROOT ".env") -Force
Show-Success "Docker Compose listo"

# --- INICIAR IMMICH ---
Show-Banner "INICIANDO IMMICH"

Show-Info "Descargando imagenes de Docker (primera vez ~4 GB)..."
Show-Info "Esto puede tardar 5-15 minutos segun tu internet."
Write-Host ""

Set-Location $CLOUDVAULT_ROOT
docker compose pull

Show-Info "Iniciando servicios..."
docker compose up -d

Write-Host ""
Show-Info "Esperando a que Immich este listo..."
$attempts = 0
$maxAttempts = 30
$ready = $false

while ($attempts -lt $maxAttempts -and -not $ready) {
    Start-Sleep -Seconds 10
    $attempts++
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:${port}/api/server-info/ping" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) { $ready = $true }
    }
    catch {
        Write-Host "  Iniciando... (intento $attempts/$maxAttempts)" -ForegroundColor Gray
    }
}

if ($ready) {
    Show-Success "Immich esta corriendo!"
} else {
    Show-Warning "Immich esta iniciando (puede tardar un poco mas la primera vez)"
    Show-Info "Verifica en unos minutos: http://localhost:${port}"
}

# --- RESUMEN FINAL ---
$localIP = Get-LocalIPAddress

Show-Banner "INSTALACION COMPLETADA!"

Write-Host "  Tu CloudVault esta listo. Aqui tienes la informacion:" -ForegroundColor White
Write-Host ""
Write-Host "  ┌──────────────────────────────────────────────────────┐" -ForegroundColor Green
Write-Host "  │  ACCESO WEB                                          │" -ForegroundColor Green
Write-Host "  │                                                      │" -ForegroundColor Green
Write-Host "  │  Desde este PC:  http://localhost:${port}              │" -ForegroundColor Green
Write-Host "  │  Desde iPhone:   http://${localIP}:${port}        │" -ForegroundColor Green
Write-Host "  │                                                      │" -ForegroundColor Green
Write-Host "  │  1. Abre la URL en tu navegador                      │" -ForegroundColor Green
Write-Host "  │  2. Crea tu cuenta de administrador                  │" -ForegroundColor Green
Write-Host "  │  3. Descarga 'Immich' en tu iPhone                   │" -ForegroundColor Green
Write-Host "  │  4. Conecta con la URL del iPhone                    │" -ForegroundColor Green
Write-Host "  └──────────────────────────────────────────────────────┘" -ForegroundColor Green
Write-Host ""
Write-Host "  PROXIMOS PASOS:" -ForegroundColor Yellow
Write-Host "  ───────────────" -ForegroundColor Yellow

$nextSteps = @()
if ($useMega -or $useGDrive -or $useOneDrive) {
    $nextSteps += "Configura las nubes cifradas:  .\scripts\configure-cloud.ps1"
    $nextSteps += "Programa el sync automatico:   .\scripts\schedule-sync.ps1"
}
$nextSteps += "Configura transcodificacion:   Admin > Video Transcoding > H.265"
$nextSteps += "Ver estado del sistema:        .\scripts\status.ps1"

$i = 1
foreach ($step in $nextSteps) {
    Write-Host "    $i. $step" -ForegroundColor White
    $i++
}

Write-Host ""
Write-Host "  ARCHIVOS IMPORTANTES:" -ForegroundColor Yellow
Write-Host "  ─────────────────────" -ForegroundColor Yellow
Write-Host "    Config:    $CLOUDVAULT_ROOT\config\settings.json"
Write-Host "    Logs:      $CLOUDVAULT_ROOT\logs\"
Write-Host "    Fotos:     $CLOUDVAULT_ROOT\upload\"
Write-Host ""

# Inicializar logger
Initialize-Logger -LogDir $Script:LOG_DIR
Write-Log -Level "INFO" -Message "Instalacion completada exitosamente" -Component "Setup"

Write-Host "  Listo! Tu nube personal esta activa." -ForegroundColor Green
Write-Host ""
