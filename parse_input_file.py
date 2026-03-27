from pydantic import BaseModel, Field, model_validator, ValidationError
from enum import Enum
from typing import Tuple, Optional, List, Any
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


class Zone(BaseModel):
    name: str = Field(...)
    coordinate: Tuple[int, int] = Field(...)
    zone: ZoneType = Field('normal')
    color: Optional[Color] = Field(None)
    max_drones: int = Field(1, gt=0)

    @model_validator(mode='after')
    def hub_check(self) -> "Zone":
        if ' ' in self.name or '-' in self.name:
            raise ValueError("Zone names can not use dashes and spaces.")
        x, y = self.coordinate
        if x < 0 or y < 0:
            raise ValueError("coordinates must be non-negative")
        return self


class Connection(BaseModel):
    hubs: List[Zone] = Field(..., min_length=2, max_length=2)
    max_link_capacity: int = Field(..., gt=0)

    @model_validator(mode='after')
    def connection_check(self) -> "Connection":
        if self.hubs[0] == self.hubs[1]:
            raise ValueError("connection must have difference hubs")


class DronesNetwork(BaseModel):
    nb_drones: int = Field(..., gt=0)
    start_hub: Zone = Field(...)
    end_hub: Zone = Field(...)
    hubs: List[Zone] = Field(...)
    connections: List[Connection] = Field(...)


def parse_input_file(file_name: str) -> DronesNetwork:
    try:
        with open(file_name) as f:
            text: str = f.read()
    except (FileNotFoundError, PermissionError) as error:
        print(error)
    lines: List[str] = text.splitlines()
    if not lines[0].startswith('nb_drones:'):
        raise ValueError()


def parse_lines(lines: List[str]) -> dict[str, Any]:
    if not lines[0].startswith('nb_drones:'):
        raise ValueError()
    for line in lines:
        if key.startswith('#') or line.strip():
            continue
        key, value = line.split(':', 1)
        value = value.strip()
        if key == 'nb_drones':
            nb_drones = value
        elif key == 'start_hub'



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
