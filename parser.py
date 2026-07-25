from typing import Dict, List, Optional, Set, Tuple
from exceptions import InvalidConfErr
from models import Zone, Connection
# import sys


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
        seen = set()
        with open(self.file_path, 'r') as f:
            x = False
            for num_lin, line in enumerate(f, start=1):
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
                        raise InvalidConfErr(
                            f"Line {num_lin}:"
                            " nb_drones must be declared first.")
                if ':' not in line:
                    raise InvalidConfErr(f"Line: {num_lin}"
                                         f"Invalid format : {line}")
                key, value = line.split(':', 1)
                key, value = key.strip(), value.strip()
                if key == 'nb_drones':
                    if key in seen:
                        raise InvalidConfErr(f"Line: {num_lin} "
                                            "Duplicate "
                                                f"nb_drones: '{line}'")
                    seen.add(key)
                    self.set_nb_drones(value)
                elif key == 'start_hub':
                    if key in seen:
                        raise InvalidConfErr(f"Line: {num_lin}"
                                                " Only one start_hub "
                                                "is allowed")
                    self.start_hub_raw = value
                    seen.add(key)
                elif key == 'end_hub':
                    if key in seen:
                        raise InvalidConfErr(f"Line: {num_lin}: "
                                                "Only one end is allowed")
                    self.end_hub_raw = value
                    seen.add(key)
                elif key == 'hub':
                    self.hubs_raw.append(value)
                elif key == 'connection':
                    self.connections_raw.append(value)
                else:
                    raise InvalidConfErr(f"Line: {num_lin} "
                                            f"Unknown key: {key}")
        self.validate_config()
        self.build_zones()
        self.build_connections()

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
        lista = []
        if self.start_hub_raw:
            sz = self.parse_zone_string(self.start_hub_raw)
            self.zones[sz.name] = sz
            lista.append(sz.x)
            lista.append(sz.y)
        if self.end_hub_raw:
            ez = self.parse_zone_string(self.end_hub_raw)
            self.zones[ez.name] = ez
            lista.append(ez.x)
            lista.append(ez.y)
        for hub_raw in self.hubs_raw:
            z = self.parse_zone_string(hub_raw)
            if z.name in self.zones:
                raise InvalidConfErr(f"Duplicate zone: {z.name}")
            self.zones[z.name] = z
            lista.append(z.x)
            lista.append(z.y)
        res = [(lista[i], lista[i + 1]) for i in range(0, len(lista), 2)]

        seen = set()
        for i in res:
            if i in seen:
                raise InvalidConfErr(f"Duplicate coordinate: {i}")
            seen.add(i)

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
                if v == "":
                    raise InvalidConfErr(f"Value of max_drones"
                                         f" cannot be '{v}'")
                if int(v) <= 0:
                    raise InvalidConfErr("max_drones must"
                                         " be greater than 0")
                max_drones = int(v)
            elif k == 'color':
                if v == "":
                    raise InvalidConfErr("Value of color cannot be empty")

                color = v
        if added:
            raise InvalidConfErr(f"Invalid key {added}")
            seen.add(k)
        if z_type == "":
            raise InvalidConfErr("Type of zone cannot be empty")
        if z_type not in ["normal", "blocked", "restricted", "priority"]:
            raise InvalidConfErr(
                f"Invalid type of zone '{z_type}'"
                " it should be 'zone=<type>'")

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
        try:
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
            seen = set()

            meta_data = ["max_link_capacity"]
            for item in meta.split():
                if '=' not in item:
                    raise InvalidConfErr(f"Invalid format: {item} "
                                         "Expected: "
                                         "max_link_capacity=number.")
                k, v = item.split('=', 1)
                if k in seen:
                    raise InvalidConfErr(f"Duplicate key: {k}")
                if k not in meta_data:
                    raise InvalidConfErr(f"Invalid Key: {k}")
                if k in meta_data:
                    value = int(v)
                    if value <= 0:
                        raise InvalidConfErr("value should be greater than 0")
                    mlc = int(v)
                    seen.add(k)
            if added:
                raise InvalidConfErr(f"Invalid Key: {added}")

            return Connection(stations[0].strip(), stations[1].strip(), mlc)
        except ValueError:
            raise InvalidConfErr("Inalid format it "
                                 "should be like this "
                                 "'max_link_capacity=number'")
