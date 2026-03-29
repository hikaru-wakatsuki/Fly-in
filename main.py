import sys
from pydantic import ValidationError
from parse_input_file import DronesNetwork, parse_input_file


def main() -> None:
    if len(sys.argv) == 1:
        return
    if len(sys.argv) == 2:
        try:
            drones_network: DronesNetwork = parse_input_file(sys.argv[1])
            graph = create_graph(drones_network)
        except (ValidationError, TypeError, ValueError) as error:
            print(error)
    if len(sys.argv) > 2:
        return
