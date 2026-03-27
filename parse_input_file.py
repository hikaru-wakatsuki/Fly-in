from pydantic import BaseModel, Field, model_validator, ValidationError
from enum import Enum
from typing import Tuple, Optional, List, Set
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
    return parse_lines(lines)


def parse_lines(lines: List[str]) -> DronesNetwork:

    def create_zone(config: str) -> Zone:
        parts = config.split(' ', 3)
        if len(parts) not in (3, 4):
            raise ValueError(f"Invalid zone format: {config}")
        name: str = parts[0]
        try:
            x, y = int(parts[1]), int(parts[2])
        except ValueError:
            raise ValueError(f"Invalid coordinates in zone {name}: {parts[1]}, {parts[2]}")
        if len(parts) == 3:
            return Zone(name=name, coordinate=(x, y))
        metadata: str = parts[3]
        if not (metadata.startswith('[') and metadata.endswith(']')):
            raise ValueError(f"Invalid metadata format in zone {name}: {metadata}")
        tags: List[str] = metadata[1:-1].split()
        seen_keys: Set[str] = set()
        zone: ZoneType = ZoneType.NORMAL
        color: Optional[Color] = None
        max_drones: int = 1
        for tag in tags:
            if '=' not in tag:
                raise ValueError(f"Invalid metadata entry in zone {name}: {tag}")
            key, value = tag.split('=', 1)
            if key in seen_keys:
                raise ValueError(f"Duplicate metadata in zone {name}: {key}")
            seen_keys.add(key)
            if key == 'zone':
                try:
                    zone = ZoneType(value)
                except ValueError:
                    raise ValueError(f"Invalid zone value in zone {name}: {value}")
            elif key == 'color':
                try:
                    color = Color(value)
                except ValueError:
                    raise ValueError(f"Invalid color value in zone {name}: {value}")
            elif key == 'max_drones':
                try:
                    max_drones = int(value)
                except ValueError:
                    raise ValueError(f"Invalid max_drones in zone {name}: {value}")
            else:
                raise ValueError(f"Unknown metadata key in zone {name}: {key}")
        return Zone(name=name, coordinate=(x, y), zone=zone, color=color, max_drones=max_drones)


    if not lines[0].strip().startswith('nb_drones:'):
        raise ValueError()
    for line in lines:
        line = line.strip()
        if line.startswith('#') or not line:
            continue
        parts = line.split(':', 1)
        if len(parts) != 2:
            raise ValueError()
        label, config = parts
        config = config.strip()
        if label == 'nb_drones':
            nb_drones: int = int(config)
        elif label == 'start_hub':
            start_hub: Zone = create_zone(config)




def main() -> None:
    if len(sys.argv) == 1:
        return
    if len(sys.argv) == 2:
        try:
            drones_network = parse_input_file(sys.argv[1])
            print(drones_network)
        except (ValidationError, TypeError, ValueError) as error:
            print(error)
    if len(sys.argv) > 2:
        return
