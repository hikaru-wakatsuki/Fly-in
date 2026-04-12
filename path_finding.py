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
    previous: Dict[Zone, Optional[Zone]] = {node: None for node in graph}
    unvisited: Set[Zone] = set(graph)

    distance[start] = 0
    penalties = penalties or {}
    # 未確定ノードがある限り、最短距離が最も小さいノードを順に確定していく
    while unvisited:
        # 既に距離算出したNodeが対象
        candidates = [node for node in unvisited if distance[node] is not None]
        if not candidates:
            break
        # 最短経路のノード検出（経路数が同じならばZoneType.PRIORITYを優先）
        current: Zone = min(candidates, key=lambda node:
                      (distance[node], 0 if node.zone == ZoneType.PRIORITY else 1))

        if current == end:
            break

        unvisited.remove(current)
        current_distance: int = distance[current]
        # 最短経路のノードの隣のZoneを比較
        for neighbor, _ in graph[current]:
            if neighbor not in unvisited:
                continue
            # penaltyを重みづけした距離を算出
            new_distance: int = (current_distance + get_cost(neighbor)
                                 + penalties.get((current, neighbor), 0))
            # 比較して最短経路を発見する
            if distance[neighbor] is None or new_distance < distance[neighbor]:
                distance[neighbor] = new_distance
                previous[neighbor] = current

    # restore path
    path: List[Zone] = []
    cur: Optional[Zone] = end
    while cur is not None:
        path.append(cur)
        cur = previous[cur]
    path.reverse()
    return path
