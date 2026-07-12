"""CloudVault Script Runner - Ejecucion de scripts PowerShell.

Proporciona una interfaz para ejecutar los scripts de gestion de CloudVault
a traves de subprocess, capturando salida y errores.
"""

import subprocess
import threading
import os
import json
from typing import Optional, Callable, Dict, Any


class ScriptResult:
    """Resultado de la ejecucion de un script."""

    def __init__(self, success: bool, output: str, error: str,
                 return_code: int, json_data: Optional[Dict] = None):
        self.success = success
        self.output = output
        self.error = error
        self.return_code = return_code
        self.json_data = json_data

    def __repr__(self):
        status = "OK" if self.success else "ERROR"
        return f"ScriptResult({status}, rc={self.return_code})"


class CancellableTask:
    """Handle for a running async script that can be cancelled.

    Call .cancel() to terminate the subprocess. After cancellation the
    callback (if any) will receive a ScriptResult with success=False and
    a cancellation error message.
    """

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None
        self._cancelled = False

    @property
    def is_running(self) -> bool:
        """True if the underlying process is still alive."""
        if self._process is None:
            return self._thread is not None and self._thread.is_alive()
        return self._process.poll() is None

    def cancel(self):
        """Terminate the running subprocess."""
        self._cancelled = True
        if self._process is not None:
            try:
                self._process.kill()
            except OSError:
                pass


