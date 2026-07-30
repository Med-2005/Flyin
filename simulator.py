"""Coordinate drone movement through a configured map."""

from typing import Dict, List, Tuple
from models import Zone, Connection, Drone
from pathfinder import SimulationRouter
from display import print_turn
from exceptions import InvalidConfErr, NoPathError


class Simulation:
    """Run drones from the start zone to the end zone safely."""

    def __init__(
        self, zones: Dict[str, Zone], connections: List[Connection],
            nb_drones: int, start_zone: str, end_zone: str):
        """Create a simulation and prepare its routing data.

        Args:
            zones: Map of zone names to zone objects.
            connections: Links that connect the zones.
            nb_drones: Number of drones to simulate.
            start_zone: Name of the starting zone.
            end_zone: Name of the destination zone.
        """
        self.zones = zones
        self.connections = connections
        self.nb_drones = nb_drones
        self.start_zone = start_zone
        self.end_zone = end_zone
        self.drones = [Drone(f"D{i+1}", start_zone) for i in range(nb_drones)]
        self.turn = 0
        self.graph: Dict[str, List[str]] = {name: [] for name in self.zones}
        self.link_caps: Dict[Tuple[str, str], int] = {}
        self.build_graph()
        self.calculate_paths()

    def build_graph(self) -> None:
        """Build an undirected graph and capacity map from connections."""
        for c in self.connections:
            self.graph[c.zone1].append(c.zone2)
            self.graph[c.zone2].append(c.zone1)
            self.link_caps[(c.zone1, c.zone2)] = c.max_link_capacity
            self.link_caps[(c.zone2, c.zone1)] = c.max_link_capacity

    def calculate_paths(self) -> None:
        """Create the router used to choose safe drone movements."""
        self.router = SimulationRouter(
            self.zones, self.graph,
            self.link_caps, self.start_zone, self.end_zone)

    def run(self) -> None:
        """Run turns until every drone arrives or no progress is possible.

        Raises:
            InvalidConfErr: If the end zone is blocked.
            NoPathError: If a drone cannot reach the end zone.
        """
        for name, zone in self.zones.items():
            if ((name == self.start_zone or name == self.end_zone)
               and zone.type == "blocked"):
                line = f"Line {zone.line_number}: " if zone.line_number else ""
                raise InvalidConfErr(
                    f"{line}start_zone or end_zone cannot be blocked")

        while not all(d.curr_loc == self.end_zone for d in self.drones):
            self.turn += 1
            movements: List[Tuple[str, str]] = []

            for d in self.drones:
                if d.curr_loc == self.end_zone:
                    continue
                if d.state == "moving" and d.target:
                    if (d.arrival_turn is not None and
                            self.turn < d.arrival_turn):
                        continue
                    d.curr_loc = d.target
                    d.state = "waiting"
                    d.last_arrival_turn = self.turn
                    movements.append((d.id, d.curr_loc))
                    d.target = None

            active_drones = []

            for d in self.drones:
                if d.curr_loc != self.end_zone and d.state == "waiting":
                    if d.last_arrival_turn != self.turn:
                        active_drones.append(d)

            active_drones.sort(
                key=lambda d: 1 if d.curr_loc == self.start_zone else 0)

            for d in active_drones:
                next_step = self.router.dijikstra_algo(
                    d.curr_loc, self.end_zone, self.turn)
                if not next_step:
                    current = self.zones[d.curr_loc]
                    raise NoPathError(
                        f"Drone is stuck at '{current.name}' "
                        f"(defined on Line {current.line_number}). "
                        "No valid path to the end zone.")
                if next_step:
                    next_zone, arrival_turn = next_step
                    if next_zone == d.curr_loc:
                        self.router.reserve_step(
                            d.curr_loc, d.curr_loc, self.turn, arrival_turn, 1)
                        continue

                    zon_typ = self.zones[next_zone]
                    _, turns_needed = self.router.get_move_cost_and_turns(
                        zon_typ.type)
                    self.router.reserve_step(
                        d.curr_loc, next_zone,
                        self.turn, arrival_turn, turns_needed)

                    if zon_typ.type == "restricted":
                        d.state = "moving"
                        d.target = next_zone
                        d.arrival_turn = self.turn + 1
                        movements.append((d.id, f"{d.curr_loc}-{next_zone}"))
                    else:
                        d.curr_loc = next_zone
                        movements.append((d.id, next_zone))

            if movements:
                movements.sort(key=lambda x: int(x[0][1:]))
                print_turn(movements, self.zones)
            else:
                waiting_drones = [
                    d for d in self.drones if d.curr_loc != self.end_zone]
                if all(d.state == "waiting"
                        and d.curr_loc == self.start_zone
                        for d in waiting_drones):
                    break
