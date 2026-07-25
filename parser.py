from typing import Dict, List, NoReturn, Optional, Set, Tuple
from exceptions import InvalidConfErr
from models import Zone, Connection
# import sys


RawLine = Tuple[int, str]


class MapParser:
    def __init__(self, file_path: str) -> None:
        self.file_path: str = file_path
        self.nb_drones: int = 0
        self.nb_drones_line: Optional[int] = None
        self.start_hub_raw: Optional[str] = None
        self.start_hub_line: Optional[int] = None
        self.end_hub_raw: Optional[str] = None
        self.end_hub_line: Optional[int] = None
        self.hubs_raw: List[RawLine] = []
        self.connections_raw: List[RawLine] = []
        self.zones: Dict[str, Zone] = {}
        self.connections: List[Connection] = []
        self.last_line_number: int = 0

    def raise_line_error(self, line_number: int, message: str) -> NoReturn:
        raise InvalidConfErr(f"Line {line_number}: {message}")

    def parse(self) -> None:
        seen = set()
        with open(self.file_path, 'r') as f:
            x = False
            for num_lin, line in enumerate(f, start=1):
                self.last_line_number = num_lin
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
                        self.raise_line_error(
                            num_lin, "nb_drones must be declared first.")
                if ':' not in line:
                    self.raise_line_error(
                        num_lin, f"Invalid format: {line}")
                key, value = line.split(':', 1)
                key, value = key.strip(), value.strip()
                if key == 'nb_drones':
                    if key in seen:
                        self.raise_line_error(
                            num_lin, f"Duplicate nb_drones: '{line}'")
                    seen.add(key)
                    self.nb_drones_line = num_lin
                    self.set_nb_drones(value, num_lin)
                elif key == 'start_hub':
                    if key in seen:
                        self.raise_line_error(
                            num_lin, "Only one start_hub is allowed")
                    self.start_hub_raw = value
                    self.start_hub_line = num_lin
                    seen.add(key)
                elif key == 'end_hub':
                    if key in seen:
                        self.raise_line_error(
                            num_lin, "Only one end_hub is allowed")
                    self.end_hub_raw = value
                    self.end_hub_line = num_lin
                    seen.add(key)
                elif key == 'hub':
                    self.hubs_raw.append((num_lin, value))
                elif key == 'connection':
                    self.connections_raw.append((num_lin, value))
                else:
                    self.raise_line_error(num_lin, f"Unknown key: {key}")
        self.validate_config()
        self.build_zones()
        self.build_connections()

    def set_nb_drones(self, value: str, line_number: int) -> None:
        try:
            drones = int(value)
        except ValueError:
            self.raise_line_error(line_number, "nb_drones must be a number")
        if drones <= 0:
            self.raise_line_error(line_number, "Number of drones must be > 0")
        self.nb_drones = drones

    def validate_config(self) -> None:
        line_number = max(1, self.last_line_number)
        if self.nb_drones_line is None:
            self.raise_line_error(line_number, "nb_drones is required")
        if not self.start_hub_raw or not self.end_hub_raw:
            self.raise_line_error(
                line_number, "start_hub and end_hub are required")
        if not self.connections_raw:
            self.raise_line_error(line_number, "At least one connection required")

    def build_zones(self) -> None:
        coordinates: Dict[Tuple[int, int], int] = {}
        if self.start_hub_raw:
            line_number = self.start_hub_line or 0
            sz = self.parse_zone_string(self.start_hub_raw, line_number)
            self.zones[sz.name] = sz
            coordinates[(sz.x, sz.y)] = line_number
        if self.end_hub_raw:
            line_number = self.end_hub_line or 0
            ez = self.parse_zone_string(self.end_hub_raw, line_number)
            self.zones[ez.name] = ez
            point = (ez.x, ez.y)
            if point in coordinates:
                self.raise_line_error(line_number, f"Duplicate coordinate: {point}")
            coordinates[point] = line_number
        for line_number, hub_raw in self.hubs_raw:
            z = self.parse_zone_string(hub_raw, line_number)
            if z.name in self.zones:
                self.raise_line_error(line_number, f"Duplicate zone: {z.name}")
            self.zones[z.name] = z
            point = (z.x, z.y)
            if point in coordinates:
                self.raise_line_error(line_number, f"Duplicate coordinate: {point}")
            coordinates[point] = line_number

    def parse_zone_string(self, raw: str, line_number: int) -> Zone:
        b_idx = raw.find('[')
        b_idx2 = raw.find(']')
        if (b_idx == -1) != (b_idx2 == -1) or b_idx2 < b_idx:
            self.raise_line_error(line_number, f"Invalid zone: {raw}")
        core = raw[:b_idx].strip() if b_idx != -1 else raw.strip()
        meta = raw[b_idx + 1: b_idx2].strip() if b_idx != -1 else ""
        added = raw[b_idx2 + 1:].strip() if b_idx != -1 else ""
        items = core.split()
        if len(items) != 3 or '-' in items[0] or ' ' in items[0]:
            self.raise_line_error(line_number, f"Invalid zone: {raw}")

        try:
            name, x, y = items[0], int(items[1]), int(items[2])
        except ValueError:
            self.raise_line_error(
                line_number, f"Invalid zone coordinates: {raw}")
        z_type, max_drones, color = "normal", 1, None
        valid_meta_data = ["zone", "color", "max_drones"]
        seen = set()

        if meta:
            for item in meta.split():
                if '=' not in item:
                    self.raise_line_error(line_number, f"Invalid key: {item}")
                k, v = item.split('=', 1)
                if k in seen:
                    self.raise_line_error(line_number, f"Duplicate key: {k}")
                if k not in valid_meta_data:
                    self.raise_line_error(line_number, f"Invalid key: {k}")
                if k == 'zone':
                    z_type = v
                elif k == 'max_drones':
                    if v == "":
                        self.raise_line_error(
                            line_number, f"Value of max_drones cannot be '{v}'")
                    try:
                        max_drones = int(v)
                    except ValueError:
                        self.raise_line_error(
                            line_number, "max_drones must be a number")
                    if max_drones <= 0:
                        self.raise_line_error(
                            line_number, "max_drones must be greater than 0")
                elif k == 'color':
                    if v == "":
                        self.raise_line_error(
                            line_number, "Value of color cannot be empty")
                    color = v
                seen.add(k)
            if z_type == "":
                self.raise_line_error(line_number, "Type of zone cannot be empty")
            if z_type not in ["normal", "blocked", "restricted", "priority"]:
                self.raise_line_error(
                    line_number,
                    f"Invalid type of zone '{z_type}' it should be 'zone=<type>'")
            if added:
                self.raise_line_error(line_number, f"Invalid key: {added}")

        return Zone(name, x, y, z_type, max_drones, color, line_number)

    def build_connections(self) -> None:
        seen: Set[Tuple[str, str]] = set()
        for line_number, raw in self.connections_raw:
            c = self.parse_connection_string(raw, line_number)
            if (c.zone1, c.zone2) in seen or (c.zone2, c.zone1) in seen:
                self.raise_line_error(
                    line_number, f"Duplicate connection: {c.zone1}-{c.zone2}")
            seen.add((c.zone1, c.zone2))
            self.connections.append(c)

    def parse_connection_string(self, raw: str, line_number: int) -> Connection:
        try:
            b_idx = raw.find('[')
            b_idx2 = raw.find(']')
            if (b_idx == -1) != (b_idx2 == -1) or b_idx2 < b_idx:
                self.raise_line_error(line_number, f"Invalid connection: {raw}")

            core = raw[:b_idx].strip() if b_idx != -1 else raw.strip()
            meta = raw[b_idx + 1: b_idx2].strip() if b_idx != -1 else ""
            added = raw[b_idx2 + 1:].strip() if b_idx != -1 else ""
            stations = core.split('-')
            if (len(stations) != 2 or
                    stations[0] not in self.zones or
                    stations[1] not in self.zones):
                self.raise_line_error(line_number, f"Invalid connection: {raw}")

            mlc = 1
            seen = set()

            meta_data = ["max_link_capacity"]
            for item in meta.split():
                if '=' not in item:
                    self.raise_line_error(
                        line_number,
                        f"Invalid format: {item} Expected: max_link_capacity=number.")
                k, v = item.split('=', 1)
                if k in seen:
                    self.raise_line_error(line_number, f"Duplicate key: {k}")
                if k not in meta_data:
                    self.raise_line_error(line_number, f"Invalid key: {k}")
                if k in meta_data:
                    value = int(v)
                    if value <= 0:
                        self.raise_line_error(
                            line_number, "value should be greater than 0")
                    mlc = int(v)
                    seen.add(k)
                if added:
                    self.raise_line_error(line_number, f"Invalid key: {added}")
            return Connection(
                stations[0].strip(), stations[1].strip(), mlc, line_number)
        except ValueError:
            self.raise_line_error(
                line_number,
                "Invalid format it should be like this "
                "'max_link_capacity=number'")
