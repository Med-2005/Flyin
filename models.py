from typing import Optional, List


class Zone:
    def __init__(self, name: str, x: int, y: int, zone_type: str,
                 max_drones: int, color: Optional[str],
                 line_number: Optional[int] = None):
        self.name = name
        self.x = x
        self.y = y
        self.type = zone_type
        self.max_drones = max_drones
        self.color = color
        self.line_number = line_number


class Connection:
    def __init__(self, zone1: str, zone2: str, max_link_capacity: int,
                 line_number: Optional[int] = None):
        self.zone1 = zone1
        self.zone2 = zone2
        self.max_link_capacity = max_link_capacity
        self.line_number = line_number


class Drone:
    def __init__(self, drone_id: str, curr_loc: str, state: str = "waiting"):
        self.id = drone_id
        self.curr_loc = curr_loc
        self.state = state
        self.target: Optional[str] = None
        self.path: List[str] = []
