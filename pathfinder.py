import heapq

from typing import Dict, List, Optional, Tuple, Set
from models import Zone


class SimulationRouter:
    def __init__(
        self, zones: Dict[str, Zone],
        graph: Dict[str, List[str]],
            link_caps: Dict[Tuple[str, str], int],
            start_zone: str, end_zone: str):
        self.zones = zones
        self.graph = graph
        self.link_caps = link_caps
        self.start_zone = start_zone
        self.reservations: Dict[str, Dict[int, int]] = {z: {} for z in zones}
        self.link_reservations: Dict[Tuple[str, str], Dict[int, int]] = {}
        self.end_zone = end_zone

    def get_move_cost_and_turns(self, zone_type: str) -> Tuple[float, int]:
        if zone_type == "restricted":
            return (2.0, 2)
        if zone_type == "priority":
            return (0.5, 1)
        return (1.0, 1)

    def is_zone_available(self, zone_name: str, target_turn: int) -> bool:
        if zone_name == self.start_zone or zone_name == self.end_zone:
            return True
        zone = self.zones[zone_name]
        current_occupancy = self.reservations[zone_name].get(target_turn, 0)
        return current_occupancy < zone.max_drones

    def is_link_available(
        self, curr_zone: str, next_zone: str,
            start_turn: int, turns_needed: int) -> bool:
        link = (curr_zone, next_zone)
        max_cap = self.link_caps.get(link, 1)
        if link not in self.link_caps:
            link = (next_zone, curr_zone)
            max_cap = self.link_caps.get(link, 1)

        for t in range(start_turn, start_turn + turns_needed):
            current_usage = self.link_reservations.get((
                curr_zone, next_zone), {}).get(t, 0)
            current_usage += self.link_reservations.get((
                next_zone, curr_zone), {}).get(t, 0)

            if current_usage >= max_cap:
                return False

        return True

    def reserve_step(
        self, curr_zone: str, next_zone: str, start_turn: int,
            arrival_turn: int, turns_needed: int):
        link = (curr_zone, next_zone)

        if link not in self.link_reservations:
            self.link_reservations[link] = {}

        for t in range(start_turn, start_turn + turns_needed):
            self.link_reservations[link][t] = self.link_reservations[link].get(
                t, 0) + 1

        self.reservations[next_zone][arrival_turn] = self.reservations[
            next_zone].get(arrival_turn, 0) + 1

    def find_dynamic_step(
        self, start: str, end: str, start_turn: int,
            max_turns: int = 1000) -> Optional[Tuple[str, int]]:
        pq = [(0.0, start_turn, start, [])]
        visited: Set[Tuple[str, int]] = set()

        # pq = [(0.0, 1, start, [])]
        while pq:
            curr_cost, curr_turn, curr_zone, path = heapq.heappop(pq)
            # curr_cost = 0, curr_turn = 1, curr_zone = start
            # path = []

            if curr_turn > start_turn + max_turns:
                continue

            if (curr_zone, curr_turn) in visited:
                continue
            visited.add((curr_zone, curr_turn))

            if curr_zone == end:
                if path:
                    return path[0]
                return None

            if self.is_zone_available(curr_zone, curr_turn + 1):
                heapq.heappush(
                    pq, (curr_cost + 1.0, curr_turn + 1,
                         curr_zone, path + [(curr_zone, curr_turn + 1)]))

            for neighbor in self.graph.get(curr_zone, []):
                neighbor_zone = self.zones[neighbor]

                if neighbor_zone.type == "blocked":
                    continue

                move_cost, turns_needed = self.get_move_cost_and_turns(
                    neighbor_zone.type)
                arrival_turn = curr_turn + turns_needed

                if self.is_zone_available(
                    neighbor, arrival_turn) and self.is_link_available(
                        curr_zone, neighbor, curr_turn, turns_needed):
                    new_cost = curr_cost + move_cost
                    new_path = path + [(neighbor, arrival_turn)]
                    heapq.heappush(pq, (
                        new_cost, arrival_turn, neighbor, new_path))

        return None
