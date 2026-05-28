from typing import Dict, List, Tuple
from models import Zone, Connection, Drone
from pathfinder import dijkstra_algo
from display import print_turn

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
        self._build_graph()
        self._calculate_paths()

    def _build_graph(self) -> None:
        for c in self.connections:
            self.graph[c.zone1].append(c.zone2)
            self.graph[c.zone2].append(c.zone1)
            self.link_caps[(c.zone1, c.zone2)] = c.max_link_capacity
            self.link_caps[(c.zone2, c.zone1)] = c.max_link_capacity

    def _calculate_paths(self) -> None:
        path = dijkstra_algo(self.start_zone, self.end_zone, self.zones, self.graph)
        if path and path[0] == self.start_zone:
            for d in self.drones:
                d.path = list(path[1:])

    def run(self) -> None:
        while not all(d.curr_loc == self.end_zone for d in self.drones):
            self.turn += 1
            movements: List[Tuple[str, str]] = []
            
            zone_occ = {z: 0 for z in self.zones}
            for d in self.drones:
                if d.state == "idle" and d.curr_loc not in (self.start_zone, self.end_zone):
                    zone_occ[d.curr_loc] += 1
                    
            link_occ = {k: 0 for k in self.link_caps}
            
            for d in self.drones:
                if d.curr_loc == self.end_zone:
                    continue
                    
                if d.state == "moving" and d.target:
                    d.curr_loc = d.target
                    d.state = "idle"
                    movements.append((d.id, d.curr_loc))
                    if d.curr_loc not in (self.start_zone, self.end_zone):
                        zone_occ[d.curr_loc] += 1
                    d.target = None
                    continue

                if not d.path:
                    continue
                    
                next_zone = d.path[0]
                z_obj = self.zones[next_zone]
                link = (d.curr_loc, next_zone)
                
                can_move_link = link_occ.get(link, 0) < self.link_caps.get(link, 1)
                can_move_zone = zone_occ[next_zone] < z_obj.max_drones or next_zone == self.end_zone
                
                if can_move_link and can_move_zone:
                    if z_obj.type == "restricted":
                        d.state = "moving"
                        d.target = next_zone
                        d.path.pop(0)
                        link_occ[link] += 1
                        zone_occ[next_zone] += 1
                        if d.curr_loc not in (self.start_zone, self.end_zone):
                            zone_occ[d.curr_loc] -= 1
                        movements.append((d.id, f"{d.curr_loc}-{next_zone}"))
                    else:
                        prev_loc = d.curr_loc
                        d.curr_loc = next_zone
                        d.path.pop(0)
                        link_occ[link] += 1
                        zone_occ[next_zone] += 1
                        if prev_loc not in (self.start_zone, self.end_zone):
                            zone_occ[prev_loc] -= 1
                        movements.append((d.id, next_zone))
                        
            if movements:
                movements.sort(key=lambda x: int(x[0][1:]))
                print_turn(movements, self.zones)
            else:
                break