from typing import Dict, List, Tuple
from models import Zone, Connection, Drone
from pathfinder import SimulationRouter
from display import print_turn
from exceptions import InvalidConfErr

class Simulation:
    def __init__(self, zones: Dict[str, Zone], connections: List[Connection], nb_drones: int, start_zone: str, end_zone: str):
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
        for c in self.connections:
            self.graph[c.zone1].append(c.zone2)
            self.graph[c.zone2].append(c.zone1)
            self.link_caps[(c.zone1, c.zone2)] = c.max_link_capacity
            self.link_caps[(c.zone2, c.zone1)] = c.max_link_capacity

    def calculate_paths(self) -> None:
        self.router = SimulationRouter(self.zones, self.graph, self.link_caps)

    def run(self) -> None:
        for name, zone in self.zones.items():
            if name in (self.start_zone, self.end_zone) and zone.type == "blocked":
                line = f"Line {zone.line_number}: " if zone.line_number else ""
                raise InvalidConfErr(
                    f"{line}Start_zone and end_zone cannot be blocked")

        while not all(d.curr_loc == self.end_zone for d in self.drones):
            self.turn += 1
            movements: List[Tuple[str, str]] = []

            for d in self.drones:
                if d.curr_loc == self.end_zone:
                    continue
                if d.state == "moving" and d.target:
                    d.curr_loc = d.target
                    d.state = "waiting"
                    movements.append((d.id, d.curr_loc))
                    d.target = None

            active_drones = [d for d in self.drones if d.curr_loc != self.end_zone and d.state == "waiting"]
            active_drones.sort(key=lambda d: 1 if d.curr_loc == self.start_zone else 0)

            for d in active_drones:
                next_step = self.router.find_dynamic_step(d.curr_loc, self.end_zone, self.turn)
                
                if next_step:
                    next_zone, arrival_turn = next_step
                    
                    if next_zone == d.curr_loc:
                        self.router.reserve_step(d.curr_loc, d.curr_loc, self.turn, arrival_turn)
                        continue

                    z_obj = self.zones[next_zone]
                    self.router.reserve_step(d.curr_loc, next_zone, self.turn, arrival_turn)

                    if z_obj.type == "restricted":
                        d.state = "moving"
                        d.target = next_zone
                        movements.append((d.id, f"{d.curr_loc}-{next_zone}"))
                    else:
                        d.curr_loc = next_zone
                        movements.append((d.id, next_zone))

            if movements:
                movements.sort(key=lambda x: int(x[0][1:]))
                print_turn(movements, self.zones)
            else:
                waiting_drones = [d for d in self.drones if d.curr_loc != self.end_zone]
                if all(d.state == "waiting" and d.curr_loc == self.start_zone for d in waiting_drones):
                    break 
                
        print(f"\nTotal moves (turns): {self.turn}")
