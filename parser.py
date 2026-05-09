import sys
from typing import Dict, List, Optional, Set, Tuple
from exceptions import InvalidConfErr
from models import Zone, Connection


class MapParser:
    def __init__(self, file_path: str) -> None:
        self.file_path: str = file_path
        self.nb_drones: int = 0
        self.start_hub_raw: Optional[str] = None
        self.end_hub_raw: Optional[str] = None
        self.hubs_raw: List[str] = []
        self.connections_raw: List[str] = []
        self.zones: Dict[str, Zone] = {}
        self.connections: List[Connection] = []

    def parse(self) -> None:
        try:
            with open(self.file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if ':' not in line:
                        raise InvalidConfErr(f"Invalid line format: {line}")
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    if key == 'nb_drones':
                        self.set_nb_drones(value)
                    elif key == 'start_hub':
                        self.start_hub_raw = value
                    elif key == 'end_hub':
                        self.end_hub_raw = value
                    elif key == 'hub':
                        self.hubs_raw.append(value)
                    elif key == 'connection':
                        self.connections_raw.append(value)
                    else:
                        raise InvalidConfErr(f'Unknown key: {key}')
            self.validate_config()
            self.build_zones()
            self.build_connections()
        except InvalidConfErr as e:
            print(f"Configuration Error: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print(f"Error: File '{self.file_path}' not found.")
            sys.exit(1)

    def set_nb_drones(self, value: str) -> None:
        try:
            drones = int(value)
            if drones <= 0:
                raise InvalidConfErr("Number of drones can't be 0 or less")
            self.nb_drones = drones
        except ValueError:
            raise InvalidConfErr("Number of drones must be a valid number")

    def validate_config(self) -> None:
        missing_keys: List[str] = []
        if self.nb_drones == 0:
            missing_keys.append("nb_drones")
        if not self.start_hub_raw:
            missing_keys.append("start_hub")
        if not self.end_hub_raw:
            missing_keys.append("end_hub")
        if missing_keys:
            raise InvalidConfErr(f"Missing mandatory keys: {missing_keys}")
        if not self.connections_raw:
            raise InvalidConfErr("At least one connection is required")

    def build_zones(self) -> None:
        if self.start_hub_raw:
            start_zone = self.parse_zone_string(self.start_hub_raw)
            self.zones[start_zone.name] = start_zone

        if self.end_hub_raw:
            end_zone = self.parse_zone_string(self.end_hub_raw)
            self.zones[end_zone.name] = end_zone

        for hub_raw in self.hubs_raw:
            zone_obj = self.parse_zone_string(hub_raw)
            if zone_obj.name in self.zones:
                raise InvalidConfErr(f"Duplicate zone. {zone_obj.name}")
            self.zones[zone_obj.name] = zone_obj

    def parse_zone_string(self, raw_string: str) -> Zone:
        raw_string = raw_string.strip()
        bracket_index = raw_string.find('[')

        core_part = ""
        metadata_str = ""

        if bracket_index != -1:
            core_part = raw_string[:bracket_index].strip()
            metadata_str = raw_string[bracket_index + 1: -1].strip()
        else:
            core_part = raw_string

        core_items = core_part.split()
        if len(core_items) != 3:
            raise InvalidConfErr(f"Invalid zone format: {raw_string}")

        name = core_items[0]

        if '-' in name:
            raise InvalidConfErr(f"Zone name cannot contain dashes: {name}")

        x = int(core_items[1])
        y = int(core_items[2])

        zone_type = "normal"
        max_drones = 1
        color = None

        if metadata_str:
            meta_items = metadata_str.split()
            for item in meta_items:
                if '=' in item:
                    key, val = item.split('=', 1)
                    if key == 'zone':
                        zone_type = val
                    elif key == 'max_drones':
                        max_drones = int(val)
                    elif key == 'color':
                        color = val

        valid_zone_types = ["normal", "blocked", "restricted", "priority"]
        if zone_type not in valid_zone_types:
            raise InvalidConfErr(
                f"Invalid zone type '{zone_type}' for zone '{name}'")

        if max_drones <= 0:
            raise InvalidConfErr(
                f"max_drones must be positive for zone '{name}'")

        return Zone(name, x, y, zone_type, max_drones, color)

    def build_connections(self) -> None:
        seen_connections: Set[Tuple[str, str]] = set()

        for conn_raw in self.connections_raw:
            conn_obj = self.parse_connection_string(conn_raw)

            conn_pair1 = (conn_obj.zone1, conn_obj.zone2)
            conn_pair2 = (conn_obj.zone2, conn_obj.zone1)

            if (conn_pair1 in seen_connections
                    or conn_pair2 in seen_connections):
                raise InvalidConfErr(
                    "Duplicate connection found: "
                    f"{conn_obj.zone1}-{conn_obj.zone2}")

            seen_connections.add(conn_pair1)
            self.connections.append(conn_obj)

    def parse_connection_string(self, raw_string: str) -> Connection:
        raw_string = raw_string.strip()
        bracket_index = raw_string.find('[')

        core_part = ""
        metadata_str = ""

        if bracket_index != -1:
            core_part = raw_string[:bracket_index].strip()
            metadata_str = raw_string[bracket_index + 1: -1].strip()
        else:
            core_part = raw_string

        stations = core_part.split('-')
        if len(stations) != 2:
            raise InvalidConfErr(f"Invalid connection format: {raw_string}")

        zone1_name = stations[0].strip()
        zone2_name = stations[1].strip()

        if zone1_name not in self.zones:
            raise InvalidConfErr(
                f"Invalid connection: '{zone1_name}' not found")
        if zone2_name not in self.zones:
            raise InvalidConfErr(
                f"Invalid connection: '{zone2_name}' not found")

        max_link_capacity = 1

        if metadata_str:
            meta_items = metadata_str.split()
            for item in meta_items:
                if '=' in item:
                    key, val = item.split('=', 1)
                    if key == 'max_link_capacity':
                        max_link_capacity = int(val)

        if max_link_capacity <= 0:
            raise InvalidConfErr(
                "max_link_capacity must be positive for connection "
                f"'{zone1_name}-{zone2_name}'")

        return Connection(zone1_name, zone2_name, max_link_capacity)
