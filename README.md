# CloudVault - Tu Nube Personal Cifrada

> Almacenamiento seguro, gratuito y profesional para fotos y videos desde iPhone.

## Que es CloudVault?

Un sistema modular que convierte tu notebook en un servidor de fotos/videos con:
- **Cifrado AES-256** en reposo y en transito
- **Sincronizacion automatica** a multiples nubes gratuitas
- **Acceso desde cualquier lugar** via VPN privada
- **Respaldo inteligente** que optimiza tu espacio en disco
- **Adaptable** a cualquier configuracion de hardware/red

## Arquitectura

```
┌─────────────┐    WiFi / Tailscale     ┌────────────────────────────────┐
│  iPhone 13  │ ───────────────────────► │     NOTEBOOK (CloudVault)      │
│  App Immich │                          │                                │
└─────────────┘                          │  ┌──────────────────────────┐  │
                                         │  │  Docker + Immich Server  │  │
                                         │  │  - Thumbnails            │  │
                                         │  │  - Base de datos         │  │
                                         │  │  - Machine Learning      │  │
                                         │  └───────────┬──────────────┘  │
                                         │              │                  │
                                         │  ┌───────────▼──────────────┐  │
                                         │  │  CloudSync Engine        │  │
                                         │  │  - Cifrado AES-256       │  │
                                         │  │  - Union de nubes        │  │
                                         │  │  - Verificacion          │  │
                                         │  └───────────┬──────────────┘  │
                                         └──────────────┼──────────────────┘
                                                        │
                          ┌─────────────────────────────┼────────────────────────┐
                          │                             │                          │
                 ┌────────▼───────┐          ┌─────────▼────────┐      ┌──────────▼───────┐
                 │   Mega (20GB)  │          │ Google Drive(15GB)│      │  OneDrive (5GB)  │
                 │   AES-256      │          │   AES-256         │      │    AES-256       │
                 └────────────────┘          └──────────────────┘      └──────────────────┘
```

## Estructura del Proyecto

```
cloudvault/
├── README.md                    # Este archivo
├── setup.ps1                    # Instalador principal (ejecutar primero)
├── config/
│   ├── settings.json            # Configuracion centralizada
│   ├── docker-compose.yml       # Servicios Immich
│   └── .env.template            # Template de variables de entorno
├── scripts/
│   ├── lib/
│   │   ├── common.ps1           # Funciones compartidas
│   │   ├── logger.ps1           # Sistema de logging
│   │   └── health.ps1           # Health checks
│   ├── install-dependencies.ps1 # Instala Docker, Rclone, etc.
│   ├── configure-cloud.ps1      # Configura nubes cifradas
│   ├── start-services.ps1       # Inicia todos los servicios
│   ├── stop-services.ps1        # Detiene servicios
│   ├── sync-cloud.ps1           # Sincronizacion a la nube
│   ├── schedule-sync.ps1        # Programa sincronizacion
│   ├── restore.ps1              # Restaurar desde la nube
│   ├── status.ps1               # Estado completo del sistema
│   └── uninstall.ps1            # Desinstalar limpiamente
├── templates/
│   └── rclone.conf.template     # Template de configuracion rclone
└── docs/
    ├── GUIA-RAPIDA.md           # Guia resumida
    ├── SEGURIDAD.md             # Documentacion de seguridad
    ├── TROUBLESHOOTING.md       # Solucion de problemas
    └── IPHONE-SETUP.md          # Configurar el iPhone
```

## Inicio Rapido

```powershell
# 1. Abrir PowerShell como Administrador
# 2. Navegar a la carpeta del proyecto
cd C:\CloudVault

# 3. Permitir ejecucion de scripts (una vez)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 4. Ejecutar el instalador
.\setup.ps1
```

El instalador te guiara interactivamente por todo el proceso.

## Comandos Disponibles

| Comando | Descripcion |
|---------|-------------|
| `.\setup.ps1` | Instalacion completa guiada |
| `.\scripts\start-services.ps1` | Iniciar CloudVault |
| `.\scripts\stop-services.ps1` | Detener CloudVault |
| `.\scripts\status.ps1` | Ver estado del sistema |
| `.\scripts\sync-cloud.ps1` | Sincronizar a la nube (manual) |
| `.\scripts\sync-cloud.ps1 -Force` | Forzar sync completo |
| `.\scripts\configure-cloud.ps1` | Reconfigurar nubes |
| `.\scripts\restore.ps1` | Restaurar desde backup |
| `.\scripts\uninstall.ps1` | Desinstalar todo |

## Requisitos

- Windows 10/11 (64-bit)
- 60 GB libres en disco (minimo) - Con 100+ GB se guardan originales locales
- Conexion a internet
- iPhone con iOS 16+

## Modos de operacion

CloudVault se adapta automaticamente segun tu espacio disponible:

| Disco libre | Modo | Comportamiento |
|-------------|------|----------------|
| 100+ GB | **Full Local** | Todo en disco + backup cifrado a nubes |
| 60-100 GB | **Hybrid** | Originales locales temporales, movidos a nube |
| < 60 GB | **Cloud-first** | Solo thumbnails locales, originales en nube |

Con **103 GB** disponibles operas en modo **Full Local**: tus fotos originales
viven en tu disco con acceso inmediato, y ademas se respaldan cifradas a la nube.

## Costos

**$0** - Todo el stack es open source y usa servicios gratuitos.

## Seguridad

- Cifrado AES-256 en todas las nubes
- Nombres de archivos cifrados
- Sin puertos expuestos a internet
- Autenticacion en todas las capas
- Logs de auditoria

## Licencia

Uso personal. Herramientas utilizadas bajo sus respectivas licencias open source.
