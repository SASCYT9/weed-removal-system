"""Configuration loader utility."""

import yaml
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


class ConfigLoader:
    """Load and manage configuration from YAML files and environment variables."""

    def __init__(self, config_path: str = None):
        """
        Initialize configuration loader.

        Args:
            config_path: Path to configuration YAML file
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self._config = None

        # Load environment variables
        load_dotenv()

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Returns:
            Configuration dictionary
        """
        if self._config is not None:
            return self._config

        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f)

        # Override with environment variables if present
        self._override_from_env()

        return self._config

    def _override_from_env(self):
        """Override configuration values from environment variables."""
        # GPS configuration
        if os.getenv('GPS_PORT'):
            self._config['navigation']['gps']['port'] = os.getenv('GPS_PORT')
        if os.getenv('GPS_BAUDRATE'):
            self._config['navigation']['gps']['baudrate'] = int(os.getenv('GPS_BAUDRATE'))

        # IMU configuration
        if os.getenv('IMU_PORT'):
            self._config['navigation']['imu']['port'] = os.getenv('IMU_PORT')
        if os.getenv('IMU_BAUDRATE'):
            self._config['navigation']['imu']['baudrate'] = int(os.getenv('IMU_BAUDRATE'))

        # MQTT configuration
        if os.getenv('MQTT_BROKER'):
            self._config['telemetry']['mqtt']['broker'] = os.getenv('MQTT_BROKER')
        if os.getenv('MQTT_PORT'):
            self._config['telemetry']['mqtt']['port'] = int(os.getenv('MQTT_PORT'))

        # Flask configuration
        if os.getenv('FLASK_DEBUG'):
            self._config['telemetry']['web']['debug'] = os.getenv('FLASK_DEBUG').lower() == 'true'

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated key path.

        Args:
            key_path: Dot-separated path to configuration value (e.g., 'camera.resolution')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        if self._config is None:
            self.load()

        keys = key_path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def reload(self):
        """Reload configuration from file."""
        self._config = None
        return self.load()


# Global configuration instance
config = ConfigLoader()
