from typing import Dict, List, Tuple
from models import Zone

COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "gray": "\033[90m",
    "reset": "\033[0m"
}

def print_turn(movements: List[Tuple[str, str]], zones: Dict[str, Zone]) -> None:
    if not movements:
        return
    
    output = []
    for drone_id, dest in movements:
        dest_name = dest.split('-')[-1] if '-' in dest else dest
        zone = zones.get(dest_name)
        
        color_code = ""
        reset_code = ""
        if zone and zone.color and zone.color.lower() in COLORS:
            color_code = COLORS[zone.color.lower()]
            reset_code = COLORS["reset"]
            
        output.append(f"{drone_id}-{color_code}{dest}{reset_code}")
        
    print(" ".join(output))