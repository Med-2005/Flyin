import sys
from typing import Dict, List, Optional
from exceptions import InvalidConfigError
from models import Zone, Connection


class MapParser:
    def __init__(self, file_path: str) -> None:
        self.file_path: str = file_path
        self.nb_drones: int = 0
        self.start_hub_raw: Optional[str] = None
        self.end_hub_raw: Optional[str] = None
        self.hubs_raw: List[str] = []
        self.connections_raw: List[str] = []

    def parse(self) -> None:
        try:
            with open(self.file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if ':' not in line:
                        raise InvalidConfigError(f"Invalid line format: {line}")
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    if key == 'nb_drones':
                        self._set_nb_drones(value)
                    elif key == 'start_hub':
                        self.start_hub_raw = value
                    elif key == 'end_hub':
                        self.end_hub_raw = value
                    elif key == 'hub':
                        self.hubs_raw.append(value)
                    elif key == 'connection':
                        self.connections_raw.append(value)
                    else:
                        raise InvalidConfigError(f'Unknown key: {key}')
            self.validate_config()
        except InvalidConfigError as e:
            print(f"Configuration Error: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print(f"Error: File '{self.file_path}' not found.")
            sys.exit(1)

    def _set_nb_drones(self, value: str) -> None:
        try:
            drones = int(value)
            if drones <= 0:
                raise InvalidConfigError("Number of drones can't be 0 or less")
            self.nb_drones = drones
        except ValueError:
            raise InvalidConfigError("Number of drones must be a valid number")

    def validate_config(self) -> None:
        missing_keys: List[str] = []
        if self.nb_drones == 0:
            missing_keys.append("nb_drones")
        if not self.start_hub_raw:
            missing_keys.append("start_hub")
        if not self.end_hub_raw:
            missing_keys.append("end_hub")
        if missing_keys:
            raise InvalidConfigError(f"Missing mandatory keys: {missing_keys}")
        if not self.connections_raw:
            raise InvalidConfigError("At least one connection is required")
