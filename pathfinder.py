import heapq
import math
from typing import Dict, List, Optional, Tuple
from models import Zone


def get_move_cost(zone_type: str) -> float:
    if zone_type == "restricted":
        return 2.0
    if zone_type == "priority":
        return 0.5
    return 1.0


def dijkstra_algo(start: str, end: str,
                  zones: Dict[str, Zone],
                  graph: Dict[str, List[str]],
                  zone_penalties: Dict[
                    str, float] = None) -> Optional[List[str]]:

    if zone_penalties is None:
        zone_penalties = {}

    distances: Dict[str, float] = {z: math.inf for z in zones}
    previous: Dict[str, Optional[str]] = {z: None for z in zones}
    distances[start] = 0.0

    pq = [(0.0, start)]

    while pq:
        curr_dist, curr_zone = heapq.heappop(pq)

        if curr_zone == end:
            break

        if curr_dist > distances[curr_zone]:
            continue
        # "Skip exploring this path
        # if we have already found a shorter,
        #  faster route to the current zone."

        for neighbor in graph.get(curr_zone, []):
            z_obj = zones[neighbor]

            if z_obj.type == "blocked":
                continue

            penalty = zone_penalties.get(
                neighbor, 0.0) if neighbor != end else 0.0

            cost = get_move_cost(z_obj.type) + penalty
            new_dist = curr_dist + cost

            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                previous[neighbor] = curr_zone
                heapq.heappush(pq, (new_dist, neighbor))

    if distances[end] == math.inf:
        return None

    path = []
    curr: Optional[str] = end
    while curr is not None:
        path.append(curr)
        curr = previous[curr]

    path.reverse()
    return path

# [goal, E, C, A, Hub]
# [hub, a, c, e, goal]


def get_diverse_paths(start: str, end: str,
                      zones: Dict[str, Zone],
                      graph: Dict[str, List[str]],
                      max_paths: int = 2) -> List[List[str]]:
    paths = []
    seen_paths = set()
    penalties: Dict[str, float] = {}

    for _ in range(max_paths * 6):
        path = dijkstra_algo(start, end, zones, graph, penalties)
        if not path:
            break

        path_key = tuple(path)
        if path_key not in seen_paths:
            paths.append(path)
            seen_paths.add(path_key)

        for zone in path:
            if zone != start and zone != end:
                capacity = zones[zone].max_drones
                penalties[zone] = penalties.get(
                    zone, 0.0) + (10.0 / capacity)

    def path_score(path: List[str]) -> Tuple[int, float]:
        cost = sum(get_move_cost(zones[zone].type) for zone in path[1:])
        return len(path), cost

    paths.sort(key=path_score)
    return paths[:max_paths]
