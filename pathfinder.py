import heapq
import math
from typing import Dict, List, Optional
from models import Zone

def get_move_cost(zone_type: str) -> float:
    if zone_type == "restricted":
        return 2.0
    if zone_type == "priority":
        return 0.5
    return 1.0

def dijkstra_algo(start: str, end: str, zones: Dict[str, Zone], graph: Dict[str, List[str]]) -> Optional[List[str]]:
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
            
        for neighbor in graph.get(curr_zone, []):
            z_obj = zones[neighbor]
            if z_obj.type == "blocked":
                continue
                
            cost = get_move_cost(z_obj.type)
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