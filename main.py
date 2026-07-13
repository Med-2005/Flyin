import sys
from parser import MapParser
from simulator import Simulation


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python main.py <map_file>")
        sys.exit(1)

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
    print(f"\nTotal moves (turns): {sim.turn}")


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        print(f"Errors happens: {e}")
