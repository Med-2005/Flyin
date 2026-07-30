"""Find safe, capacity-aware routes for drones."""

import heapq
from typing import Dict, List, Optional, Tuple, Set
from models import Zone


PathStep = Tuple[str, int]
QueueItem = Tuple[float, int, str, List[PathStep]]


class SimulationRouter:
    """
    A router class responsible for managing drone movements, pathfinding,
    and space-time reservations within the simulation network.
    """

    def __init__(
        self, zones: Dict[str, Zone],
        graph: Dict[str, List[str]],
            link_caps: Dict[Tuple[str, str], int],
            start_zone: str, end_zone: str):
        """
        Initialize the SimulationRouter with the network
        topology and capacities.

        Args:
            zones: A dictionary mapping zone names to Zone objects.
            graph: An adjacency list representing the network connections.
            link_caps: A dictionary mapping connection tuples to their
            maximum capacities.
            start_zone: The name of the starting zone for all drones.
            end_zone: The name of the destination zone.
        """
        self.zones = zones
        self.graph = graph
        self.link_caps = link_caps
        self.start_zone = start_zone
        self.reservations: Dict[str, Dict[int, int]] = {z: {} for z in zones}
        self.link_reservations: Dict[Tuple[str, str], Dict[int, int]] = {}
        self.end_zone = end_zone

    def get_move_cost_and_turns(self, zone_type: str) -> Tuple[float, int]:
        """
        Calculate the cost and required turns for moving into a
        specific zone type.

        Args:
            zone_type: The type of the destination zone (e.g., 'restricted',
            'priority').

        Returns:
            A tuple containing the mathematical cost for the pathfinder
            and the actual turns required.
        """
        if zone_type == "restricted":
            return (2.0, 2)
        if zone_type == "priority":
            return (0.5, 1)
        return (1.0, 1)

    def is_zone_available(self, zone_name: str, target_turn: int) -> bool:
        """
        Check if a zone can accommodate an additional drone
        at a specific future turn.

        Args:
            zone_name: The name of the zone to check.
            target_turn: The future simulation turn when the drone
            expects to arrive.

        Returns:
            True if the zone has available capacity, False otherwise.
        """
        if zone_name == self.start_zone or zone_name == self.end_zone:
            return True
        zone = self.zones[zone_name]
        current_occupancy = self.reservations[zone_name].get(target_turn, 0)
        return current_occupancy < zone.max_drones

    def is_link_available(
        self, curr_zone: str, next_zone: str,
            start_turn: int, turns_needed: int) -> bool:
        """
        Determine if a connection between two zones has
        available capacity during transit.

        Args:
            curr_zone: The starting zone of the link.
            next_zone: The destination zone of the link.
            start_turn: The turn when the transit begins.
            turns_needed: The duration of the transit in turns.

        Returns:
            True if the link has sufficient capacity for the entire
            duration, False otherwise.
        """
        link = (curr_zone, next_zone)
        max_cap = self.link_caps.get(link, 1)
        if link not in self.link_caps:
            link = (next_zone, curr_zone)
            max_cap = self.link_caps.get(link, 1)

        forward = self.link_reservations.get((curr_zone, next_zone), {})
        backward = self.link_reservations.get((next_zone, curr_zone), {})

        for t in range(start_turn, start_turn + turns_needed):
            current_usage = forward.get(t, 0) + backward.get(t, 0)

            if current_usage >= max_cap:
                return False

        return True

    def reserve_step(
        self, curr_zone: str, next_zone: str, start_turn: int,
            arrival_turn: int, turns_needed: int) -> None:
        """
        Reserve capacity on a link and the destination zone for
        a drone's planned movement.

        Args:
            curr_zone: The starting zone of the movement.
            next_zone: The destination zone of the movement.
            start_turn: The turn when the movement begins.
            arrival_turn: The turn when the drone arrives at the destination.
            turns_needed: The duration of the movement across the link.
        """
        link = (curr_zone, next_zone)

        if link not in self.link_reservations:
            self.link_reservations[link] = {}

        link_reservations = self.link_reservations[link]

        for t in range(start_turn, start_turn + turns_needed):
            link_reservations[t] = link_reservations.get(t, 0) + 1

        zone_reservations = self.reservations[next_zone]
        zone_reservations[arrival_turn] = (
            zone_reservations.get(arrival_turn, 0) + 1
        )

    def dijikstra_algo(self, start: str, end: str,
                       start_turn: int,
                       max_turns: Optional[int] = None) -> Optional[PathStep]:
        """
        Find the optimal next step for a drone using
        a time-aware Dijkstra's algorithm.

        Args:
            start: The current zone of the drone.
            end: The ultimate destination zone (goal).
            start_turn: The current simulation turn.
            max_turns: The maximum number
             of turns to look ahead to prevent infinite loops.

        Returns:
            A tuple containing the next zone to move to and
            the arrival turn,
            or None if no valid path is found.
        """
        if max_turns is None:
            max_turns = len(self.zones) * 10

        pq: List[QueueItem] = [(0.0, start_turn, start, [])]
        visited: Set[Tuple[str, int]] = set()

        while pq:
            curr_cost, curr_turn, curr_zone, path = heapq.heappop(pq)

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
                    pq,
                    (
                        curr_cost + 1.0,
                        curr_turn + 1,
                        curr_zone,
                        path + [(curr_zone, curr_turn + 1)]
                    )
                )

            for neighbor in self.graph.get(curr_zone, []):
                neighbor_zone = self.zones[neighbor]

                if neighbor_zone.type == "blocked":
                    continue

                move_cost, turns_needed = self.get_move_cost_and_turns(
                    neighbor_zone.type)
                arrival_turn = curr_turn + turns_needed

                if (self.is_zone_available(neighbor, arrival_turn)
                   and self.is_link_available(
                        curr_zone,
                        neighbor,
                        curr_turn,
                        turns_needed)):

                    new_cost = curr_cost + move_cost
                    new_path = path + [(neighbor, arrival_turn)]
                    heapq.heappush(pq, (
                        new_cost, arrival_turn, neighbor, new_path))

        return None
