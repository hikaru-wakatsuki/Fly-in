import heapq
from parse_input_file import Zone, ZoneType
from typing import Tuple, Optional, List, Dict


def get_cost(zone: Zone) -> int:
    """Return movement cost based on zone type."""
    if zone.zone == ZoneType.RESTRICTED:
        return 2
    return 1


def dijkstra_path(graph: Dict[Zone, List[Tuple[Zone, int]]],
                  start: Zone, end: Zone) -> List[Zone]:
    """Compute shortest paths from start using Dijkstra."""
    distance: Dict[Zone, Optional[int]] = {node: None for node in graph}
    prev_zone: Dict[Zone, Optional[Zone]] = {node: None for node in graph}

    distance[start] = 0
    heap_queue: List[Tuple[int, Zone]] = [(0, start)]

    while heap_queue:
        current_distance, node = heapq.heappop(heap_queue)

        if current_distance > distance[node]:
            continue
        if node == end:
            break

        for neighbor, _ in graph[node]:
            cost = get_cost(neighbor)
            new_distance: int = current_distance + cost

            if distance[neighbor] is None or new_distance < distance[neighbor]:
                distance[neighbor] = new_distance
                prev_zone[neighbor] = node
                heapq.heappush(heap_queue, (new_distance, neighbor))

    path: List[Zone] = []
    cur: Optional[Zone] = end

    while cur is not None:
        path.append(cur)
        cur = prev_zone[cur]
    return path.reverse()
