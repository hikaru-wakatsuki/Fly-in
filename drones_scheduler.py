from parse_input_file import Zone, ZoneType
from typing import Tuple, Optional, List, Dict
from path_finding import find_shortest_path


class DroneState:
    """単一ドローンの状態を管理するクラス

    Attributes:
        drone_count (int): ドローン識別番号
        current_zone (Zone): 現在位置
        path (List[Zone]): 割り当てられた経路
        path_index (int): 現在の経路インデックス
        in_transit (bool): リンク移動中かどうか
        transit_to (Optional[Zone]): 移動先ゾーン（移動中のみ）
        finished (bool): ゴール到達済みかどうか
    """
    def __init__(self, drone_count: int, start: Zone,
                 path: List[Zone]) -> None:
        self.drone_count: int = drone_count
        self.current_zone: Zone = start
        self.path: List[Zone] = path
        self.path_index: int = 0
        self.in_transit: bool = False
        self.transit_to: Optional[Zone] = None
        self.finished: bool = False


class SimulationState:
    """シミュレーション全体の状態（占有・リンク使用）を管理するクラス

    Attributes:
        graph (Dict[Zone, List[Tuple[Zone, int]]]): グラフ（隣接リスト）
        zone_occupancy (Dict[Zone, int]): 各ゾーンの現在占有数
        link_usage (Dict[Tuple[Zone, Zone], int]): 各リンクの使用数
        next_zone_reservation (Dict[Zone, int]): 次ターンでのゾーン予約数（同時突入防止）
    """
    def __init__(self, graph: Dict[Zone, List[Tuple[Zone, int]]]) -> None:
        self.graph: Dict[Zone, List[Tuple[Zone, int]]] = graph
        # 現在の占有
        self.zone_occupancy: Dict[Zone, int] = {}
        self.link_usage: Dict[Tuple[Zone, Zone], int] = {}
        self.next_zone_reservation: Dict[Zone, int] = {}

    def initialize_state(self, drones: List[DroneState]) -> None:
        """初期状態としてゾーン占有数を設定"""
        for drone in drones:
            zone: Zone = drone.current_zone
            self.zone_occupancy[zone] = self.zone_occupancy.get(zone, 0) + 1

    def leave_zone(self, zone: Zone) -> None:
        """ゾーンからドローンが離脱した際の占有数を更新"""
        self.zone_occupancy[zone] -= 1

    def enter_zone(self, zone: Zone) -> None:
        """ゾーンにドローンが入った際の占有数を更新"""
        self.zone_occupancy[zone] = self.zone_occupancy.get(zone, 0) + 1

    def leave_link(self, from_zone: Zone, to_zone: Zone) -> None:
        """リンク移動完了時の状態更新

        リンク使用数を減少させ、予約を解除し、到達ゾーンへドローンを配置
        """
        link: Tuple[Zone, Zone] = tuple(
            sorted((from_zone, to_zone), key=lambda zone: zone.name))
        self.link_usage[link] = self.link_usage.get(link) - 1
        self.next_zone_reservation[to_zone] -= 1
        self.enter_zone(to_zone)

    def enter_link(self, from_zone: Zone, to_zone: Zone) -> None:
        """リンクへの進入時の状態更新

        出発ゾーンの占有数を減らし、リンク使用数と到達ゾーンの予約数を更新
        """
        self.leave_zone(from_zone)
        link: Tuple[Zone, Zone] = tuple(
            sorted((from_zone, to_zone), key=lambda zone: zone.name))
        self.link_usage[link] = self.link_usage.get(link, 0) + 1
        next_zone_count: int = self.next_zone_reservation.get(to_zone, 0) + 1
        self.next_zone_reservation[to_zone] = next_zone_count


