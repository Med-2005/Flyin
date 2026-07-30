"""Define the data objects used by the drone simulation."""

from typing import Optional, List


class Zone:
    """Store the name, location, type, and capacity of a map zone."""

    def __init__(self, name: str, x: int, y: int, zone_type: str,
                 max_drones: int, color: Optional[str],
                 line_number: Optional[int] = None):
        """Create a zone from its configuration values.

        Args:
            name: Unique name of the zone.
            x: Horizontal position of the zone.
            y: Vertical position of the zone.
            zone_type: Movement rule for the zone.
            max_drones: Maximum number of drones allowed in the zone.
            color: Optional display color for the zone.
            line_number: Source line where the zone was defined.
        """
        self.name = name
        self.x = x
        self.y = y
        self.type = zone_type
        self.max_drones = max_drones
        self.color = color
        self.line_number = line_number


class Connection:
    """Store a connection and its maximum drone capacity."""

    def __init__(self, zone1: str, zone2: str, max_link_capacity: int,
                 line_number: Optional[int] = None):
        """Create a connection between two zones.

        Args:
            zone1: Name of the first connected zone.
            zone2: Name of the second connected zone.
            max_link_capacity: Maximum drones allowed on the link per turn.
            line_number: Source line where the connection was defined.
        """
        self.zone1 = zone1
        self.zone2 = zone2
        self.max_link_capacity = max_link_capacity
        self.line_number = line_number


class Drone:
    """Store a drone's current location and movement state."""

    def __init__(self, drone_id: str, curr_loc: str, state: str = "waiting"):
        """Create a drone at a location.

        Args:
            drone_id: Unique identifier for the drone.
            curr_loc: Name of the drone's current zone.
            state: Current movement state. Defaults to ``"waiting"``.
        """
        self.id = drone_id
        self.curr_loc = curr_loc
        self.state = state
        self.target: Optional[str] = None
        self.arrival_turn: Optional[int] = None
        self.last_arrival_turn: Optional[int] = None
        self.path: List[str] = []
