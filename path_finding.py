from parse_input_file import Zone, ZoneType
from typing import Tuple, Optional, List, Dict, Set


def get_cost(zone: Zone) -> int:
    """ゾーンに応じた移動コストを計算する。

    コストは以下のルールで加算される:
        - 基本コスト: 1
        - RESTRICTEDゾーン: +5
        - max_drones <= 1: +5（混雑・ボトルネック）
        - max_drones == 2: +2
    """
    cost: int = 1
    if zone.zone == ZoneType.RESTRICTED:
        cost += 5
    if zone.max_drones <= 1:
        cost += 5
    elif zone.max_drones == 2:
        cost += 2
    return cost


def find_shortest_path(graph: Dict[Zone, List[Tuple[Zone, int]]],
                  start: Zone, end: Zone,
                  penalties: Dict[Tuple[Zone, Zone], int]) -> List[Zone]:
    """ペナルティ付きダイクストラ法で最短経路を決定

    通常のダイクストラ法に加えて以下の拡張を行う:
        - ゾーンごとのコスト（get_cost）を加算
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
            penalty: int = penalties.get((current_node, neighbor), 0)
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


def add_penalty(
        path: List[Zone], penalties: Dict[Tuple[Zone, Zone], int],
        value: int = 2) -> None:
    """経路上のエッジにペナルティを追加

    同じ経路が繰り返し選ばれないようにするため、
    経路に含まれる全エッジのコストを増加

    RESTRICTEDゾーンを含むエッジはペナルティを倍増
    """
    for i in range(len(path) - 1):
        zone1: Zone = path[i]
        zone2: Zone = path[i + 1]
        penalty: int = value
        if ZoneType.RESTRICTED in (zone1.zone, zone2.zone):
            penalty *= 2
        penalties[(zone1, zone2)] = penalties.get((zone1, zone2), 0) + penalty
        penalties[(zone2, zone1)] = penalties.get((zone2, zone1), 0) + penalty


def find_multiple_paths(
        graph: Dict[Zone, List[Tuple[Zone, int]]],
        start: Zone, end: Zone, count: int) -> List[List[Zone]]:
    """複数の異なる経路候補を探索

    ダイクストラ法を複数回実行し、毎回ペナルティを追加することで
    異なる経路を生成

    同一経路が生成された場合は重複を除外
    """
    penalties: Dict[Tuple[Zone, Zone], int] = {}
    paths: List[List[Zone]] = []
    for _ in range(count):
        path = find_shortest_path(graph, start, end, penalties)
        add_penalty(path, penalties, 2)
        if path in paths:
            continue
        paths.append(path)
    return paths


def determine_path_count(nb_drones: int) -> int:
    """ドローン数に応じて生成する経路数を決定

    Rules:
        - <= 2: 1経路
        - <= 4: 2経路
        - <= 8: 3経路
        - <= 16: 4経路
        - > 16: 5経路
    """
    if nb_drones <= 2:
        return 1
    elif nb_drones <= 4:
        return 2
    elif nb_drones <= 8:
        return 3
    elif nb_drones <= 16:
        return 4
    else:
        return 5
