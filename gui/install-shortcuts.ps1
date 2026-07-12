# CloudVault - Instalar Accesos Directos
# Crea accesos directos en Escritorio, Menu Inicio y Carpeta de Inicio
#
# Uso:
#   .\install-shortcuts.ps1 [-Desktop] [-Startup] [-StartMenu] [-All]

param(
    [switch]$Desktop,
    [switch]$Startup,
    [switch]$StartMenu,
    [switch]$All,
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallPath = Split-Path -Parent $ScriptDir

Write-Host "" -ForegroundColor Magenta
Write-Host "  CloudVault - Accesos Directos" -ForegroundColor Magenta
Write-Host "  =============================" -ForegroundColor Magenta
Write-Host ""

# Determinar target (exe o python)
$ExePath = Join-Path $ScriptDir "dist\CloudVault.exe"
$IconPath = Join-Path $ScriptDir "assets\cloud.ico"
$AppPy = Join-Path $ScriptDir "app.py"

if (Test-Path $ExePath) {
    $Target = $ExePath
    $Arguments = ""
    Write-Host "  [OK] Usando ejecutable: $ExePath" -ForegroundColor Green
} else {
    $Target = "python.exe"
    $Arguments = "`"$AppPy`""
    Write-Host "  [i] Ejecutable no encontrado. Usando: python $AppPy" -ForegroundColor Cyan
    Write-Host "      (Ejecuta build.exe.ps1 primero para crear el .exe)" -ForegroundColor Gray
}

# Funciones helper
function New-Shortcut {
    param(
        [string]$ShortcutPath,
        [string]$TargetPath,
        [string]$Arguments = "",
        [string]$Description = "CloudVault - Nube Personal Cifrada",
        [string]$IconLocation = "",
        [string]$WorkingDir = ""
    )

    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $TargetPath
    $Shortcut.Arguments = $Arguments
    $Shortcut.Description = $Description
    $Shortcut.WorkingDirectory = if ($WorkingDir) { $WorkingDir } else { $InstallPath }
    if ($IconLocation -and (Test-Path $IconLocation)) {
        $Shortcut.IconLocation = "$IconLocation,0"
    }
    $Shortcut.Save()
}

# Si no se especifico nada, preguntar
if (-not ($Desktop -or $Startup -or $StartMenu -or $All -or $Remove)) {
    $All = $true
}

if ($Remove) {
    Write-Host "  Eliminando accesos directos..." -ForegroundColor Yellow
    
    $paths = @(
        [System.IO.Path]::Combine([Environment]::GetFolderPath("Desktop"), "CloudVault.lnk"),
        [System.IO.Path]::Combine([Environment]::GetFolderPath("Startup"), "CloudVault.lnk"),
        [System.IO.Path]::Combine([Environment]::GetFolderPath("Programs"), "CloudVault", "CloudVault.lnk")
    )
    
    foreach ($p in $paths) {
        if (Test-Path $p) {
            Remove-Item $p -Force
            Write-Host "    [OK] Eliminado: $p" -ForegroundColor Green
        }
    }
    
    # Eliminar carpeta si esta vacia
    $folder = [System.IO.Path]::Combine([Environment]::GetFolderPath("Programs"), "CloudVault")
    if ((Test-Path $folder) -and (Get-ChildItem $folder).Count -eq 0) {
        Remove-Item $folder -Force
    }
    
    Write-Host ""
    Write-Host "  Accesos directos eliminados." -ForegroundColor Green
    exit 0
}

# Crear accesos directos
if ($All -or $Desktop) {
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $shortcutFile = Join-Path $desktopPath "CloudVault.lnk"
    New-Shortcut -ShortcutPath $shortcutFile -TargetPath $Target `
        -Arguments $Arguments -IconLocation $IconPath
    Write-Host "  [OK] Escritorio: $shortcutFile" -ForegroundColor Green
}

if ($All -or $Startup) {
    $startupPath = [Environment]::GetFolderPath("Startup")
    $shortcutFile = Join-Path $startupPath "CloudVault.lnk"
    New-Shortcut -ShortcutPath $shortcutFile -TargetPath $Target `
        -Arguments $Arguments -IconLocation $IconPath
    Write-Host "  [OK] Inicio automatico: $shortcutFile" -ForegroundColor Green
}

if ($All -or $StartMenu) {
    $programsPath = [Environment]::GetFolderPath("Programs")
    $folder = Join-Path $programsPath "CloudVault"
    if (-not (Test-Path $folder)) { New-Item -ItemType Directory -Path $folder -Force | Out-Null }
    $shortcutFile = Join-Path $folder "CloudVault.lnk"
    New-Shortcut -ShortcutPath $shortcutFile -TargetPath $Target `
        -Arguments $Arguments -IconLocation $IconPath
    Write-Host "  [OK] Menu Inicio: $shortcutFile" -ForegroundColor Green
}

Write-Host ""
Write-Host "  Accesos directos creados!" -ForegroundColor Green
Write-Host ""
Write-Host "  Ahora puedes:" -ForegroundColor White
Write-Host "    - Abrir CloudVault desde el escritorio" -ForegroundColor Gray
Write-Host "    - Se iniciara automaticamente con Windows" -ForegroundColor Gray
Write-Host "    - Buscarlo en el Menu Inicio" -ForegroundColor Gray
Write-Host ""
Write-Host "  Para eliminar: .\install-shortcuts.ps1 -Remove" -ForegroundColor Gray
Write-Host ""
