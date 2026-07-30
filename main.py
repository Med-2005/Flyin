"""Run a drone simulation from a map configuration file."""

import sys
from parser import MapParser
from simulator import Simulation


def main() -> None:
    """Read the map file argument, build the simulation, and run it.

    Returns:
        None.
    """
    if len(sys.argv) != 2:
        print("Usage: python main.py <map_file>")
        sys.exit(0)

    map_file = sys.argv[1]

    parser = MapParser(map_file)
    parser.parse()

    if parser.start_hub_raw:
        start_name = parser.start_hub_raw.split()[0]
    else:
        ""
    if parser.end_hub_raw:
        end_name = parser.end_hub_raw.split()[0]
    else:
        ""
    sim = Simulation(
        parser.zones, parser.connections, parser.nb_drones,
        start_name, end_name)
    sim.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(0)
    except KeyboardInterrupt:
        print("Exit Safely")
        sys.exit(0)
