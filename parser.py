import sys
import re
from typing import Dict, List, Optional, Set, FrozenSet
from exceptions import InvalidConfigError
from models import Zone, Connection

ZONE_NAME = r"([^\s\-]+)"
ZONE_PATTERN = re.compile(
    rf"^{ZONE_NAME}\s+(\d+)\s+(\d+)(?:\s+\[([^\]]*)\])?$"
)
CONNECTION_PATTERN = re.compile(
    rf"^{ZONE_NAME}-{ZONE_NAME}(?:\s+\[([^\]]*)\])?$"
)

VALID_ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}

class MapParser:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self._nb_drones_raw: Optional[str] = None
        self._start_hub_raw: Optional[str] = None
        self._end_hub_raw:   Optional[str] = None
        self._hubs_raw:      List[str]     = []
        self._connections_raw: List[str]   = []
        self.nb_drones:  int                       = 0
        self.zones:      Dict[str, Zone]           = {}
        self.connections: List[Connection]         = []
        self._seen_connections: Set[FrozenSet[str]] = set()

    def parse(self) -> None:
        try:
            self._read_file()
            self._validate_config()
            self._build_objects()
        except InvalidConfigError as e:
            print(f"Configuration Error: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print(f"Error: File '{self.file_path}' not found.")
            sys.exit(1)

    def _read_file(self) -> None:
        with open(self.file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                self._dispatch_line(line)

    def _dispatch_line(self, line: str) -> None:
        if ":" not in line:
            raise InvalidConfigError(f"Invalid line format (missing ':'): {line}")

        key, _, value = line.partition(":")
        key   = key.strip().lower()
        value = value.strip()

        handlers = {
            "nb_drones":  self._handle_nb_drones,
            "start_hub":  self._handle_start_hub,
            "end_hub":    self._handle_end_hub,
            "hub":        self._handle_hub,
            "connection": self._handle_connection,
        }

        if key not in handlers:
            raise InvalidConfigError(f"Unknown key: '{key}'")

        handlers[key](value)

    def _handle_nb_drones(self, value: str) -> None:
        if self._nb_drones_raw is not None:
            raise InvalidConfigError("'nb_drones' is defined more than once")
        self._nb_drones_raw = value

    def _handle_start_hub(self, value: str) -> None:
        if self._start_hub_raw is not None:
            raise InvalidConfigError("'start_hub' is defined more than once")
        self._start_hub_raw = value

    def _handle_end_hub(self, value: str) -> None:
        if self._end_hub_raw is not None:
            raise InvalidConfigError("'end_hub' is defined more than once")
        self._end_hub_raw = value

    def _handle_hub(self, value: str) -> None:
        self._hubs_raw.append(value)

    def _handle_connection(self, value: str) -> None:
        self._connections_raw.append(value)

    def _validate_config(self) -> None:
        missing = []
        if self._nb_drones_raw is None:
            missing.append("nb_drones")
        if self._start_hub_raw is None:
            missing.append("start_hub")
        if self._end_hub_raw is None:
            missing.append("end_hub")
        if missing:
            raise InvalidConfigError(f"Missing mandatory keys: {missing}")

        try:
            drones = int(str(self._nb_drones_raw))
            if drones <= 0:
                raise InvalidConfigError("'nb_drones' must be greater than 0")
            self.nb_drones = drones
        except ValueError:
            raise InvalidConfigError(
                f"'nb_drones' must be a valid integer, got: '{self._nb_drones_raw}'"
            )

        start_name = str(self._start_hub_raw).split()[0]
        end_name   = str(self._end_hub_raw).split()[0]
        if start_name == end_name:
            raise InvalidConfigError(
                f"'start_hub' and 'end_hub' cannot be the same zone: '{start_name}'"
            )

        if not self._connections_raw:
            raise InvalidConfigError("At least one connection is required")

    def _build_objects(self) -> None:
        self._parse_zone(str(self._start_hub_raw))
        self._parse_zone(str(self._end_hub_raw))
        for hub_raw in self._hubs_raw:
            self._parse_zone(hub_raw)

        for conn_raw in self._connections_raw:
            self._parse_connection(conn_raw)

    def _parse_zone(self, raw: str) -> None:
        match = ZONE_PATTERN.match(raw)
        if not match:
            raise InvalidConfigError(f"Invalid zone format: '{raw}'")

        name, x_str, y_str, meta_str = match.groups()

        if name in self.zones:
            raise InvalidConfigError(f"Duplicate zone name: '{name}'")

        x, y       = int(x_str), int(y_str)
        zone_type  = "normal"
        color      = None
        max_drones = 1

        if meta_str:
            zone_type, color, max_drones = self._parse_zone_meta(
                meta_str, zone_type, color, max_drones
            )

        self.zones[name] = Zone(name, x, y, zone_type, max_drones, color)

    def _parse_zone_meta(
        self,
        meta_str: str,
        zone_type: str,
        color: Optional[str],
        max_drones: int,
    ):
        for part in meta_str.split():
            if "=" not in part:
                continue
            k, v = part.split("=", 1)

            if k == "zone":
                if v not in VALID_ZONE_TYPES:
                    raise InvalidConfigError(
                        f"Invalid zone type '{v}'. "
                        f"Valid types: {sorted(VALID_ZONE_TYPES)}"
                    )
                zone_type = v

            elif k == "color":
                color = v

            elif k == "max_drones":
                max_drones = self._parse_positive_int(v, "max_drones")

        return zone_type, color, max_drones

    def _parse_connection(self, raw: str) -> None:
        match = CONNECTION_PATTERN.match(raw)
        if not match:
            raise InvalidConfigError(f"Invalid connection format: '{raw}'")

        name1, name2, meta_str = match.groups()

        if name1 == name2:
            raise InvalidConfigError(
                f"A zone cannot connect to itself: '{name1}'"
            )

        for name in (name1, name2):
            if name not in self.zones:
                raise InvalidConfigError(
                    f"Connection references unknown zone: '{name}'"
                )

        conn_pair = frozenset([name1, name2])
        if conn_pair in self._seen_connections:
            raise InvalidConfigError(
                f"Duplicate connection between '{name1}' and '{name2}'"
            )
        self._seen_connections.add(conn_pair)

        max_link_capacity = 1
        if meta_str:
            for part in meta_str.split():
                if "=" not in part:
                    continue
                k, v = part.split("=", 1)
                if k == "max_link_capacity":
                    max_link_capacity = self._parse_positive_int(v, "max_link_capacity")

        zone1 = self.zones[name1]
        zone2 = self.zones[name2]
        self.connections.append(Connection(zone1, zone2, max_link_capacity))

    @staticmethod
    def _parse_positive_int(value: str, field_name: str) -> int:
        try:
            result = int(value)
            if result <= 0:
                raise ValueError
            return result
        except ValueError:
            raise InvalidConfigError(
                f"'{field_name}' must be a positive integer, got: '{value}'"
            )
            