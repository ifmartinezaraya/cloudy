"""CloudVault Shortcuts - Creacion de accesos directos.

Crea accesos directos en el escritorio, menu inicio,
y la carpeta de inicio automatico de Windows.
"""

import os
import sys
from typing import Optional


def get_desktop_path() -> str:
    """Obtiene la ruta del escritorio del usuario."""
    # Intentar con variable de entorno
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if os.path.exists(desktop):
        return desktop
    # Alternativa en espanol
    desktop_es = os.path.join(os.path.expanduser("~"), "Escritorio")
    if os.path.exists(desktop_es):
        return desktop_es
    # Fallback via registry (Windows)
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        )
        desktop_path, _ = winreg.QueryValueEx(key, "Desktop")
        winreg.CloseKey(key)
        return desktop_path
    except Exception:
        return os.path.join(os.path.expanduser("~"), "Desktop")


def get_startup_path() -> str:
    """Obtiene la ruta de la carpeta de inicio de Windows."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        )
        startup_path, _ = winreg.QueryValueEx(key, "Startup")
        winreg.CloseKey(key)
        return startup_path
    except Exception:
        return os.path.join(
            os.path.expanduser("~"),
            r"AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
        )


def get_start_menu_path() -> str:
    """Obtiene la ruta del menu inicio."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        )
        programs_path, _ = winreg.QueryValueEx(key, "Programs")
        winreg.CloseKey(key)
        return programs_path
    except Exception:
        return os.path.join(
            os.path.expanduser("~"),
            r"AppData\Roaming\Microsoft\Windows\Start Menu\Programs"
        )


def create_shortcut(
    target_path: str,
    shortcut_path: str,
    description: str = "CloudVault - Nube Personal Cifrada",
    icon_path: Optional[str] = None,
    arguments: str = "",
    working_directory: Optional[str] = None
) -> bool:
    """Crea un acceso directo (.lnk) de Windows.

    Args:
        target_path: Ruta al ejecutable o script
        shortcut_path: Ruta donde crear el .lnk
        description: Descripcion del acceso directo
        icon_path: Ruta al icono (.ico)
        arguments: Argumentos para el ejecutable
        working_directory: Directorio de trabajo

    Returns:
        True si se creo correctamente, False en caso de error.
    """
    try:
        # Usar COM para crear el shortcut (solo Windows)
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = target_path
        shortcut.Description = description
        shortcut.Arguments = arguments

        if icon_path and os.path.exists(icon_path):
            shortcut.IconLocation = f"{icon_path},0"

        if working_directory:
            shortcut.WorkingDirectory = working_directory
        else:
            shortcut.WorkingDirectory = os.path.dirname(target_path)

        shortcut.save()
        return True
    except ImportError:
        # Fallback sin win32com: usar PowerShell
        return _create_shortcut_powershell(
            target_path, shortcut_path, description,
            icon_path, arguments, working_directory
        )
    except Exception:
        return False


def _create_shortcut_powershell(
    target_path: str,
    shortcut_path: str,
    description: str,
    icon_path: Optional[str],
    arguments: str,
    working_directory: Optional[str]
) -> bool:
    """Crea acceso directo usando PowerShell (fallback sin pywin32)."""
    import subprocess

    working_dir = working_directory or os.path.dirname(target_path)
    icon_location = f"{icon_path},0" if icon_path else ""

    # Escapar comillas para PowerShell
    ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target_path}"
