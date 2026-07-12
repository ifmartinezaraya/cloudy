# Guia Rapida - CloudVault

## Instalacion (15-30 min)

### Prerequisitos
1. Instala [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Reinicia el PC
3. Abre Docker Desktop y espera a que este listo (icono verde)

### Instalar CloudVault
```powershell
# Abrir PowerShell como Administrador
cd C:\CloudVault
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup.ps1
```

Sigue las instrucciones interactivas. El instalador:
- Verifica tu sistema
- Instala dependencias faltantes
- Genera configuracion segura
- Descarga e inicia Immich
- Te muestra la URL de acceso

### Configurar nubes cifradas
```powershell
.\scripts\configure-cloud.ps1
```

### Programar sync automatico
```powershell
.\scripts\schedule-sync.ps1
```

### Conectar iPhone
1. Descarga "Immich" de App Store
2. Pon la URL que te mostro el instalador
3. Activa Backup automatico

## Uso Diario

| Accion | Comando |
|--------|---------|
| Iniciar | `.\scripts\start-services.ps1` |
| Detener | `.\scripts\stop-services.ps1` |
| Ver estado | `.\scripts\status.ps1` |
| Sync manual | `.\scripts\sync-cloud.ps1` |
| Restaurar | `.\scripts\restore.ps1` |

## Archivos Importantes

```
C:\CloudVault\
├── config\settings.json    ← Toda la configuracion
├── config\.env             ← Contrasenas (no compartir!)
├── logs\                   ← Logs de sync y sistema
└── upload\                 ← Fotos locales (temporales)
```

## Emergencia

Si algo falla:
```powershell
.\scripts\status.ps1 -Detailed    # Ver que falla
.\scripts\stop-services.ps1       # Detener
.\scripts\start-services.ps1      # Reiniciar
```

Si el notebook muere, tus fotos estan seguras en la nube.
Para recuperarlas en otro PC:
```powershell
.\scripts\restore.ps1
```
