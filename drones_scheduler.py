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
        self.remaining_turns: int = 0
        self.finished: bool = False


class SimulationState:
    def __init__(self, graph: Dict[Zone, List[Tuple[Zone, int]]]) -> None:
        self.graph: Dict[Zone, List[Tuple[Zone, int]]] = graph
        #現在の占有
        self.zone_occupancy: Dict[Zone, int] = {}
        self.link_usage: Dict[Tuple[Zone, Zone], int] = {}

    def reset_usage(self, drones: List[DroneState]) -> None:
        for drone in drones:
            if drone.finished:
                continue
            if drone.in_transit:
                link: Tuple[Zone, Zone] = (drone.current_zone, drone.transit_to)
                self.link_usage[link] = self.link_usage.get(link, 0) + 1
            else:
                zone: Zone = drone.current_zone
                self.zone_occupancy[zone] = self.zone_occupancy.get(zone, 0) + 1


def initialize_drones(nb_drones: int, start: Zone, path: List[Zone]) -> List[DroneState]:
    drones: List[DroneState] = []
    for i in range(1, nb_drones + 1):
        drones.append(DroneState(i, start, path))
    return drones


def can_move(state: SimulationState, from_zone: Zone, to_zone: Zone) -> bool:
    if state.zone_occupancy.get(to_zone, 0) >= to_zone.max_drones:
        return False
    max_link_capacity: int = (
        capacity for zone, capacity in state.graph[from_zone] if zone==to_zone)
    if state.link_usage.get((from_zone, to_zone), 0) >= max_link_capacity:
        return False
    return True


def next_transit(state: SimulationState, drone: DroneState, end: Zone) -> None:
    if drone.in_transit:
        drone.in_transit = False
    drone.current_zone = drone.transit_to
    drone.transit_to = None
    if drone.current_zone == end:
        drone.finished = True





def run_turn(state: SimulationState, drones: List[DroneState], end: Zone) -> List[str]:
    movements: List[str] = []

    for drone in drones:
        if drone.finished:
            continue
        if drone.in_transit:
            drone.remaining_turns -= 1
            if drone.remaining_turns == 0:
                next_transit(state, drone, end)
                if not drone.finished:
                    movements.append(f"D{drone.drone_id}-{drone.current_zone.name}")
        else:
            next_zone: Zone = drone.path[drone.path_index + 1]
            if not can_move(state, drone.current_zone, next_zone):
                continue
            if next_zone.zone == ZoneType.RESTRICTED:
                drone.in_transit = True
                drone.transit_to = next_zone
                drone.remaining_turns = 1
                movements.append(f"D{drone.drone_id}-{drone.current_zone.name}-{next_zone.name}")
            else:
                drone.current_zone = next_zone
                drone.path_index += 1
                if next_zone == state.end_hub:
                    drone.finished = True
                    movements.append(f"D{drone.drone_id}-{next_zone.name}")
    state.reset_usage(drones)
    return movements
