from parse_input_file import Zone, ZoneType
from typing import Tuple, Optional, List, Dict, Set


def get_cost(zone: Zone) -> int:
    """Return movement cost based on zone type."""
    if zone.zone == ZoneType.RESTRICTED:
        return 2
    return 1


def dijkstra_path(graph: Dict[Zone, List[Tuple[Zone, int]]],
                  start: Zone, end: Zone) -> List[Zone]:
    """Compute shortest paths from start using Dijkstra."""
    # 各ノードまでの最短距離と、経路復元用の直前ノードを初期化
    distance: Dict[Zone, Optional[int]] = {node: None for node in graph}
    prev_zone: Dict[Zone, Optional[Zone]] = {node: None for node in graph}
    unvisited: Set[Zone] = set(graph.keys())

    distance[start] = 0
    # 未確定ノードがある限り、最短距離が最も小さいノードを順に確定していく
    while unvisited:
        current_distance: Optional[int] = None
        current_node: Optional[Zone] = None
        # 未確定ノードの中から、最も距離が短いノードを探す
        # 同距離なら priority zone を優先する
        for node in unvisited:
            if distance[node] is None:
                continue
            if (current_distance is None or distance[node] < current_distance
                or (distance[node] == current_distance and current_node is not None
                    and node.zone == ZoneType.PRIORITY
                    and current_node.zone != ZoneType.PRIORITY)
                    ):
                current_node = node
                current_distance = distance[node]

        if current_node == end:
            break
        assert current_node is not None
        assert current_distance is not None
        unvisited.remove(current_node)
        # 隣接ノードに対して、今のノード経由の方が短いかを確認して更新する
        for neighbor, _ in graph[current_node]:
            if neighbor not in unvisited:
                continue
            new_distance: int = current_distance + get_cost(neighbor)
            # to find the shortest paths
            if distance[neighbor] is None or new_distance < distance[neighbor]:
                distance[neighbor] = new_distance
                prev_zone[neighbor] = current_node
    # restore path
    path: List[Zone] = []
    cur: Optional[Zone] = end
    while cur is not None:
        path.append(cur)
        cur = prev_zone[cur]
    path.reverse()
    return path
