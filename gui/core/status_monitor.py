"""CloudVault Status Monitor - Monitoreo periodico del sistema.

Ejecuta comprobaciones de salud del sistema a intervalos regulares
usando el script status.ps1 -Json y notifica cambios de estado.
"""

import threading
import time
import json
from typing import Optional, Callable, Dict, Any, List
from .script_runner import ScriptRunner


class ServiceStatus:
    """Estado de un servicio individual."""

    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"

    def __init__(self, name: str, status: str = "unknown",
                 details: str = ""):
        self.name = name
        self.status = status
        self.details = details

    @property
    def is_running(self) -> bool:
        return self.status == self.RUNNING

    @property
    def is_error(self) -> bool:
        return self.status == self.ERROR

    def __repr__(self):
        return f"ServiceStatus({self.name}: {self.status})"


class SystemHealth:
    """Estado general del sistema CloudVault."""

    def __init__(self):
        self.services: Dict[str, ServiceStatus] = {}
        self.disk_usage_percent: float = 0.0
        self.disk_free_gb: float = 0.0
        self.disk_total_gb: float = 0.0
        self.last_sync: str = "Nunca"
        self.last_sync_status: str = "unknown"
        self.cloud_usage_gb: float = 0.0
        self.cloud_total_gb: float = 0.0
        self.immich_accessible: bool = False
        self.immich_url: str = ""
        self.photos_count: int = 0
        self.videos_count: int = 0
        self.timestamp: str = ""
        self.raw_data: Dict[str, Any] = {}

    @property
    def all_services_running(self) -> bool:
        """Verifica si todos los servicios estan activos."""
        if not self.services:
            return False
        return all(s.is_running for s in self.services.values())

    @property
    def any_service_error(self) -> bool:
        """Verifica si hay algun servicio con error."""
        return any(s.is_error for s in self.services.values())

    @property
    def overall_status(self) -> str:
        """Estado general del sistema."""
        if self.all_services_running:
            return "healthy"
        elif self.any_service_error:
            return "error"
        elif any(s.is_running for s in self.services.values()):
            return "degraded"
        else:
            return "stopped"

    @property
    def cloud_usage_percent(self) -> float:
        """Porcentaje de uso de almacenamiento en la nube."""
        if self.cloud_total_gb <= 0:
            return 0.0
        return (self.cloud_usage_gb / self.cloud_total_gb) * 100


