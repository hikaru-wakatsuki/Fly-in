from parse_input_file import DronesNetwork, Zone
from typing import Tuple, Optional, List, Set, Dict

def create_graph(drones_network: DronesNetwork) -> Dict:
    graph: Dict = {}
    all_zones: List[Zone] = [
        drones_network.start_hub, drones_network.end_hub] + drones_network.hubs
    for zone in all_zones:
        for connection in drones_network.connections:
            hub1, hub2 = connection.hubs
            if zone.name == hub1:
                graph[zone.name] = hub2
            if zone.name == hub2:
                graph[zone.name] = hub1
