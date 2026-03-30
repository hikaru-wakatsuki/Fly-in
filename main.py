import sys
from pydantic import ValidationError
from parse_input_file import DronesNetwork, parse_input_file
from create_graph import create_graph
from path_finding import find_multiple_paths, determine_path_conunt


def main() -> None:
    if len(sys.argv) == 1:
        return
    if len(sys.argv) == 2:
        try:
            network: DronesNetwork = parse_input_file(sys.argv[1])
        except (ValidationError, TypeError, ValueError) as error:
            print(error)
        try:
            graph = create_graph(network)
        except ValueError as error:
            print(error)
        count: int = determine_path_conunt(network.nb_drones)
        find_multiple_paths(graph, network.start_hub, network.end_hub, count)

    if len(sys.argv) > 2:
        return
