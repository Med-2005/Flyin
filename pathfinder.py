import heapq
import math
from typing import Dict, List, Optional, Tuple, Set

class SimulationRouter:
    def __init__(self, zones: Dict[str, 'Zone'], graph: Dict[str, List[str]], link_caps: Dict[Tuple[str, str], int]):
        self.zones = zones
        self.graph = graph
        self.link_caps = link_caps
        self.reservations: Dict[str, Dict[int, int]] = {z: {} for z in zones}
        self.link_reservations: Dict[Tuple[str, str], Dict[int, int]] = {}

    def get_move_cost_and_turns(self, zone_type: str) -> Tuple[float, int]:
        if zone_type == "restricted":
            return (2.0, 2)
        if zone_type == "priority":
            return (0.5, 1)
        return (1.0, 1)

    def is_zone_available(self, zone_name: str, target_turn: int) -> bool:
        zone = self.zones[zone_name]
        current_occupancy = self.reservations[zone_name].get(target_turn, 0)
        return current_occupancy < zone.max_drones

    def is_link_available(self, curr_zone: str, next_zone: str, target_turn: int) -> bool:
        link = (curr_zone, next_zone)
        max_cap = self.link_caps.get(link, 1)
        if link not in self.link_caps:
            link = (next_zone, curr_zone)
            max_cap = self.link_caps.get(link, 1)
        
        current_usage = self.link_reservations.get((curr_zone, next_zone), {}).get(target_turn, 0)
        current_usage += self.link_reservations.get((next_zone, curr_zone), {}).get(target_turn, 0)
        
        return current_usage < max_cap

    def reserve_step(self, curr_zone: str, next_zone: str, start_turn: int, arrival_turn: int):
        link = (curr_zone, next_zone)
        
        if link not in self.link_reservations:
            self.link_reservations[link] = {}
        self.link_reservations[link][start_turn] = self.link_reservations[link].get(start_turn, 0) + 1
        
        self.reservations[next_zone][arrival_turn] = self.reservations[next_zone].get(arrival_turn, 0) + 1

    def find_dynamic_step(self, start: str, end: str, start_turn: int) -> Optional[Tuple[str, int]]:
        pq = [(0.0, start_turn, start, [])]
        visited: Set[Tuple[str, int]] = set()

        while pq:
            curr_cost, curr_turn, curr_zone, path = heapq.heappop(pq)

            if (curr_zone, curr_turn) in visited:
                continue
            visited.add((curr_zone, curr_turn))

            if curr_zone == end:
                if path:
                    return path[0]
                return None

            if self.is_zone_available(curr_zone, curr_turn + 1):
                heapq.heappush(pq, (curr_cost + 1.0, curr_turn + 1, curr_zone, path + [(curr_zone, curr_turn + 1)]))

            for neighbor in self.graph.get(curr_zone, []):
                neighbor_zone = self.zones[neighbor]

                if neighbor_zone.type == "blocked":
                    continue

                move_cost, turns_needed = self.get_move_cost_and_turns(neighbor_zone.type)
                arrival_turn = curr_turn + turns_needed

                if self.is_zone_available(neighbor, arrival_turn) and self.is_link_available(curr_zone, neighbor, curr_turn):
                    new_cost = curr_cost + move_cost
                    new_path = path + [(neighbor, arrival_turn)]
                    heapq.heappush(pq, (new_cost, arrival_turn, neighbor, new_path))

        return None