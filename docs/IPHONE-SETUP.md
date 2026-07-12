# Configurar iPhone con CloudVault

## Paso 1: Descargar la app

1. Abre la **App Store** en tu iPhone 13
2. Busca **"Immich"**
3. Descarga la app gratuita (icono azul con montanas)

## Paso 2: Obtener la IP del servidor

En tu notebook, abre PowerShell y ejecuta:
```powershell
.\scripts\status.ps1
```

Busca la linea que dice "iPhone: http://192.168.x.x:2283"

## Paso 3: Conectar

1. Abre la app Immich
2. En "Server Endpoint URL" ingresa: `http://TU_IP:2283`
3. Toca "Login"
4. Ingresa tu email y contrasena (los que creaste en el navegador)

## Paso 4: Activar respaldo automatico

1. Ve a **Configuracion** (icono de engranaje)
2. Toca **"Backup"**
3. Activa **"Background Backup"**
4. Selecciona los albumes a respaldar:
   - "Recientes" (todas las fotos)
   - O albumes especificos
5. Activa **"WiFi Only"** (para no usar datos moviles)
6. Opcionalmente activa **"Require Charging"** (solo sube cargando)

## Paso 5: Subida inicial

La primera vez tardara bastante (60 GB). Recomendaciones:
- Conecta el iPhone al cargador
- Asegurate de estar en WiFi
- Deja la app abierta (o el iPhone desbloqueado)
- Puedes ver el progreso en la pestana "Backup" de la app

## Consejos

### Respaldo en segundo plano
iOS limita las apps en segundo plano. Para mejor respaldo:
- **No cierres la app** (dejala en segundo plano, no la deslices para cerrar)
- **Ubicacion "Siempre"**: Si la app pide permiso de ubicacion, dale "Siempre". Immich usa geofencing para detectar cuando llegas a casa y subir fotos.
- **Desactiva "Ahorro de bateria"** mientras hace la subida inicial

### Velocidad de subida
- La primera subida (60 GB) puede tomar 6-24 horas
- Despues, solo sube las fotos nuevas (segundos por dia)
- Si es muy lento, verifica que ambos dispositivos estan en la misma red WiFi

### Acceso desde fuera de casa (Tailscale)
Si configuraste Tailscale:
1. Instala Tailscale desde App Store
2. Inicia sesion con la misma cuenta que tu notebook
3. En Immich > Settings > Server URL, cambia a la IP de Tailscale
   (algo como `http://100.x.x.x:2283`)

### Fotos Live Photos
Immich soporta Live Photos de Apple. Se suben como foto + video corto.

### Formato HEIC
Immich soporta HEIC/HEIF nativo. No necesitas cambiar el formato de la camara.

## Solucion de problemas

| Problema | Solucion |
|----------|----------|
| "Cannot connect to server" | Verifica la IP, ambos en misma WiFi |
| Backup no avanza | Cierra y abre la app, verifica WiFi |
| Muy lento | El notebook esta encendido? Docker corriendo? |
| Se detiene al bloquear iPhone | Normal, se reanuda luego (background) |
| No sube videos | Verifica que seleccionaste "Videos" en backup settings |
