"""CloudVault Settings Manager - Lectura y escritura de configuracion.

Maneja el archivo config/settings.json proporcionando acceso
tipado y validado a todas las opciones de configuracion.
"""

import json
import os
import copy
from typing import Any, Optional, Dict, List


class SettingsManager:
    """Gestiona la configuracion de CloudVault (config/settings.json)."""

    def __init__(self, install_path: Optional[str] = None):
        """Inicializa el gestor de configuracion.

        Args:
            install_path: Ruta base de CloudVault.
        """
        if install_path:
            self.install_path = install_path
        else:
            self.install_path = self._detect_install_path()

        self.config_path = os.path.join(
            self.install_path, "config", "settings.json"
        )
        self._settings: Dict[str, Any] = {}
        self._original: Dict[str, Any] = {}
        self.load()

    def _detect_install_path(self) -> str:
        """Detecta la ruta de instalacion de CloudVault."""
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
        return candidates[0]

    def load(self) -> bool:
        """Carga la configuracion desde el archivo JSON.

        Returns:
            True si la carga fue exitosa, False si hubo error.
        """
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._settings = json.load(f)
            self._original = copy.deepcopy(self._settings)
            return True
        except FileNotFoundError:
            self._settings = self._get_defaults()
            self._original = copy.deepcopy(self._settings)
            return False
        except json.JSONDecodeError:
            self._settings = self._get_defaults()
            self._original = copy.deepcopy(self._settings)
            return False

    def save(self) -> bool:
        """Guarda la configuracion actual al archivo JSON.

        Returns:
            True si se guardo correctamente, False si hubo error.
        """
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            self._original = copy.deepcopy(self._settings)
            return True
        except (IOError, OSError):
            return False

    def get(self, key_path: str, default: Any = None) -> Any:
        """Obtiene un valor de configuracion usando notacion de punto.

        Args:
            key_path: Ruta al valor (e.g., "sync.schedule", "cloud.providers")
            default: Valor por defecto si no existe

        Returns:
            El valor de configuracion o el default.
        """
        keys = key_path.split(".")
        value = self._settings
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, key_path: str, value: Any) -> bool:
        """Establece un valor de configuracion usando notacion de punto.

        Args:
            key_path: Ruta al valor (e.g., "sync.schedule")
            value: Nuevo valor a establecer

        Returns:
            True si se establecio correctamente.
        """
        keys = key_path.split(".")
        target = self._settings
        for key in keys[:-1]:
            if key not in target or not isinstance(target[key], dict):
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value
        return True

    def has_changes(self) -> bool:
        """Verifica si hay cambios sin guardar."""
        return self._settings != self._original

    def discard_changes(self):
        """Descarta cambios y restaura la configuracion original."""
        self._settings = copy.deepcopy(self._original)

    def get_all(self) -> Dict[str, Any]:
        """Retorna una copia de toda la configuracion."""
        return copy.deepcopy(self._settings)

    # --- Propiedades de acceso rapido ---

    @property
    def app_name(self) -> str:
        return self.get("general.app_name", "CloudVault")

    @property
    def install_path_setting(self) -> str:
        return self.get("general.install_path", r"C:\CloudVault")

    @property
    def immich_port(self) -> int:
        return self.get("immich.port", 2283)

    @property
    def sync_schedule(self) -> str:
        return self.get("sync.schedule", "02:00")

    @property
    def sync_frequency(self) -> str:
        return self.get("sync.frequency", "daily")

    @property
    def sync_dry_run(self) -> bool:
        return self.get("sync.dry_run", True)

    @property
    def bandwidth_limit(self) -> str:
        return self.get("sync.bandwidth_limit", "")

    @property
    def max_local_usage_gb(self) -> int:
        return self.get("storage.max_local_usage_gb", 80)

    @property
    def auto_cleanup(self) -> bool:
        return self.get("storage.auto_cleanup", True)

    @property
    def cloud_providers(self) -> List[Dict]:
        return self.get("cloud.providers", [])

    @property
    def health_check_interval(self) -> int:
        return self.get("health.check_interval_minutes", 30)

    @property
    def auto_start(self) -> bool:
        return self.get("general.auto_start_on_boot", True)

    @property
    def notifications_enabled(self) -> bool:
        return self.get("general.notifications_enabled", True)

    @property
    def log_level(self) -> str:
        return self.get("general.log_level", "INFO")

    # --- Metodos de configuracion especifica ---

    def get_provider_by_name(self, name: str) -> Optional[Dict]:
        """Obtiene un proveedor de nube por nombre."""
        for provider in self.cloud_providers:
            if provider.get("name") == name:
                return provider
        return None

    def get_total_cloud_capacity(self) -> int:
        """Retorna la capacidad total en GB de todas las nubes."""
        return sum(
            p.get("capacity_gb", 0)
            for p in self.cloud_providers
            if p.get("enabled", False)
        )

    def get_enabled_providers(self) -> List[Dict]:
        """Retorna solo los proveedores habilitados."""
        return [
            p for p in self.cloud_providers
            if p.get("enabled", False)
        ]

    def _get_defaults(self) -> Dict[str, Any]:
        """Retorna configuracion por defecto."""
        return {
            "_schema": "cloudvault-settings",
            "_version": "1.1.0",
            "general": {
                "app_name": "CloudVault",
                "install_path": r"C:\CloudVault",
                "log_level": "INFO",
                "language": "es",
                "auto_start_on_boot": True,
                "notifications_enabled": True
            },
            "immich": {
                "version": "release",
                "port": 2283,
                "host": "0.0.0.0",
                "machine_learning": True
            },
            "storage": {
                "upload_path": "./upload",
                "max_local_usage_gb": 80,
                "auto_cleanup": True
            },
            "cloud": {
                "enabled": True,
                "providers": [],
                "union_name": "cloudvault-union"
            },
            "sync": {
                "schedule": "02:00",
                "frequency": "daily",
                "transfers": 4,
                "bandwidth_limit": "",
                "dry_run": True,
                "task_name": "CloudVault-Sync"
            },
            "health": {
                "check_interval_minutes": 30
            }
        }