$Shortcut.Description = "{description}"
$Shortcut.Arguments = "{arguments}"
$Shortcut.WorkingDirectory = "{working_dir}"
'''
    if icon_location:
        ps_script += f'$Shortcut.IconLocation = "{icon_location}"\n'
    ps_script += "$Shortcut.Save()\n"

    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True, timeout=30,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        return result.returncode == 0
    except Exception:
        return False


def create_desktop_shortcut(
    install_path: str,
    use_exe: bool = True
) -> bool:
    """Crea acceso directo de CloudVault en el escritorio.

    Args:
        install_path: Ruta base de CloudVault (C:\\CloudVault)
        use_exe: True para usar .exe, False para usar python script

    Returns:
        True si se creo correctamente.
    """
    desktop = get_desktop_path()
    shortcut_path = os.path.join(desktop, "CloudVault.lnk")
    icon_path = os.path.join(install_path, "gui", "assets", "cloud.ico")

    if use_exe:
        # Apuntar al .exe compilado
        target = os.path.join(install_path, "gui", "dist", "CloudVault.exe")
        if not os.path.exists(target):
            # Fallback: ejecutar con python
            use_exe = False

    if not use_exe:
        # Usar python directamente
        target = sys.executable or "python.exe"
        arguments = f'"{os.path.join(install_path, "gui", "app.py")}"'
    else:
        arguments = ""

    return create_shortcut(
        target_path=target,
        shortcut_path=shortcut_path,
        description="CloudVault - Nube Personal Cifrada",
        icon_path=icon_path if os.path.exists(icon_path) else None,
        arguments=arguments,
        working_directory=install_path
    )


def create_startup_shortcut(
    install_path: str,
    use_exe: bool = True
) -> bool:
    """Crea acceso directo en la carpeta de inicio automatico de Windows.

    Args:
        install_path: Ruta base de CloudVault
        use_exe: True para usar .exe, False para python script

    Returns:
        True si se creo correctamente.
    """
    startup = get_startup_path()
    shortcut_path = os.path.join(startup, "CloudVault.lnk")
    icon_path = os.path.join(install_path, "gui", "assets", "cloud.ico")

    if use_exe:
        target = os.path.join(install_path, "gui", "dist", "CloudVault.exe")
        if not os.path.exists(target):
            use_exe = False

    if not use_exe:
        target = sys.executable or "python.exe"
        arguments = f'"{os.path.join(install_path, "gui", "app.py")}"'
    else:
        arguments = ""

    return create_shortcut(
        target_path=target,
        shortcut_path=shortcut_path,
        description="CloudVault - Inicio Automatico",
        icon_path=icon_path if os.path.exists(icon_path) else None,
        arguments=arguments,
        working_directory=install_path
    )


def create_start_menu_shortcut(
    install_path: str,
    use_exe: bool = True
) -> bool:
    """Crea acceso directo en el menu inicio de Windows.

    Args:
        install_path: Ruta base de CloudVault
        use_exe: True para usar .exe, False para python script

    Returns:
        True si se creo correctamente.
    """
    start_menu = get_start_menu_path()
    # Crear subcarpeta CloudVault
    folder = os.path.join(start_menu, "CloudVault")
    os.makedirs(folder, exist_ok=True)
    shortcut_path = os.path.join(folder, "CloudVault.lnk")
    icon_path = os.path.join(install_path, "gui", "assets", "cloud.ico")

    if use_exe:
        target = os.path.join(install_path, "gui", "dist", "CloudVault.exe")
        if not os.path.exists(target):
            use_exe = False

    if not use_exe:
        target = sys.executable or "python.exe"
        arguments = f'"{os.path.join(install_path, "gui", "app.py")}"'
    else:
        arguments = ""

    return create_shortcut(
        target_path=target,
        shortcut_path=shortcut_path,
        description="CloudVault - Nube Personal Cifrada",
        icon_path=icon_path if os.path.exists(icon_path) else None,
        arguments=arguments,
        working_directory=install_path
    )


def remove_all_shortcuts(install_path: str) -> dict:
    """Elimina todos los accesos directos de CloudVault.

    Returns:
        Diccionario con resultados por ubicacion.
    """
    results = {}

    paths = {
        "desktop": os.path.join(get_desktop_path(), "CloudVault.lnk"),
        "startup": os.path.join(get_startup_path(), "CloudVault.lnk"),
        "start_menu": os.path.join(get_start_menu_path(), "CloudVault", "CloudVault.lnk"),
    }

    for location, path in paths.items():
        try:
            if os.path.exists(path):
                os.remove(path)
                results[location] = True
            else:
                results[location] = None  # No existia
        except OSError:
            results[location] = False

    # Intentar eliminar carpeta del menu inicio
    folder = os.path.join(get_start_menu_path(), "CloudVault")
    try:
        if os.path.exists(folder) and not os.listdir(folder):
            os.rmdir(folder)
    except OSError:
        pass

    return results


def install_all_shortcuts(install_path: str, use_exe: bool = True) -> dict:
    """Instala accesos directos en todas las ubicaciones.

    Args:
        install_path: Ruta base de CloudVault
        use_exe: True para usar .exe compilado

    Returns:
        Diccionario con resultados {ubicacion: True/False}
    """
    return {
        "desktop": create_desktop_shortcut(install_path, use_exe),
        "startup": create_startup_shortcut(install_path, use_exe),
        "start_menu": create_start_menu_shortcut(install_path, use_exe),
    }
