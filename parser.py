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
            seen = set()
            with open(self.file_path, 'r') as f:
                x = False
                y = False
                for num_lin, line in enumerate(f):
                    line = line.split("#", 1)[0].strip()
                    if not line:
                        continue
                    if line.startswith("nb_drones"):
                        x = True
                    elif (
                        line.startswith(("start_hub",
                                         "hub", "end_hub",
                                         "connection"))
                    ):
                        if not x:
                            raise InvalidConfErr("The nb_drones should"
                                                 " be declared "
                                                 "the first "
                                                 "the error is in line"
                                                 f" number: {num_lin}")

                    if ':' not in line:
                        raise InvalidConfErr(f"Invalid format: {line}")
                    key, value = line.split(':', 1)
                    key, value = key.strip().lower(), value.strip()
                    if key == 'nb_drones':
                        self.set_nb_drones(value)
                    elif key == 'start_hub':
                        if key in seen:
                            raise InvalidConfErr("It cannot "
                                                 "be more than one start")
                        self.start_hub_raw = value
                        seen.add(key)
                    elif key == 'end_hub':
                        if key in seen:
                            raise InvalidConfErr("It cannot "
                                                 "be more than one end")
                        self.end_hub_raw = value
                        seen.add(key)
                    elif key == 'hub':
                        self.hubs_raw.append(value)
                    elif key == 'connection':
                        self.connections_raw.append(value)
                    else:
                        raise InvalidConfErr(f'Unknown key: {key}')
            self.validate_config()
            self.build_zones()
            self.build_connections()
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    def set_nb_drones(self, value: str) -> None:
        drones = int(value)
        if drones <= 0:
            raise InvalidConfErr("Number of drones must be > 0")
        self.nb_drones = drones

    def validate_config(self) -> None:
        if not self.start_hub_raw or not self.end_hub_raw:
            raise InvalidConfErr("start_hub and end_hub are required")
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
        b_idx2 = raw.find(']')
        core = raw[:b_idx].strip() if b_idx != -1 else raw.strip()
        meta = raw[b_idx + 1: -1].strip() if b_idx != -1 else ""
        added = raw[b_idx2 + 1:].strip() if meta != -1 else ""

        items = core.split()
        if len(items) != 3 or '-' in items[0]:
            raise InvalidConfErr(f"Invalid zone: {raw}")

        name, x, y = items[0], int(items[1]), int(items[2])
        z_type, max_drones, color = "normal", 1, None
        valid_meta_data = ["zone", "color", "max_drones"]
        seen = set()
        for item in meta.split():
            if '=' not in item:
                raise InvalidConfErr(f"Invalid key: {item}")
            k, v = item.split('=', 1)
            if k in seen:
                raise InvalidConfErr(f"Duplicate Key: {k}")
            if k not in valid_meta_data:
                raise InvalidConfErr(f"Invalid key: {k}")
            if k == 'zone':
                z_type = v
            elif k == 'max_drones':
                if int(v) < 0:
                    raise InvalidConfErr("max_drones cannot be negative")
                max_drones = int(v)
            elif k == 'color':
                color = v
            if added:
                raise InvalidConfErr(f"Invalid key {added}")
            seen.add(k)
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
        b_idx2 = raw.find(']')

        core = raw[:b_idx].strip() if b_idx != -1 else raw.strip()
        meta = raw[b_idx + 1: b_idx2].strip() if b_idx != -1 else ""
        added = raw[b_idx2 + 1:].strip() if b_idx != -1 else ""
        stations = core.split('-')
        if (len(stations) != 2 or
                stations[0] not in self.zones or
                stations[1] not in self.zones):
            raise InvalidConfErr(f"Invalid connection: {raw}")

        mlc = 1
        meta_data = ["max_link_capacity"]
        seen = set()
        for item in meta.split():
            if item == "max_link_capacity":
                if '=' not in item:
                    raise InvalidConfErr(f"Invalid format: {item} "
                                         "Expected: "
                                         "max_link_capacity=number.")
            k, v = item.split('=', 1)
            if k in seen:
                raise InvalidConfErr(f"Duplicate key: {k}")
            if k not in meta_data:
                raise InvalidConfErr(f"Invalid Key: {k}")
            if k == 'max_link_capacity':
                if int(v) < 0:
                    raise InvalidConfErr("max_link_capacity"
                          " cannot be negative")
                mlc = int(v)
                seen.add(k)
            if added:
                raise InvalidConfErr(f"Invalid Key: {added}")

        return Connection(stations[0].strip(), stations[1].strip(), mlc)