class ScriptRunner:
    """Ejecuta scripts PowerShell de CloudVault via subprocess."""

    # Mapeo de scripts disponibles
    SCRIPTS = {
        "start": "start-services.ps1",
        "stop": "stop-services.ps1",
        "sync": "sync-cloud.ps1",
        "status": "status.ps1",
        "configure": "configure-cloud.ps1",
        "restore": "restore.ps1",
        "schedule": "schedule-sync.ps1",
        "uninstall": "uninstall.ps1",
    }

    def __init__(self, install_path: Optional[str] = None):
        """Inicializa el runner con la ruta de instalacion.

        Args:
            install_path: Ruta base de CloudVault.
                          Si es None, usa la ruta del settings.json.
        """
        if install_path:
            self.install_path = install_path
        else:
            self.install_path = self._detect_install_path()

        self.scripts_path = os.path.join(self.install_path, "scripts")
        self._running_processes: Dict[str, subprocess.Popen] = {}

    def _detect_install_path(self) -> str:
        """Detecta la ruta de instalacion buscando config/settings.json."""
        # Intentar rutas comunes
        candidates = [
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)
            ))),
            r"C:\CloudVault",
            os.path.expanduser("~\\CloudVault"),
        ]
        for path in candidates:
            if os.path.exists(os.path.join(path, "config", "settings.json")):
                return path
        # Default
        return candidates[0]

    def _get_script_path(self, script_key: str) -> str:
        """Obtiene la ruta completa de un script."""
        filename = self.SCRIPTS.get(script_key)
        if not filename:
            raise ValueError(
                f"Script desconocido: '{script_key}'. "
                f"Disponibles: {list(self.SCRIPTS.keys())}"
            )
        return os.path.join(self.scripts_path, filename)

    # Characters that are never allowed in parameter values
    _FORBIDDEN_CHARS = set(';|&`$(){}[]!<>')

    @staticmethod
    def _sanitize_value(value: str) -> str:
        """Sanitize a parameter value for safe PowerShell invocation.

        Rejects values containing shell metacharacters that could be used
        for command injection. Strips leading/trailing whitespace.

        Raises:
            ValueError: If the value contains forbidden characters.
        """
        value = str(value).strip()
        dangerous = ScriptRunner._FORBIDDEN_CHARS.intersection(value)
        if dangerous:
            raise ValueError(
                f"Valor no permitido: contiene caracteres peligrosos "
                f"{dangerous!r} en '{value}'"
            )
        # Reject embedded newlines
        if '\n' in value or '\r' in value:
            raise ValueError(
                f"Valor no permitido: contiene saltos de linea en '{value}'"
            )
        return value

    def _build_command(self, script_key: str,
                       params: Optional[Dict[str, Any]] = None,
                       flags: Optional[list] = None) -> list:
        """Construye el comando PowerShell completo.

        All parameter values are validated against a blocklist of shell
        metacharacters before being included in the command.
        """
        script_path = self._get_script_path(script_key)
        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy", "Bypass",
            "-File", script_path
        ]

        # Agregar parametros con nombre (sanitized)
        if params:
            for key, value in params.items():
                if value is True:
                    cmd.append(f"-{key}")
                elif value is not False and value is not None:
                    sanitized = self._sanitize_value(value)
                    cmd.append(f"-{key}")
                    cmd.append(sanitized)

        # Agregar flags simples
        if flags:
            for flag in flags:
                if not flag.startswith("-"):
                    flag = f"-{flag}"
                cmd.append(flag)

        return cmd

    def run(self, script_key: str, params: Optional[Dict[str, Any]] = None,
            flags: Optional[list] = None,
            timeout: Optional[int] = 300,
            interactive: bool = False) -> ScriptResult:
        """Ejecuta un script de forma sincrona.

        Args:
            script_key: Clave del script (start, stop, sync, etc.)
            params: Parametros con nombre {nombre: valor}
            flags: Flags booleanas ["-Force", "-Json"]
            timeout: Tiempo maximo en segundos (default: 5 min)
            interactive: If True, launch in a visible terminal window

        Returns:
            ScriptResult con el resultado de la ejecucion
        """
        if interactive:
            return self._run_interactive(script_key, params)

        cmd = self._build_command(script_key, params, flags)

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=getattr(
                    subprocess, "CREATE_NO_WINDOW", 0
                )
            )
            stdout, stderr = process.communicate(timeout=timeout)
            success = process.returncode == 0

            # Intentar parsear JSON si se paso flag -Json
            json_data = None
            if flags and "Json" in flags or flags and "-Json" in flags:
                try:
                    json_data = json.loads(stdout)
                except (json.JSONDecodeError, ValueError):
                    pass

            return ScriptResult(
                success=success,
                output=stdout.strip(),
                error=stderr.strip(),
                return_code=process.returncode,
                json_data=json_data
            )
        except subprocess.TimeoutExpired:
            process.kill()
            return ScriptResult(
                success=False,
                output="",
                error=f"Timeout: el script excedio {timeout} segundos",
                return_code=-1
            )
        except FileNotFoundError:
            return ScriptResult(
                success=False,
                output="",
                error="PowerShell no encontrado en el sistema",
                return_code=-1
            )
        except Exception as e:
            return ScriptResult(
                success=False,
                output="",
                error=f"Error ejecutando script: {str(e)}",
                return_code=-1
            )

    def run_async(self, script_key: str,
                  params: Optional[Dict[str, Any]] = None,
                  flags: Optional[list] = None,
                  callback: Optional[Callable[[ScriptResult], None]] = None,
                  timeout: Optional[int] = 300,
                  interactive: bool = False):
        """Ejecuta un script de forma asincrona en un hilo separado.

        Args:
            script_key: Clave del script
            params: Parametros con nombre
            flags: Flags booleanas
            callback: Funcion a llamar con el resultado
            timeout: Tiempo maximo en segundos
            interactive: If True, launch in a visible terminal window
        """
        def _worker():
            result = self.run(
                script_key, params, flags, timeout, interactive=interactive
            )
            if callback:
                callback(result)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread

    def run_cancellable(self, script_key: str,
                        params: Optional[Dict[str, Any]] = None,
                        flags: Optional[list] = None,
                        callback: Optional[
                            Callable[[ScriptResult], None]] = None,
                        timeout: Optional[int] = 300):
        """Ejecuta un script de forma asincrona con soporte para cancelacion.

        Returns a CancellableTask object with a .cancel() method that
        terminates the underlying subprocess.

        Args:
            script_key: Clave del script
            params: Parametros con nombre
            flags: Flags booleanas
            callback: Funcion a llamar con el resultado
            timeout: Tiempo maximo en segundos

        Returns:
            CancellableTask with a .cancel() method
        """
        task = CancellableTask()
        cmd = self._build_command(script_key, params, flags)

        def _worker():
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=getattr(
                        subprocess, "CREATE_NO_WINDOW", 0
                    )
                )
                task._process = process
                stdout, stderr = process.communicate(timeout=timeout)

                if task._cancelled:
                    result = ScriptResult(
                        success=False,
                        output="",
                        error="Operacion cancelada por el usuario",
                        return_code=-2
                    )
                else:
                    success = process.returncode == 0
                    json_data = None
                    if (flags and
                            ("Json" in flags or "-Json" in flags)):
                        try:
                            json_data = json.loads(stdout)
                        except (json.JSONDecodeError, ValueError):
                            pass
                    result = ScriptResult(
                        success=success,
                        output=stdout.strip(),
                        error=stderr.strip(),
                        return_code=process.returncode,
                        json_data=json_data
                    )
            except subprocess.TimeoutExpired:
                process.kill()
                result = ScriptResult(
                    success=False,
                    output="",
                    error=f"Timeout: el script excedio {timeout} segundos",
                    return_code=-1
                )
            except Exception as e:
                result = ScriptResult(
                    success=False,
                    output="",
                    error=f"Error ejecutando script: {str(e)}",
                    return_code=-1
                )

            if callback:
                callback(result)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        task._thread = thread
        return task

    def start_services(self, callback=None):
        """Inicia los servicios de CloudVault."""
        if callback:
            return self.run_async("start", callback=callback)
        return self.run("start")

    def stop_services(self, callback=None):
        """Detiene los servicios de CloudVault."""
        if callback:
            return self.run_async("stop", callback=callback)
        return self.run("stop")

    def sync_cloud(self, force: bool = False, dry_run: bool = False,
                   callback=None):
        """Ejecuta sincronizacion a la nube.

        Args:
            force: Forzar sincronizacion completa
            dry_run: Solo simular, no transferir
            callback: Funcion callback para ejecucion async
        """
        params = {}
        if force:
            params["Force"] = True
        if dry_run:
            params["DryRun"] = True

        if callback:
            return self.run_async("sync", params=params, callback=callback)
        return self.run("sync", params=params)

    def get_status(self, as_json: bool = True, callback=None):
        """Obtiene el estado del sistema.

        Args:
            as_json: Solicitar salida en formato JSON
            callback: Funcion callback para ejecucion async
        """
        flags = ["Json"] if as_json else None
        if callback:
            return self.run_async("status", flags=flags, callback=callback)
        return self.run("status", flags=flags)

    def configure_cloud(self, provider: Optional[str] = None, callback=None):
        """Inicia la configuracion de nubes.

        Because configure-cloud.ps1 is interactive (prompts the user for
        provider selection and API keys), it must be launched in a visible
        terminal window rather than captured via PIPE. On Windows this opens
        a new PowerShell window; on other platforms it falls back to the
        non-interactive path.
        """
        params = {"Provider": provider} if provider else None
        if callback:
            return self.run_async(
                "configure", params=params, callback=callback,
                interactive=True
            )
        return self.run("configure", params=params, interactive=True)

    def _run_interactive(self, script_key: str,
                         params: Optional[Dict[str, Any]] = None
                         ) -> 'ScriptResult':
        """Launches an interactive script in a visible terminal window.

        This spawns a new PowerShell console window so the user can
        interact with prompts. The GUI does not capture output; instead
        it waits for the process to complete and returns a success/failure
        result based on the exit code.
        """
        script_path = self._get_script_path(script_key)
        cmd_line = (
            f'powershell.exe -NoProfile -ExecutionPolicy Bypass '
            f'-File "{script_path}"'
        )

        # Append sanitized parameters
        if params:
            for key, value in params.items():
                if value is True:
                    cmd_line += f' -{key}'
                elif value is not False and value is not None:
                    sanitized = self._sanitize_value(value)
                    cmd_line += f' -{key} "{sanitized}"'

        try:
            # On Windows, use START to open a new console window
            # CREATE_NEW_CONSOLE ensures the user can interact
            creation_flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
            process = subprocess.Popen(
                cmd_line,
                shell=False if creation_flags else True,
                creationflags=creation_flags
            )
            process.wait()
            return ScriptResult(
                success=process.returncode == 0,
                output="Configuracion interactiva finalizada.",
                error="" if process.returncode == 0
                else f"Proceso termino con codigo {process.returncode}",
                return_code=process.returncode
            )
        except FileNotFoundError:
            return ScriptResult(
                success=False,
                output="",
                error="PowerShell no encontrado en el sistema",
                return_code=-1
            )
        except Exception as e:
            return ScriptResult(
                success=False,
                output="",
                error=f"Error ejecutando script interactivo: {str(e)}",
                return_code=-1
            )

    def restore(self, provider: Optional[str] = None,
                destination: Optional[str] = None,
                list_only: bool = False, callback=None):
        """Ejecuta restauracion desde la nube.

        Args:
            provider: Nombre del proveedor
            destination: Ruta de destino
            list_only: Solo listar archivos disponibles
            callback: Funcion callback para ejecucion async
        """
        params = {}
        if provider:
            params["Provider"] = provider
        if destination:
            params["Destination"] = destination
        if list_only:
            params["ListOnly"] = True

        if callback:
            return self.run_async("restore", params=params, callback=callback)
        return self.run("restore", params=params)

    def schedule_sync(self, time: Optional[str] = None,
                      frequency: Optional[str] = None, callback=None):
        """Programa la sincronizacion automatica.

        Args:
            time: Hora en formato HH:MM
            frequency: Frecuencia (daily, weekly, etc.)
            callback: Funcion callback para ejecucion async
        """
        params = {}
        if time:
            params["Time"] = time
        if frequency:
            params["Frequency"] = frequency

        if callback:
            return self.run_async("schedule", params=params, callback=callback)
        return self.run("schedule", params=params)
