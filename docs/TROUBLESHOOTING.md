# Solucion de Problemas - CloudVault

## Diagnostico Rapido

Ejecuta siempre primero:
```powershell
.\scripts\status.ps1 -Detailed
```

## Problemas Comunes

### Docker no inicia

**Sintoma**: "Docker Engine is not running"

**Soluciones**:
1. Abre Docker Desktop manualmente y espera 1-2 minutos
2. Verifica que WSL2 esta instalado:
   ```powershell
   wsl --status
   ```
3. Si WSL2 no esta:
   ```powershell
   wsl --install
   # Reiniciar PC
   ```
4. Verifica virtualizacion en BIOS (VT-x / AMD-V)

### Immich no responde

**Sintoma**: http://localhost:2283 no carga

**Soluciones**:
1. Verificar contenedores:
   ```powershell
   docker compose ps
   docker compose logs immich-server --tail 50
   ```
2. Reiniciar servicios:
   ```powershell
   .\scripts\stop-services.ps1 -Force
   .\scripts\start-services.ps1
   ```
3. Si la DB falla:
   ```powershell
   docker compose logs database --tail 30
   ```

### iPhone no conecta

**Sintoma**: "Cannot connect to server" en la app

**Soluciones**:
1. Verificar que estan en la misma red WiFi
2. Verificar la IP correcta: `.\scripts\status.ps1`
3. Probar en navegador del iPhone: `http://IP:2283`
4. Verificar Firewall de Windows:
   ```powershell
   # Agregar regla de firewall
   New-NetFirewallRule -DisplayName "CloudVault Immich" `
       -Direction Inbound -Protocol TCP -LocalPort 2283 -Action Allow
   ```
5. Si cambio la IP del notebook, actualizar en la app de Immich

### Sync falla

**Sintoma**: Logs muestran errores de sincronizacion

**Soluciones**:
1. Ver logs:
   ```powershell
   Get-Content ".\logs\sync-$(Get-Date -Format 'yyyy-MM-dd').log" -Tail 50
   ```
2. Verificar internet: `ping google.com`
3. Verificar rclone: `rclone lsd cloudvault-union:`
4. Re-autorizar nube:
   ```powershell
   .\scripts\configure-cloud.ps1 -Provider gdrive
   ```
5. Sync manual con verbose:
   ```powershell
   .\scripts\sync-cloud.ps1 -VerboseOutput
   ```

### Disco lleno

**Sintoma**: Warning de espacio o servicios fallan

**Soluciones**:
1. Verificar uso:
   ```powershell
   .\scripts\status.ps1
   ```
2. Forzar limpieza local (si sync esta activo):
   ```powershell
   # En config/settings.json cambiar dry_run a false
   .\scripts\sync-cloud.ps1 -Force
   ```
3. Limpiar Docker:
   ```powershell
   docker system prune -f
   ```
4. Limpiar thumbs viejos de Immich: Admin > Jobs > "Clean up"

### Rclone "token expired"

**Sintoma**: Google Drive u OneDrive dejan de funcionar

**Solucion**:
```powershell
# Re-autorizar el provider
rclone config reconnect gdrive-raw:
# o
rclone config reconnect onedrive-raw:
```

### Subida inicial muy lenta

**Sintoma**: 60 GB tardan dias en subir

**Soluciones**:
1. Es normal! 60 GB por WiFi puede tomar 12-48 horas
2. Asegurar que el iPhone no entra en modo ahorro
3. Mantener la app Immich abierta
4. Conectar iPhone al cargador
5. Si es demasiado lento, verificar velocidad de red:
   - Acercar iPhone al router
   - Conectar notebook por cable Ethernet

## Comandos Utiles

```powershell
# Ver logs de Docker en tiempo real
docker compose logs -f --tail 20

# Reiniciar un servicio especifico
docker compose restart immich-server

# Ver espacio de Docker
docker system df

# Ver todas las tareas programadas
schtasks /query /tn "CloudVault*"

# Test rapido de rclone
rclone lsd cloudvault-union:
rclone about mega-cifrado:

# Verificar estado de la DB
docker exec cloudvault_db pg_isready

# Backup manual de la base de datos
docker exec cloudvault_db pg_dump -U postgres immich > backup.sql
```

## Reset Completo (ultimo recurso)

Si nada funciona y quieres empezar de cero SIN perder las fotos en la nube:

```powershell
# 1. Detener todo
.\scripts\stop-services.ps1 -Force

# 2. Eliminar contenedores y volumenes
docker compose down -v

# 3. Eliminar datos locales (thumbnails y DB, NO las fotos en nube)
Remove-Item -Recurse -Force .\postgres
Remove-Item -Recurse -Force .\upload

# 4. Volver a instalar
.\setup.ps1

# 5. Restaurar fotos desde la nube
.\scripts\restore.ps1
```
