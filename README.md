*This project has been created as part of the 42 curriculum by hikaru.*

# Fly-in

## Description

Fly-in is a Python project that simulates a fleet of drones moving from a single start hub to a single end hub through a graph of connected zones.

The goal is to deliver all drones in as few simulation turns as possible while respecting:

- zone capacities (`max_drones`)
- connection capacities (`max_link_capacity`)
- blocked zones
- restricted zones with a 2-turn movement cost
- priority zones that should be favored by the routing strategy

The project includes:

- a parser for the input map format
- a graph builder
- a pathfinding layer
- a turn-based scheduling engine
- a graphical visualization built with `pygame`

## Features

- Object-oriented domain models with type hints
- Input validation with clear parsing errors
- Graph construction without external graph libraries
- Weighted pathfinding that accounts for zone types and congestion
- Simultaneous multi-drone simulation with occupancy and link-capacity checks
- Graphical visualization of zones, links, and drone movements

## Project Structure

- `main.py`: entry point of the program
- `parse_input_file.py`: parsing, validation, and data models
- `create_graph.py`: graph construction and reachability validation
- `path_finding.py`: shortest-path computation with custom costs
- `drones_scheduler.py`: turn scheduling and simulation logic
- `output_visualize.py`: `pygame` visualization
- `input_file.txt`: sample input map
- `Makefile`: install, run, debug, clean, and lint helpers

## Instructions

### Requirements

- Python 3.10 or later
- `pip`

### Installation

```bash
make install
```

### Run

```bash
make run
```

This runs:

```bash
python3 main.py input_file.txt
```

### Debug

```bash
make debug
```

### Lint

```bash
make lint
```

Optional strict type checking:

```bash
make lint-strict
```

### Clean

```bash
make clean
```

## Input Format

The simulation reads a text file describing the drone network.

Example:

```txt
nb_drones: 5
start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: roof2 6 2 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
connection: hub-roof1
connection: hub-corridorA
connection: roof1-roof2
connection: roof2-goal
```

### Supported metadata

- Zone metadata:
  - `zone=normal|blocked|restricted|priority`
  - `color=<name>`
  - `max_drones=<positive integer>`
- Connection metadata:
  - `max_link_capacity=<positive integer>`

### Parsing rules

- zone names must be unique
- coordinates must be unique
- zone names cannot contain spaces or dashes
- connections must reference existing zones
- duplicate connections are rejected
- invalid metadata raises an error

## Output Format

The simulation prints one line per turn.

Each movement uses the format:

```txt
D<ID>-<zone>
```

For a movement toward a restricted zone, the log may temporarily show the drone on the connection path during transit:

```txt
D<ID>-<from>-<to>
```

Only drones that move during a turn are printed on that line.

## Algorithm Choices

### 1. Parsing and validation

The parser builds strongly typed objects for:

- `Zone`
- `Connection`
- `DronesNetwork`

Validation is performed during parsing so invalid maps are rejected before the simulation starts. This avoids running scheduling logic on inconsistent data.

### 2. Graph construction

The network is converted into an adjacency-list graph. Blocked zones are excluded from usable routes. A reachability check confirms that at least one valid path exists from the start hub to the end hub.

### 3. Pathfinding strategy

The pathfinding layer uses a Dijkstra-style shortest-path search with custom costs:

- base movement cost for every step
- additional cost for restricted zones
- additional cost for low-capacity zones
- tie-breaking in favor of priority zones

This heuristic does not only search for the shortest geometric path. It tries to reduce congestion and improve throughput across the full simulation.

### 4. Turn scheduling

All drones are simulated turn by turn. During each turn, the scheduler:

- resolves drones already in transit
- checks whether each drone can move
- respects zone occupancy limits
- respects connection capacity limits
- prevents two drones from entering a full zone
- allows waiting when movement is not possible

When a planned move is blocked, the drone can recompute a path using penalties derived from current congestion. This makes the simulation more adaptive on overlapping routes.

### 5. Restricted-zone handling

Restricted zones require 2 turns to enter. The implementation models this as a transit state:

- on the first turn, the drone leaves the current zone and occupies the connection
- on the next turn, it must arrive at the restricted zone

This behavior matches the project rule that drones cannot wait indefinitely on a connection toward a restricted zone.

## Complexity

The exact runtime depends on the map and the number of turns, but the main costs are:

- parsing: linear in the number of input lines
- graph construction: linear in the number of zones and connections
- shortest-path computation: quadratic in the number of zones in the current implementation
- simulation: proportional to the number of turns multiplied by the number of drones

Because paths may be recomputed during congestion, performance depends on how often rerouting happens. In practice, this tradeoff improves solution quality on contested maps.

## Visual Representation

The project includes a `pygame` visualization to make the simulation easier to understand.

It displays:

- zone positions based on input coordinates
- links between zones
- zone colors from metadata
- visual distinction for restricted and priority zones
- larger outlines for zones with higher capacity
- animated drone positions between turns
- a turn counter and legend

This visual layer helps reviewers quickly understand:

- which paths are used
- where congestion appears
- how restricted movements behave
- whether capacities are respected during the simulation

## Error Handling

The project is designed to fail early with explicit error messages when:

- the input file cannot be opened
- the map format is invalid
- a zone or connection contains invalid metadata
- duplicate zones or connections are found
- no valid route exists from start to end

## Resources

- [Python documentation](https://docs.python.org/3/)
- [Pygame documentation](https://www.pygame.org/docs/)
- [mypy documentation](https://mypy.readthedocs.io/)
- [flake8 documentation](https://flake8.pycqa.org/)
- [Dijkstra's algorithm overview](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)

### AI Usage

AI was used as a support tool for:

- improving documentation structure
- reviewing wording and clarity
- helping summarize the project requirements into README form

AI was not used as a blind code replacement. All generated or suggested content was reviewed, understood, and adapted before being kept in the project.
