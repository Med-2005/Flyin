*This project has been created as part of the 42 curriculum by mryahi-e.*

# Flyin

## Description

**Flyin** is a terminal-based drone-routing simulator. It reads a map of hubs and
bidirectional connections, finds routes from a start hub to an end hub, and then
simulates the drones moving turn by turn while respecting hub occupancy and link
capacity limits.

The goal is to model the practical constraints of coordinated autonomous travel:
some hubs are blocked, some are slower to cross, some are faster to use, and each
hub or connection can limit how many drones it accepts in a turn. Sample maps are
provided under `maps/`, from simple routes to capacity and maze challenges.

## Features

- Validates the configuration and reports malformed maps, duplicate zones or
  connections, unknown keys, and invalid capacities.
- Builds an undirected graph from the map configuration.
- Avoids blocked hubs and uses weighted Dijkstra pathfinding.
- Gives restricted hubs a higher routing cost and priority hubs a lower cost.
- Computes up to two route alternatives and distributes drones between them.
- Enforces per-hub occupancy and per-link, per-turn capacity during simulation.
- Displays each turn in the terminal and reports the final number of turns.

## Instructions

### Requirements

- Python 3.11 or newer
- The [`rich`](https://rich.readthedocs.io/) Python package, used for coloured
  terminal output

Install the development dependencies:

```sh
make install
```

Run the default map (`setting.txt`):

```sh
make run
```

Or run any map directly:

```sh
python3 main.py maps/easy/01_linear_path.txt
```

Useful development commands:

```sh
make lint          # flake8 and mypy checks
make lint-strict   # stricter mypy checks
make debug         # start Python's debugger
make clean         # remove Python and mypy caches
```

## Map format

Configuration files are plain text. Empty lines and text after `#` are ignored.
Every active line has the form `key: value`.

```text
nb_drones: 2
start_hub: start 0 0 [color=green]
hub: waypoint 1 0 [zone=normal color=blue max_drones=1]
end_hub: goal 2 0 [color=red]
connection: start-waypoint [max_link_capacity=1]
connection: waypoint-goal
```

| Key | Meaning |
| --- | --- |
| `nb_drones` | Positive number of drones to simulate. |
| `start_hub`, `end_hub`, `hub` | A zone: `name x y`, optionally followed by metadata in brackets. |
| `connection` | A bidirectional link: `zone_a-zone_b`, optionally with `max_link_capacity`. |

Zone metadata accepts `zone`, `color`, and `max_drones`. The zone type is one of:

- `normal` — standard traversal cost of `1`.
- `blocked` — excluded from route search.
- `restricted` — traversal cost of `2`; a drone spends one turn in transit before
  arriving at the hub.
- `priority` — traversal cost of `0.5`, making it preferable during pathfinding.

The default hub capacity and link capacity are both `1`. Start and end hubs may
not be blocked.

## Algorithm and implementation strategy

The parser first removes comments, validates each known directive, turns zone
definitions into `Zone` objects, and turns connections into `Connection` objects.
The simulator then creates an adjacency list and records link capacities in both
directions.

Routing uses Dijkstra's algorithm with a priority queue. Moving into a normal hub
costs `1`, a restricted hub costs `2`, and a priority hub costs `0.5`; blocked hubs
are skipped. The destination has no additional penalty. After the first shortest
path is found, intermediate restricted hubs receive a large temporary penalty
before a second search. This produces up to two more diverse paths, which are
assigned to drones in round-robin order.

Simulation advances in discrete turns. For every turn it:

1. Completes drones that were already crossing a restricted hub.
2. Counts current hub occupancy and resets per-turn link usage.
3. Processes each remaining drone's next route step only if its destination hub
   and its outgoing link both have available capacity.
4. Prints successful movements in numerical drone-ID order.

Normal and priority moves arrive in the same turn. A move into a restricted hub
is shown as `source-destination` and is completed on the following turn. The
simulation stops when every drone has reached the destination, or when an entire
turn makes no movement.

## Visual representation

Flyin represents the simulation as one line per turn. Each token is written as
`D<id>-<destination>`; tokens on the same line moved during the same turn. This
makes parallel movement and bottlenecks easy to compare at a glance. If a zone
has a `color` metadata value, its destination token is rendered using that colour
through Rich, helping distinguish paths, hazards, and endpoints without changing
the map syntax. Terminals without colour support still receive readable text.

## Example

Input: `maps/easy/01_linear_path.txt`

```text
nb_drones: 2
start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]
connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

Command:

```sh
python3 main.py maps/easy/01_linear_path.txt
```

Expected output (colour omitted here):

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal

Total moves (turns): 4
```

## Project layout

```text
main.py        Command-line entry point
parser.py      Configuration parsing and validation
pathfinder.py  Weighted route search and path diversification
simulator.py   Turn-based movement and capacity enforcement
display.py     Rich-based terminal rendering
models.py      Zone, connection, and drone data models
maps/          Ready-to-run example configurations
```

## Resources

- [Python documentation: `heapq`](https://docs.python.org/3/library/heapq.html)
  — priority queue used by Dijkstra's algorithm.
- [Dijkstra's algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
  — shortest-path algorithm behind route selection.
- [Rich documentation](https://rich.readthedocs.io/) — terminal colour markup and
  rendering.
- [Python typing documentation](https://docs.python.org/3/library/typing.html) —
  type annotations used throughout the codebase.

### AI usage

AI was used to inspect the existing source code and sample maps, verify a sample
execution, and draft this README. It was not used to modify the simulator's
Python implementation, routing algorithm, or map files.