def can_move(state: SimulationState, from_zone: Zone, to_zone: Zone,
             end: Zone) -> bool:
    """ドローンが次のゾーンへ移動可能かを判定

    判定条件:
        - 到達ゾーンの収容上限(max_drones)を超えない
        - リンク容量(max_link_capacity)を超えない
    """
    if to_zone != end:
        current_occupancy: int = state.zone_occupancy.get(to_zone, 0)
        reserved: int = state.next_zone_reservation.get(to_zone, 0)
        if current_occupancy + reserved >= to_zone.max_drones:
            return False
    for zone, capacity in state.graph[from_zone]:
        if zone == to_zone:
            max_link_capacity: int = capacity
            break
    link: Tuple[Zone, Zone] = tuple(
        sorted((from_zone, to_zone), key=lambda zone: zone.name))
    return state.link_usage.get(link, 0) < max_link_capacity


def run_turn(state: SimulationState, drones: List[DroneState],
             end: Zone) -> List[str]:
    """1ターン分のシミュレーションを実行する。

    処理は以下の順序で行う:
        1. 移動中ドローンの到着処理
        2. 次の移動の判定と実行(RESTRICTEDゾーンはリンク移動(2ステップ))
    """
    movements: List[str] = []
    for drone in drones:
        if drone.finished:
            continue
        if drone.in_transit:
            state.leave_link(drone.current_zone, drone.transit_to)
            drone.current_zone = drone.transit_to
            drone.in_transit = False
            drone.transit_to = None
            drone.path_index += 1
            if drone.current_zone == end:
                drone.finished = True
            movements.append(f"D{drone.drone_count}-{drone.current_zone.name}")
            continue
        next_zone: Zone = drone.path[drone.path_index + 1]
        if not can_move(state, drone.current_zone, next_zone, end):
            new_path: List[Zone] = recompute_path(
                state, drone.current_zone, end)
            drone.path = new_path
            drone.path_index = 0
            next_zone = drone.path[1]

            if not can_move(state, drone.current_zone, next_zone, end):
                continue
        if next_zone.zone == ZoneType.RESTRICTED:
            state.enter_link(drone.current_zone, next_zone)
            drone.in_transit = True
            drone.transit_to = next_zone
            movements.append(
                f"D{drone.drone_count}-{drone.current_zone.name}"
                f"-{next_zone.name}")
        else:
            state.leave_zone(drone.current_zone)
            state.enter_zone(next_zone)
            drone.current_zone = next_zone
            drone.path_index += 1
            if next_zone == end:
                drone.finished = True
            movements.append(f"D{drone.drone_count}-{next_zone.name}")
    return movements


def run_simulation(drone_count: int, start: Zone, end: Zone,
                   graph: Dict[Zone, List[Tuple[Zone, int]]]) -> List[str]:
    """ドローン配送シミュレーションを実行
    全ドローンがゴールに到達するまでターンを繰り返す

    Returns:
        List[List[str]]: ターンごとの移動ログ
    """
    drones: List[DroneState] = []
    path = find_shortest_path(graph, start, end)
    for i in range(1, drone_count + 1):
        drones.append(DroneState(i, start, path))
    state: SimulationState = SimulationState(graph)
    state.initialize_state(drones)
    logs: List[List[str]] = []
    while not all(drone.finished for drone in drones):
        logs.append(run_turn(state, drones, end))
    return logs


def recompute_path(state: SimulationState, current_zone: Zone,
                   end: Zone,) -> List[Zone]:
    """混雑状況（リンク使用量・ゾーン占有）に基づくペナルティを考慮
    current_zone から end までの最短経路を再計算
    """
    penalties: Dict[Tuple[Zone, Zone], int] = {}
    # linkが使用されている場合penalty付与
    for (zone1, zone2), usage in state.link_usage.items():
        if usage > 0:
            penalties[(zone1, zone2)] = usage * 4
            penalties[(zone2, zone1)] = usage * 4
    # 専有中のZoneにpenalty付与
    for zone, occupancy in state.zone_occupancy.items():
        if zone != current_zone and zone != end and occupancy > 0:
            penalties[(current_zone, zone)] = occupancy * 2

    return find_shortest_path(state.graph, current_zone, end, penalties)
