from parse_input_file import DronesNetwork, Zone, ZoneType
from typing import Tuple, List, Dict, Set


def create_graph(network: DronesNetwork) -> Dict[Zone, List[Tuple[Zone, int]]]:
    graph: Dict[Zone, List[Tuple[Zone, int]]] = {}
    all_zones: List[Zone] = [network.start_hub, network.end_hub] + network.hubs
    zone_maps: Dict[str, Zone] = {zone.name: zone for zone in all_zones}

    for zone in all_zones:
        graph[zone] = []

    for connection in network.connections:
        zone_name1, zone_name2 = connection.hubs
        zone1: Zone = zone_maps[zone_name1]
        zone2: Zone = zone_maps[zone_name2]
        if zone1.zone == ZoneType.BLOCKED or zone2.zone == ZoneType.BLOCKED:
            continue
        graph[zone1].append((zone2, connection.max_link_capacity))
        graph[zone2].append((zone1, connection.max_link_capacity))

    if not check_graph(graph, network.start_hub, network.end_hub):
        raise ValueError("No valid path from start to end")
    return graph


def check_graph(
        graph: Dict[Zone, List[Tuple[Zone, int]]],
        start: Zone, end: Zone) -> bool:
    visited: Set[Zone] = {start}
    stack: List[Zone] = [start]

    while stack:
        node: Zone = stack.pop()
        if node == end:
            return True
        for neighbor, _ in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                stack.append(neighbor)
    return False
