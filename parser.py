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
                        raise InvalidConfErr(f"Invalid format: {line}")
                    key, value = line.split(':', 1)
                    key, value = key.strip().lower(), value.strip()
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
        except BaseException as e:
            print(f"Error: {e}")
            sys.exit(1)

    def set_nb_drones(self, value: str) -> None:
        drones = int(value)
        if drones <= 0:
            raise InvalidConfErr("Number of drones must be > 0")
        self.nb_drones = drones

    def validate_config(self) -> None:
        if not self.start_hub_raw or not self.end_hub_raw:
            raise InvalidConfErr("Missing mandatory keys")
        if not self.connections_raw:
            raise InvalidConfErr("At least one connection required")

    def build_zones(self) -> None:
        if self.start_hub_raw:
            sz = self.parse_zone_string(self.start_hub_raw)
            self.zones[sz.name] = sz
        if self.end_hub_raw:
            ez = self.parse_zone_string(self.end_hub_raw)
            self.zones[ez.name] = ez
        for hub_raw in self.hubs_raw:
            z = self.parse_zone_string(hub_raw)
            if z.name in self.zones:
                raise InvalidConfErr(f"Duplicate zone: {z.name}")
            self.zones[z.name] = z

    def parse_zone_string(self, raw: str) -> Zone:
        b_idx = raw.find('[')
        core = raw[:b_idx].strip() if b_idx != -1 else raw.strip()
        meta = raw[b_idx + 1: -1].strip() if b_idx != -1 else ""

        items = core.split()
        if len(items) != 3 or '-' in items[0]:
            raise InvalidConfErr(f"Invalid zone: {raw}")

        name, x, y = items[0], int(items[1]), int(items[2])
        z_type, max_drones, color = "normal", 1, None

        for item in meta.split():
            if '=' in item:
                k, v = item.split('=', 1)
                if k == 'zone':
                    z_type = v
                elif k == 'max_drones':
                    max_drones = int(v)
                elif k == 'color':
                    color = v

        if z_type not in ["normal", "blocked", "restricted", "priority"]:
            raise InvalidConfErr(f"Invalid type of zone '{z_type}'")

        return Zone(name, x, y, z_type, max_drones, color)

    def build_connections(self) -> None:
        seen: Set[Tuple[str, str]] = set()
        for raw in self.connections_raw:
            c = self.parse_connection_string(raw)
            if (c.zone1, c.zone2) in seen or (c.zone2, c.zone1) in seen:
                raise InvalidConfErr(
                    f"Duplicate connection: {c.zone1}-{c.zone2}")
            seen.add((c.zone1, c.zone2))
            self.connections.append(c)

    def parse_connection_string(self, raw: str) -> Connection:
        b_idx = raw.find('[')
        core = raw[:b_idx].strip() if b_idx != -1 else raw.strip()
        meta = raw[b_idx + 1: -1].strip() if b_idx != -1 else ""

        stations = core.split('-')
        if (len(stations) != 2 or
                stations[0] not in self.zones or
                stations[1] not in self.zones):
            raise InvalidConfErr(f"Invalid connection: {raw}")

        mlc = 1
        for item in meta.split():
            if '=' in item:
                k, v = item.split('=', 1)
                if k == 'max_link_capacity':
                    mlc = int(v)

        return Connection(stations[0].strip(), stations[1].strip(), mlc)