class StatusMonitor:
    """Monitor periodico del estado del sistema CloudVault."""

    def __init__(self, script_runner: Optional[ScriptRunner] = None,
                 interval_seconds: int = 60):
        """Inicializa el monitor de estado.

        Args:
            script_runner: Instancia de ScriptRunner para ejecutar status.ps1
            interval_seconds: Intervalo de verificacion en segundos
        """
        self.runner = script_runner or ScriptRunner()
        self.interval = interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._health = SystemHealth()
        self._callbacks: List[Callable[[SystemHealth], None]] = []
        self._lock = threading.Lock()

    @property
    def health(self) -> SystemHealth:
        """Retorna el estado actual del sistema."""
        with self._lock:
            return self._health

    def add_callback(self, callback: Callable[[SystemHealth], None]):
        """Registra un callback para notificaciones de cambio de estado.

        Args:
            callback: Funcion que recibe SystemHealth cuando hay cambios.
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[SystemHealth], None]):
        """Elimina un callback registrado."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def start(self):
        """Inicia el monitoreo periodico en un hilo daemon."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Detiene el monitoreo periodico."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def check_now(self):
        """Ejecuta una verificacion inmediata (asincrona)."""
        thread = threading.Thread(target=self._do_check, daemon=True)
        thread.start()

    def _monitor_loop(self):
        """Bucle principal de monitoreo."""
        while self._running:
            self._do_check()
            # Dormir en intervalos cortos para responder rapido al stop
            elapsed = 0
            while elapsed < self.interval and self._running:
                time.sleep(1)
                elapsed += 1

    def _do_check(self):
        """Ejecuta una verificacion de estado."""
        result = self.runner.get_status(as_json=True)

        with self._lock:
            if result.success and result.json_data:
                self._parse_json_status(result.json_data)
            elif result.success and result.output:
                self._parse_text_status(result.output)
            else:
                self._set_offline_status(result.error)

        # Notificar callbacks
        for callback in self._callbacks:
            try:
                callback(self._health)
            except Exception:
                pass

    def _parse_json_status(self, data: Dict[str, Any]):
        """Parsea la salida JSON del script status.ps1 -Json."""
        health = SystemHealth()
        health.raw_data = data
        health.timestamp = data.get("timestamp", "")

        # Servicios Docker
        containers = data.get("containers", data.get("services", {}))
        if isinstance(containers, dict):
            for name, info in containers.items():
                if isinstance(info, dict):
                    status = info.get("status", "unknown")
                    details = info.get("details", "")
                else:
                    status = str(info)
                    details = ""
                health.services[name] = ServiceStatus(name, status, details)
        elif isinstance(containers, list):
            for item in containers:
                name = item.get("name", "unknown")
                status = item.get("status", "unknown")
                details = item.get("details", "")
                health.services[name] = ServiceStatus(name, status, details)

        # Uso de disco
        disk = data.get("disk", {})
        health.disk_usage_percent = disk.get("usage_percent", 0.0)
        health.disk_free_gb = disk.get("free_gb", 0.0)
        health.disk_total_gb = disk.get("total_gb", 0.0)

        # Sincronizacion
        sync_info = data.get("sync", data.get("last_sync", {}))
        if isinstance(sync_info, dict):
            health.last_sync = sync_info.get("time", "Nunca")
            health.last_sync_status = sync_info.get("status", "unknown")
        elif isinstance(sync_info, str):
            health.last_sync = sync_info

        # Nube
        cloud = data.get("cloud", {})
        health.cloud_usage_gb = cloud.get("usage_gb", 0.0)
        health.cloud_total_gb = cloud.get("total_gb", 40.0)

        # Immich
        immich = data.get("immich", {})
        health.immich_accessible = immich.get("accessible", False)
        health.immich_url = immich.get("url", "http://localhost:2283")
        health.photos_count = immich.get("photos", 0)
        health.videos_count = immich.get("videos", 0)

        self._health = health

    def _parse_text_status(self, output: str):
        """Parsea salida de texto plano del script status.ps1."""
        health = SystemHealth()

        # Intentar extraer informacion basica del texto
        lines = output.lower().split("\n")
        for line in lines:
            if "running" in line or "activo" in line:
                if "server" in line or "immich" in line:
                    health.services["cloudvault_server"] = ServiceStatus(
                        "cloudvault_server", ServiceStatus.RUNNING
                    )
                if "redis" in line:
                    health.services["cloudvault_redis"] = ServiceStatus(
                        "cloudvault_redis", ServiceStatus.RUNNING
                    )
                if "database" in line or "postgres" in line or "db" in line:
                    health.services["cloudvault_db"] = ServiceStatus(
                        "cloudvault_db", ServiceStatus.RUNNING
                    )
                if "ml" in line or "machine" in line:
                    health.services["cloudvault_ml"] = ServiceStatus(
                        "cloudvault_ml", ServiceStatus.RUNNING
                    )

        self._health = health

    def _set_offline_status(self, error: str):
        """Establece el estado como offline/no disponible."""
        health = SystemHealth()
        # Marcar todos los servicios conocidos como desconocidos
        known_services = [
            "cloudvault_server",
            "cloudvault_ml",
            "cloudvault_redis",
            "cloudvault_db"
        ]
        for name in known_services:
            health.services[name] = ServiceStatus(
                name, ServiceStatus.UNKNOWN, error
            )
        self._health = health
