from parse_input_file import Zone, ZoneType
from typing import Tuple, Optional, List, Dict, Set


def get_cost(zone: Zone) -> int:
    """ゾーンに応じた移動コストを計算する。

    コストは以下のルールで加算される:
        - 基本コスト: 1
        - RESTRICTEDゾーン: +5
        - max_drones <= 1: +5 (混雑・ボトルネック)
        - max_drones == 2: +2
    """
    cost: int = 1
    if zone.zone == ZoneType.RESTRICTED:
        cost += 1
    if zone.max_drones <= 1:
        cost += 5
    elif zone.max_drones == 2:
        cost += 2
    return cost


def find_shortest_path(graph: Dict[Zone, List[Tuple[Zone, int]]],
                       start: Zone, end: Zone,
                       penalties: Optional[Dict[Tuple[Zone, Zone], int]] = None
                       ) -> List[Zone]:
    """ペナルティ付きダイクストラ法で最短経路を決定

    通常のダイクストラ法に加えて以下の拡張を行う:
        - ゾーンごとのコスト(get_cost)を加算
        - エッジごとのペナルティを加算
        - 同距離の場合は PRIORITYゾーンを優先
    """
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
                or (distance[node] == current_distance
                    and current_node is not None
                    and node.zone == ZoneType.PRIORITY
                    and current_node.zone != ZoneType.PRIORITY)):
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
            if penalties:
                penalty: int = penalties.get((current_node, neighbor), 0)
            else:
                penalty = 0
            new_distance: int = current_distance + get_cost(neighbor) + penalty
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
