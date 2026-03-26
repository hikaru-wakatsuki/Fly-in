from pydantic import BaseModel, Field, model_validator, ValidationError
from enum import Enum
from typing import Tuple, Optional, List
import sys


class ZoneType(Enum):
    NORMAL = 'normal'
    BLOCKED = 'blocked'
    RESTRICTED = 'restricted'
    PRIORITY = 'priority'


class Color(Enum):
    RED = 'red'
    BLUE = 'blue'
    GREEN = 'green'
    YELLOW = 'yellow'
    GRAY = 'gray'


class Hub(BaseModel):
    coordinate: Tuple[int, int] = Field(...)
    zone: ZoneType = Field('normal')
    color: Optional[Color] = Field(None)
    max_drones: int = Field(1, gt=0)

    @model_validator(mode='after')
    def hub_check(self) -> "Hub":
        x, y = self.coordinate
        if x < 0 or y < 0:
            raise ValueError("coordinates must be non-negative")
        return self


class Connection(BaseModel):
    hubs: List[Hub] = Field(..., max_length=2)
    max_link_capacity: int = Field(..., gt=0)


class DronesNetwork(BaseModel):
    nb_drones: int = Field(..., gt=0)
    start_hub: Hub = Field(...)
    end_hub: Hub = Field(...)
    hubs: List[Hub] = Field(...)
    connections: List[Connection] = Field(...)


def parse_input_file(file_name: str) -> DronesNetwork:
    try:
        with open(file_name) as f:
            text: str = f.read()

    except (FileNotFoundError, PermissionError) as error:
        print(error)


def main() -> None:
    if len(sys.argv) == 1:
        return
    if len(sys.argv) == 2:
        try:
            drones_network = parse_input_file(sys.argv[1])
            print(drones_network)
        except (ValidationError) as error:
            print(error)
    if len(sys.argv) > 2:
        return
