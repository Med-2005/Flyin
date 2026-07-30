"""Parse and validate drone simulation map configuration files."""

from typing import Dict, List, NoReturn, Optional, Set, Tuple
from exceptions import InvalidConfErr
from models import Zone, Connection


RawLine = Tuple[int, str]

zone_meta_ex = "max_drones=<number> color=<value> zone=<type>"
zone_ex = (
    "hub: <name> <x> <y> "
    "[max_drones=<number> color=<value> zone=<type>]"
)
conn_ex = "connection: <hub_a>-<hub_b> [max_link_capacity=<number>]"
req_conf = (
    "nb_drones: <number>; start_hub: <name> <x> <y>; "
    "hub: <name> <x> <y>; end_hub: <name> <x> <y>; "
    "connection: <hub_a>-<hub_b>"
)


class MapParser:
    """Read a map file and convert its entries into simulation objects."""

    def __init__(self, file_path: str) -> None:
        """Set up an empty parser for a map file.

        Args:
            file_path: Path to the map configuration file.
        """
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
        """Raise a configuration error that includes its source line.

        Args:
            line_number: Line where the problem was found.
            message: Clear description of the problem.

        Raises:
            InvalidConfErr: Always raised with line information.
        """
        raise InvalidConfErr(f"Line {line_number}: {message}")

    def parse(self) -> None:
        """Read, validate, and build zones and connections from the map.

        Raises:
            InvalidConfErr: If the map configuration is invalid.
        """
        seen = set()
        with open(self.file_path, 'r') as f:
            x = False
            has_content = False
            for num_lin, line in enumerate(f, start=1):
                self.last_line_number = num_lin
                line = line.split("#", 1)[0].strip()
                if not line:
                    continue
                has_content = True
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
                        num_lin,
                        f"Invalid entry '{line}'. Expected: key: value.")
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
        if not has_content:
            raise InvalidConfErr(
                "Configuration file is empty. Add the required entries: "
                f"{req_conf}. "
                f"Optional hub metadata: {zone_meta_ex}."
            )
        self.validate_config()
        self.build_zones()
        self.build_connections()

    def set_nb_drones(self, value: str, line_number: int) -> None:
        """Validate and save the configured number of drones.

        Args:
            value: Text value from the configuration file.
            line_number: Line where the value was defined.

        Raises:
            InvalidConfErr: If the value is not a positive number.
        """
        try:
            drones = int(value)
        except ValueError:
            self.raise_line_error(
                line_number, "nb_drones must be a positive number. "
                "Expected: nb_drones: <number>.")
        if drones <= 0:
            self.raise_line_error(
                line_number, "nb_drones must be greater than 0. "
                "Expected: nb_drones: <number>.")
        self.nb_drones = drones

    def validate_config(self) -> None:
        """Check that all required map settings are present.

        Raises:
            InvalidConfErr: If a required setting is missing.
        """
        line_number = max(1, self.last_line_number)
        if self.nb_drones_line is None:
            self.raise_line_error(
                line_number, "Missing required entry 'nb_drones'. "
                "Expected: nb_drones: <number>.")
        if not self.start_hub_raw or not self.end_hub_raw:
            self.raise_line_error(
                line_number, "Missing required entries 'start_hub' and/or "
                f"'end_hub'. Expected: {zone_ex}.")
        if not self.connections_raw:
            self.raise_line_error(line_number, "At least one "
                                  f"connection is required. Expected: "
                                  f"{conn_ex}.")

    def build_zones(self) -> None:
        """Create zones from parsed text and reject duplicate locations.

        Raises:
            InvalidConfErr: If a zone name or coordinate is duplicated.
        """
        coordinates: Dict[Tuple[int, int], int] = {}
        if self.start_hub_raw:
            line_number = self.start_hub_line or 0
            sz = self.parse_zone_string(self.start_hub_raw, line_number)
            self.zones[sz.name] = sz
            coordinates[(sz.x, sz.y)] = line_number
        if self.end_hub_raw:
            line_number = self.end_hub_line or 0
            ez = self.parse_zone_string(self.end_hub_raw, line_number)
            if ez.name in self.zones:
                self.raise_line_error(
                    line_number, "start_hub and end_hub cannot "
                    f" have the same name: {ez.name}"
                )
            self.zones[ez.name] = ez
            point = (ez.x, ez.y)
            if point in coordinates:
                self.raise_line_error(
                    line_number, f"Duplicate coordinate: {point}")
            coordinates[point] = line_number
        for line_number, hub_raw in self.hubs_raw:
            z = self.parse_zone_string(hub_raw, line_number)
            if z.name in self.zones:
                self.raise_line_error(line_number, f"Duplicate zone: {z.name}")
            self.zones[z.name] = z
            point = (z.x, z.y)
            if point in coordinates:
                self.raise_line_error(
                    line_number, f"Duplicate coordinate: {point}")
            coordinates[point] = line_number

    def parse_zone_string(self, raw: str, line_number: int) -> Zone:
        """Convert one zone definition into a ``Zone`` object.

        Args:
            raw: Zone text without its configuration key.
            line_number: Line where the zone was defined.

        Returns:
            The validated zone object.

        Raises:
            InvalidConfErr: If the zone definition is invalid.
        """
        b_idx = raw.find('[')
        b_idx2 = raw.find(']')
        if (b_idx == -1) != (b_idx2 == -1) or b_idx2 < b_idx:
            self.raise_line_error(
                line_number, f"Invalid hub definition '{raw}'. "
                f"Expected: {zone_ex}.")
        core = raw[:b_idx].strip() if b_idx != -1 else raw.strip()
        meta = raw[b_idx + 1: b_idx2].strip() if b_idx != -1 else ""
        added = raw[b_idx2 + 1:].strip() if b_idx != -1 else ""
        items = core.split()
        if len(items) != 3 or '-' in items[0] or ' ' in items[0]:
            self.raise_line_error(
                line_number, f"Invalid hub definition '{raw}'. "
                f"Expected: {zone_ex}.")

        try:
            name, x, y = items[0], int(items[1]), int(items[2])
        except ValueError:
            self.raise_line_error(
                line_number, f"Invalid hub coordinates in '{raw}'. "
                "Expected: <name> <x> <y>.")
        z_type, max_drones, color = "normal", 1, None
        valid_meta_data = ["zone", "color", "max_drones"]
        seen = set()
        if not meta:
            add = raw[b_idx2 + 1:] if b_idx2 != -1 else ""
            if add:
                raise self.raise_line_error(
                    line_number, f"Invalid key {add}"
                )

        if meta:
            for item in meta.split():
                if '=' not in item:
                    self.raise_line_error(
                        line_number, f"Invalid hub metadata '{item}'. "
                        f"Expected: {zone_meta_ex}.")
                k, v = item.split('=', 1)
                if k in seen:
                    self.raise_line_error(line_number, f"Duplicate key: {k}")
                if k not in valid_meta_data:
                    self.raise_line_error(
                        line_number, f"Unknown hub metadata '{k}'. "
                        f"Allowed: {zone_meta_ex}.")
                if k == 'zone':
                    z_type = v
                elif k == 'max_drones':
                    if v == "":
                        self.raise_line_error(
                            line_number, "max_drones cannot be empty. "
                            "Expected: max_drones=<number>.")
                    try:
                        max_drones = int(v)
                    except ValueError:
                        self.raise_line_error(
                            line_number, "max_drones must be a number. "
                            "Expected: max_drones=<number>.")
                    if max_drones <= 0:
                        self.raise_line_error(
                            line_number, "max_drones must be greater than 0. "
                            "Expected: max_drones=<number>.")
                elif k == 'color':
                    if v == "":
                        self.raise_line_error(
                            line_number, "color cannot be empty. "
                            "Expected: color=<value>.")
                    color = v
                seen.add(k)
            if z_type == "":
                self.raise_line_error(
                    line_number, "zone cannot be empty. "
                    "Expected: zone=<type>.")
            if z_type not in ["normal", "blocked", "restricted", "priority"]:
                self.raise_line_error(
                    line_number,
                    f"Invalid zone type '{z_type}'. Expected: zone=<type>, "
                    "where <type> is normal, blocked, restricted, or "
                    "priority.")
            if added:
                self.raise_line_error(line_number, f"Invalid key: {added}")

        return Zone(name, x, y, z_type, max_drones, color, line_number)

    def build_connections(self) -> None:
        """Create connections from parsed text and reject duplicates.

        Raises:
            InvalidConfErr: If a connection is defined more than once.
        """
        seen: Set[Tuple[str, str]] = set()
        for line_number, raw in self.connections_raw:
            c = self.parse_connection_string(raw, line_number)
            if (c.zone1, c.zone2) in seen or (c.zone2, c.zone1) in seen:
                self.raise_line_error(
                    line_number, f"Duplicate connection: {c.zone1}-{c.zone2}")
            seen.add((c.zone1, c.zone2))
            self.connections.append(c)

    def parse_connection_string(
            self, raw: str, line_number: int) -> Connection:
        """Convert one connection definition into a ``Connection`` object.

        Args:
            raw: Connection text without its configuration key.
            line_number: Line where the connection was defined.

        Returns:
            The validated connection object.

        Raises:
            InvalidConfErr: If the connection definition is invalid.
        """
        try:
            b_idx = raw.find('[')
            b_idx2 = raw.find(']')
            if (b_idx == -1) != (b_idx2 == -1) or b_idx2 < b_idx:
                self.raise_line_error(
                    line_number, f"Invalid connection '{raw}'. "
                    f"Expected: {conn_ex}.")

            core = raw[:b_idx].strip() if b_idx != -1 else raw.strip()
            meta = raw[b_idx + 1: b_idx2].strip() if b_idx != -1 else ""
            added = raw[b_idx2 + 1:].strip() if b_idx != -1 else ""
            stations = core.split('-')
            if (len(stations) != 2 or
                    stations[0] not in self.zones or
                    stations[1] not in self.zones):
                self.raise_line_error(
                    line_number, f"Invalid connection '{raw}'. "
                    f"Expected: {conn_ex}; both hubs must exist.")
            zone_1 = stations[0].strip()
            zone_2 = stations[1].strip()
            zone_1_line = self.zones[zone_1].line_number
            if (zone_1_line is not None and
                    zone_1_line > line_number):
                self.raise_line_error(
                    line_number, "Connection links is "
                    "not previously "
                    f"defined zone '{zone_1}'")
            zone_2_line = self.zones[zone_2].line_number
            if (zone_2_line is not None and
                    zone_2_line > line_number):
                self.raise_line_error(
                    line_number, "Connection links is "
                    "not previously "
                    f"defined zone '{zone_2}'"
                )
            mlc = 1
            seen = set()

            meta_data = ["max_link_capacity"]
            for item in meta.split():
                if '=' not in item:
                    self.raise_line_error(
                        line_number,
                        f"Invalid format: {item} "
                        "Expected: max_link_capacity=number.")
                k, v = item.split('=', 1)
                if k in seen:
                    self.raise_line_error(line_number, f"Duplicate key: {k}")
                if k not in meta_data:
                    self.raise_line_error(
                        line_number, f"Unknown connection metadata '{k}'. "
                        "Expected: max_link_capacity=<number>.")
                if k in meta_data:
                    value = int(v)
                    if value <= 0:
                        self.raise_line_error(
                            line_number,
                            "max_link_capacity must be greater than 0. "
                            "Expected: max_link_capacity=<number>.")
                    mlc = int(v)
                    seen.add(k)
                if added:
                    self.raise_line_error(line_number, f"Invalid key: {added}")
            return Connection(
                stations[0].strip(), stations[1].strip(), mlc, line_number)
        except ValueError:
            self.raise_line_error(
                line_number,
                "max_link_capacity must be a number. "
                "Expected: max_link_capacity=<number>.")
