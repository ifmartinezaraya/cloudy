# CloudVault GUI - Interfaz Grafica

> Aplicacion de escritorio para gestionar CloudVault con interfaz moderna en morado y negro azabache.

## Requisitos

- Windows 10/11
- Python 3.9 o superior
- Las dependencias listadas en `requirements.txt`

## Instalacion

```powershell
# 1. Navegar al directorio gui/
cd C:\CloudVault\gui

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. (Opcional) Generar el icono
python assets\generate_icon.py

# 4. Ejecutar la aplicacion
python app.py
```

## Compilar como Ejecutable (.exe)

```powershell
# Compilar con un solo comando
.\build.exe.ps1

# El ejecutable se genera en: dist\CloudVault.exe
```

Para limpiar y recompilar:

```powershell
.\build.exe.ps1 -Clean
```

Para compilar en modo debug (con consola):

```powershell
.\build.exe.ps1 -Debug
```

## Caracteristicas

### Panel de Control (Dashboard)
- Estado de servicios Docker en tiempo real
- Uso de disco local y almacenamiento en nube
- Ultima sincronizacion y estado
- Botones de accion rapida (Iniciar/Detener/Sincronizar)

### Sincronizacion
- Sincronizacion manual o forzada
- Modo prueba (Dry Run) para simular sin transferir
- Configuracion de programacion automatica
- Visor de registro de sincronizacion

### Proveedores de Nube
- Vista de todos los proveedores (Mega, Google Drive, OneDrive)
- Barras de capacidad individuales
- Verificacion de conexiones
- Reconfiguracion de proveedores

### Configuracion
- Editor visual de todas las opciones de settings.json
- Guardado y descarte de cambios
- Validacion de valores

### Registros (Logs)
- Visor de logs en tiempo real
- Filtrado por nivel (INFO/WARN/ERROR/DEBUG)
- Auto-scroll configurable
- Exportacion de logs

### Restaurar
- Seleccion de proveedor de origen
- Selector de carpeta de destino
- Listado de archivos disponibles
- Restauracion con confirmacion

### Bandeja del Sistema
- Icono de nube morada en la bandeja
- Menu contextual con acciones rapidas
- Minimizar a bandeja al cerrar ventana
- Notificaciones del sistema

## Estructura

```
gui/
├── app.py                  # Punto de entrada principal
├── tray.py                 # Integracion bandeja del sistema
├── requirements.txt        # Dependencias Python
├── build.exe.ps1           # Script de compilacion
├── README.md               # Este archivo
├── assets/
│   └── generate_icon.py    # Generador de icono
├── core/
│   ├── __init__.py
│   ├── theme.py            # Colores y estilos
│   ├── script_runner.py    # Ejecutor de scripts PowerShell
│   ├── settings_manager.py # Gestor de configuracion
│   └── status_monitor.py   # Monitor de salud del sistema
└── views/
    ├── __init__.py
    ├── dashboard.py        # Panel principal
    ├── sync_view.py        # Gestion de sync
    ├── clouds_view.py      # Proveedores de nube
    ├── settings_view.py    # Editor de configuracion
    ├── logs_view.py        # Visor de registros
    └── restore_view.py     # Restauracion de archivos
```

## Tema Visual

La aplicacion usa un tema oscuro con colores:

| Color | Hex | Uso |
|-------|-----|-----|
| Morado | `#8B5CF6` | Acento principal, botones, barras |
| Negro Azabache | `#0a0a0a` | Fondo de la ventana |
| Morado Oscuro | `#6D28D9` | Hover, estados activos |
| Morado Claro | `#A78BFA` | Textos destacados |

## Dependencias

| Paquete | Version | Uso |
|---------|---------|-----|
| customtkinter | >= 5.2.0 | Framework de UI moderna |
| Pillow | >= 10.0.0 | Generacion de iconos |
| pystray | >= 0.19.0 | Bandeja del sistema |
| darkdetect | >= 0.8.0 | Deteccion de tema del SO |

## Solucion de Problemas

### La aplicacion no inicia
- Verifica que Python 3.9+ esta instalado: `python --version`
- Instala las dependencias: `pip install -r requirements.txt`

### No se ve el icono en la bandeja
- Verifica que pystray esta instalado correctamente
- En algunas configuraciones de Windows, revisa los iconos ocultos de la bandeja

### Los servicios no responden
- Verifica que Docker Desktop esta ejecutandose
- Ejecuta `.\scripts\status.ps1` manualmente para diagnosticar

### Error de permisos con scripts
- Ejecuta PowerShell como Administrador
- Verifica: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`
