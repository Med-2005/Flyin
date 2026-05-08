import sys
import re
from typing import Dict, List, Optional, Set, FrozenSet
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
        
        self.zones: Dict[str, Zone] = {}
        self.connections: List[Connection] = []
        self.seen_connections: Set[FrozenSet[str]] = set()

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
                        self.set_nb_drones(value)
                    elif key == 'start_hub':
                        if self.start_hub_raw is not None:
                            raise InvalidConfigError("Multiple start_hub defined")
                        self.start_hub_raw = value
                    elif key == 'end_hub':
                        if self.end_hub_raw is not None:
                            raise InvalidConfigError("Multiple end_hub defined")
                        self.end_hub_raw = value
                    elif key == 'hub':
                        self.hubs_raw.append(value)
                    elif key == 'connection':
                        self.connections_raw.append(value)
                    else:
                        raise InvalidConfigError(f"Unknown key: {key}")
            
            self.validate_config()
            self.build_objects()
            
        except InvalidConfigError as e:
            print(f"Configuration Error: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print(f"Error: File '{self.file_path}' not found.")
            sys.exit(1)

    def set_nb_drones(self, value: str) -> None:
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

    def build_objects(self) -> None:
        if self.start_hub_raw:
            self.parse_zone(self.start_hub_raw)
        if self.end_hub_raw:
            self.parse_zone(self.end_hub_raw)
            
        for hub_raw in self.hubs_raw:
            self.parse_zone(hub_raw)
            
        for conn_raw in self.connections_raw:
            self.parse_connection(conn_raw)

    def parse_zone(self, raw_str: str) -> None:
        match = re.match(r"^([^\s-]+)\s+(\d+)\s+(\d+)(?:\s+\[(.*)\])?$", raw_str)
        if not match:
            raise InvalidConfigError(f"Invalid zone format: {raw_str}")
        
        name, x_str, y_str, meta_str = match.groups()
        
        if name in self.zones:
            raise InvalidConfigError(f"Duplicate zone name: {name}")
            
        x, y = int(x_str), int(y_str)
        zone_type = 'normal'
        color = None
        max_drones = 1
        
        if meta_str:
            for part in meta_str.split():
                if '=' in part:
                    k, v = part.split('=', 1)
                    if k == 'zone':
                        if v not in ['normal', 'blocked', 'restricted', 'priority']:
                            raise InvalidConfigError(f"Invalid zone type: {v}")
                        zone_type = v
                    elif k == 'color':
                        color = v
                    elif k == 'max_drones':
                        try:
                            max_drones = int(v)
                            if max_drones <= 0:
                                raise ValueError
                        except ValueError:
                            raise InvalidConfigError(f"max_drones must be a positive integer: {v}")

        self.zones[name] = Zone(name, x, y, zone_type, max_drones, color)

    def parse_connection(self, raw_str: str) -> None:
        match = re.match(r"^([^\s-]+)-([^\s-]+)(?:\s+\[(.*)\])?$", raw_str)
        if not match:
            raise InvalidConfigError(f"Invalid connection format: {raw_str}")
            
        name1, name2, meta_str = match.groups()
        
        if name1 == name2:
            raise InvalidConfigError(f"Zone cannot connect to itself: {name1}")
            
        if name1 not in self.zones or name2 not in self.zones:
            raise InvalidConfigError(f"Connection references unknown zones: {name1}-{name2}")
            
        conn_pair = frozenset([name1, name2])
        if conn_pair in self.seen_connections:
            raise InvalidConfigError(f"Duplicate connection found between {name1} and {name2}")
        self.seen_connections.add(conn_pair)
            
        max_link_capacity = 1
        
        if meta_str:
            for part in meta_str.split():
                if '=' in part:
                    k, v = part.split('=', 1)
                    if k == 'max_link_capacity':
                        try:
                            max_link_capacity = int(v)
                            if max_link_capacity <= 0:
                                raise ValueError
                        except ValueError:
                            raise InvalidConfigError(f"max_link_capacity must be a positive integer: {v}")
                        
        zone1 = self.zones[name1]
        zone2 = self.zones[name2]
        self.connections.append(Connection(zone1, zone2, max_link_capacity))