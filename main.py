import sys
from pydantic import ValidationError
from parse_input_file import Zone, DronesNetwork, parse_input_file
from create_graph import create_graph
from path_finding import find_multiple_paths, determine_path_count
from typing import Dict, List, Tuple
from drones_scheduler import run_simulation
from output_visualize import visualize


def main() -> None:
    if len(sys.argv) != 2:
        return
    if len(sys.argv) == 2:
        try:
            network: DronesNetwork = parse_input_file(sys.argv[1])
        except (ValidationError, TypeError, ValueError) as error:
            print(error)
            return
        try:
            graph: Dict[Zone, List[Tuple[Zone, int]]] = create_graph(network)
        except ValueError as error:
            print(error)
            return
        count: int = determine_path_count(network.nb_drones)
        paths: List[List[Zone]] = find_multiple_paths(
            graph, network.start_hub, network.end_hub, count)
        logs: List[List[str]] = run_simulation(
            network.nb_drones, network.start_hub, network.end_hub,
            graph, paths)
        for log in logs:
            print(" ".join(log))
        visualize(logs, graph)


if __name__ == "__main__":
    main()
