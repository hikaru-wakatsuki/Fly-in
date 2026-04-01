from parse_input_file import Zone, ZoneType
from typing import Tuple, Optional, List, Dict, Set


drone_positions: Dict[int, Zone]
finished_drones: Set[int]


class DroneState:
    def __init__(self, drone_id: int, start: Zone, path: List[Zone]) -> None:
        self.drone_id: int = drone_id
        self.current_zone: Zone = start
        self.path: List[Zone] = path
        self.path_index: int = 0
        self.in_transit: bool = False
        self.transit_to: Optional[Zone] = None
        self.finished: bool = False


class SimulationState:
    def __init__(self, graph: Dict[Zone, List[Tuple[Zone, int]]]) -> None:
        self.graph: Dict[Zone, List[Tuple[Zone, int]]] = graph
        #現在の占有
        self.zone_occupancy: Dict[Zone, int] = {}
        self.link_usage: Dict[Tuple[Zone, Zone], int] = {}

    def initialize_state(self, drones: List[DroneState]) -> None:
        for drone in drones:
            zone: Zone = drone.current_zone
            self.zone_occupancy[zone] = self.zone_occupancy.get(zone, 0) + 1

    def leave_zone(self, zone: Zone) -> None:
        self.zone_occupancy[zone] = self.zone_occupancy.get(zone) - 1

    def enter_zone(self, zone: Zone) -> None:
        self.zone_occupancy[zone] = self.zone_occupancy.get(zone, 0) + 1

    def leave_link(self, from_zone: Zone, to_zone: Zone) -> None:
        link: Tuple[Zone, Zone] = (from_zone, to_zone)
        self.link_usage[link] = self.link_usage.get(link, 0) - 1
        self.enter_zone(to_zone)

    def enter_link(self, from_zone: Zone, to_zone: Zone) -> None:
        self.leave_zone(from_zone)
        link: Tuple[Zone, Zone] = (from_zone, to_zone)
        self.link_usage[link] = self.link_usage.get(link, 0) + 1


def initialize_drones(nb_drones: int, start: Zone, path: List[Zone]) -> List[DroneState]:
    drones: List[DroneState] = []
    for i in range(1, nb_drones + 1):
        drones.append(DroneState(i, start, path))
    return drones


def can_move(state: SimulationState, from_zone: Zone, to_zone: Zone) -> bool:
    if state.zone_occupancy.get(to_zone, 0) >= to_zone.max_drones:
        return False
    max_link_capacity = None
    for zone, capacity in state.graph[from_zone]:
        if zone == to_zone:
            max_link_capacity = capacity
            break
    return state.link_usage.get((from_zone, to_zone), 0) < max_link_capacity


def run_turn(state: SimulationState, drones: List[DroneState], end: Zone) -> List[str]:
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
            movements.append(f"D{drone.drone_id}-{drone.current_zone.name}")
        else:
            next_zone: Zone = drone.path[drone.path_index + 1]
            if not can_move(state, drone.current_zone, next_zone):
                continue
            if next_zone.zone == ZoneType.RESTRICTED:
                state.enter_link(drone.current_zone, next_zone)
                drone.in_transit = True
                drone.transit_to = next_zone
                movements.append(f"D{drone.drone_id}-{drone.current_zone.name}-{next_zone.name}")
            else:
                state.leave_zone(drone.current_zone)
                state.enter_zone(next_zone)
                drone.current_zone = next_zone
                drone.path_index += 1
                if next_zone == end:
                    drone.finished = True
                movements.append(f"D{drone.drone_id}-{next_zone.name}")
    return movements
