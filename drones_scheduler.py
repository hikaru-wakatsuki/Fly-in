from parse_input_file import Zone, ZoneType
from typing import Tuple, Optional, List, Dict


class DroneState:
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
    def __init__(self, graph: Dict[Zone, List[Tuple[Zone, int]]]) -> None:
        self.graph: Dict[Zone, List[Tuple[Zone, int]]] = graph
        # 現在の占有
        self.zone_occupancy: Dict[Zone, int] = {}
        self.link_usage: Dict[Tuple[Zone, Zone], int] = {}
        self.next_zone_reservation: Dict[Zone, int] = {}

    def initialize_state(self, drones: List[DroneState]) -> None:
        for drone in drones:
            zone: Zone = drone.current_zone
            self.zone_occupancy[zone] = self.zone_occupancy.get(zone, 0) + 1

    def leave_zone(self, zone: Zone) -> None:
        self.zone_occupancy[zone] -= 1

    def enter_zone(self, zone: Zone) -> None:
        self.zone_occupancy[zone] = self.zone_occupancy.get(zone, 0) + 1

    def leave_link(self, from_zone: Zone, to_zone: Zone) -> None:
        link: Tuple[Zone, Zone] = (from_zone, to_zone)
        self.link_usage[link] = self.link_usage.get(link) - 1
        self.next_zone_reservation[to_zone] -= 1
        self.enter_zone(to_zone)

    def enter_link(self, from_zone: Zone, to_zone: Zone) -> None:
        self.leave_zone(from_zone)
        link: Tuple[Zone, Zone] = (from_zone, to_zone)
        self.link_usage[link] = self.link_usage.get(link, 0) + 1
        next_zone_count: int = self.next_zone_reservation.get(to_zone, 0) + 1
        self.next_zone_reservation[to_zone] = next_zone_count


def can_move(state: SimulationState, from_zone: Zone, to_zone: Zone,
             end: Zone) -> bool:
    if to_zone != end:
        current_occupancy: int = state.zone_occupancy.get(to_zone, 0)
        reserved: int = state.next_zone_reservation.get(to_zone, 0)
        if current_occupancy + reserved >= to_zone.max_drones:
            return False
    for zone, capacity in state.graph[from_zone]:
        if zone == to_zone:
            max_link_capacity: int = capacity
            break
    return state.link_usage.get((from_zone, to_zone), 0) < max_link_capacity


def run_turn(state: SimulationState, drones: List[DroneState],
             end: Zone) -> List[str]:
    movements: List[str] = []
    for drone in drones:
        if drone.finished:
            continue
        if drone.in_transit:
            state.leave_link(drone.current_zone, drone.transit_to)
            drone.in_transit = False
            drone.current_zone = drone.transit_to
            drone.transit_to = None
            drone.path_index += 1
            if drone.current_zone == end:
                drone.finished = True
            movements.append(f"D{drone.drone_count}-{drone.current_zone.name}")
        else:
            next_zone: Zone = drone.path[drone.path_index + 1]
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


def assign_paths(drone_count: int, start: Zone,
                 paths: List[List[Zone]]) -> List[DroneState]:
    drones: List[DroneState] = []
    path_costs: List[tuple[List[Zone], int]] = []
    for path in paths:
        cost: int = 0
        for zone in path[1:]:
            if zone.zone == ZoneType.RESTRICTED:
                cost += 2
            else:
                cost += 1
        path_costs.append((path, cost))
    # cost が小さいほど多く割り当てたいので、逆数で重みを作る
    weights: List[float] = [1 / cost for _, cost in path_costs]
    total_weight: float = sum(weights)
    # ドローンの数　* pathに通す割合
    assigned_counts: List[int] = [
        int(drone_count * weight / total_weight)
        for weight in weights
    ]
    while sum(assigned_counts) < drone_count:
        best_index: int = weights.index(max(weights))
        assigned_counts[best_index] += 1

    drones: List[DroneState] = []
    drone_id: int = 1
    for (path, _), count in zip(path_costs, assigned_counts):
        for i in range(count):
            drones.append(DroneState(drone_id, start, path))
            drone_id += 1
    return drones


def run_simulation(drone_count: int, start: Zone, end: Zone,
                   graph: Dict[Zone, List[Tuple[Zone, int]]],
                   paths: List[List[Zone]]) -> None:
    drones: List[DroneState] = assign_paths(drone_count, start, paths)
    state: SimulationState = SimulationState(graph)
    state.initialize_state(drones)
    while not all(drone.finished for drone in drones):
        movements: List[str] = run_turn(state, drones, end)
        if not movements:
            print("No more possible moves (deadlock)")
            break

        print(" ".join(movements))
