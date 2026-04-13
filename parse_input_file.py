from pydantic import BaseModel, Field, model_validator, ConfigDict
from enum import Enum
from typing import Tuple, Optional, List, Set


class ZoneType(Enum):
    """ゾーンの種類を表す列挙型。"""
    NORMAL = 'normal'
    BLOCKED = 'blocked'
    RESTRICTED = 'restricted'
    PRIORITY = 'priority'


class Zone(BaseModel):
    """
    ドローンネットワーク内のゾーン（ハブ）を表すクラス

    Attributes:
        name (str): ゾーン名（スペースやハイフンは禁止）
        coordinate (Tuple[int, int]): ゾーンの座標 (x, y)
        zone (ZoneType): ゾーンの種類
        color (Optional[str]): 任意の色情報
        max_drones (int): 同時に存在できる最大ドローン数
    """
    model_config = ConfigDict(frozen=True)
    name: str = Field(...)
    coordinate: Tuple[int, int] = Field(...)
    zone: ZoneType = Field(ZoneType.NORMAL)
    color: Optional[str] = Field(None)
    max_drones: int = Field(1, gt=0)

    @model_validator(mode='after')
    def hub_check(self) -> "Zone":
        """ゾーン名のバリデーションを実施"""
        if ' ' in self.name or '-' in self.name:
            raise ValueError("Zone names can not use dashes and spaces.")
        return self


class Connection(BaseModel):
    """
    ゾーン間の接続（リンク）を表すクラス。

    Attributes:
        hubs (Tuple[str, str]): 接続する2つのハブ名。
        max_link_capacity (int): 接続の最大容量。
    """
    hubs: Tuple[str, str] = Field(...)
    max_link_capacity: int = Field(1, gt=0)

    @model_validator(mode='after')
    def connection_check(self) -> "Connection":
        """接続のバリデーションを実施"""
        if self.hubs[0] == self.hubs[1]:
            raise ValueError("connection must link two different hubs")
        return self


class DronesNetwork(BaseModel):
    """
    ドローン配送ネットワーク全体を表すモデル。

    Attributes:
        nb_drones (int): ドローンの総数（1以上）。
        start_hub (Zone): 出発地点となるハブ。
        end_hub (Zone): 到着地点となるハブ。
        hubs (List[Zone]): 中間ハブの一覧。
        connections (List[Connection]): ハブ間の接続情報。
    """
    nb_drones: int = Field(..., gt=0)
    start_hub: Zone = Field(...)
    end_hub: Zone = Field(...)
    hubs: List[Zone] = Field(default_factory=list)
    connections: List[Connection] = Field(default_factory=list)

    @model_validator(mode='after')
    def drones_network_check(self) -> "DronesNetwork":
        """ネットワーク全体の整合性を検証
        検証内容:
            - ゾーン名の一意性
            - 座標の一意性
            - 接続の整合性（存在確認・重複禁止）
            - start/end の制約チェック
        """

        all_zones: List[Zone] = [self.start_hub, self.end_hub] + self.hubs
        zone_names: Set[str] = set()
        zone_coordinates: Set[Tuple[int, int]] = set()

        for zone in all_zones:
            if zone.name in zone_names:
                raise ValueError(f"Duplicate zone name: {zone.name}")
            zone_names.add(zone.name)

        for zone in all_zones:
            if zone.coordinate in zone_coordinates:
                raise ValueError(
                    f"Duplicate zone coordinate: {zone.coordinate}")
            zone_coordinates.add(zone.coordinate)

        seen_connections: Set[Tuple[str, str]] = set()
        for connection in self.connections:
            hub1, hub2 = connection.hubs
            if hub1 not in zone_names:
                raise ValueError(f"Connection references unknown hub: {hub1}")
            if hub2 not in zone_names:
                raise ValueError(f"Connection references unknown hub: {hub2}")
            first_hub, second_hub = sorted((hub1, hub2))
            connection_key: Tuple[str, str] = (first_hub, second_hub)
            if connection_key in seen_connections:
                raise ValueError(f"Duplicate connection: {hub1}-{hub2}")
            seen_connections.add(connection_key)

        if self.start_hub.max_drones < self.nb_drones:
            raise ValueError("start_hub max_drones must be >= nb_drones")
        if self.end_hub.max_drones < self.nb_drones:
            raise ValueError("end_hub max_drones must be >= nb_drones")
        if self.start_hub.zone == ZoneType.BLOCKED:
            raise ValueError("start_hub cannot be blocked")
        if self.end_hub.zone == ZoneType.BLOCKED:
            raise ValueError("end_hub cannot be blocked")
        return self


def parse_input_file(file_name: str) -> DronesNetwork:
    """入力ファイルを読み込み、ドローンネットワークを構築"""
    try:
        with open(file_name) as f:
            text: str = f.read()
    except (FileNotFoundError, PermissionError) as error:
        raise ValueError(f"File error: {error}")
    lines: List[str] = text.splitlines()
    return parse_lines(lines)


def parse_lines(lines: List[str]) -> DronesNetwork:
    """テキスト行からドローンネットワークを構築する。

    入力フォーマット:
        nb_drones: <int>
        start_hub: <zone定義>
        end_hub: <zone定義>
        hub: <zone定義>
        connection: <hub1-hub2> [max_link_capacity=...]

    コメント行 (#) と空行は無視される。
    """

    def create_zone(config: str) -> Zone:
        """1行の文字列からZoneオブジェクトの生成

        フォーマット:
            name x y [key=value ...]
        """
        parts = config.split(maxsplit=3)
        if len(parts) not in (3, 4):
            raise ValueError(f"Invalid zone format: {config}")
        name: str = parts[0]
        try:
            x, y = int(parts[1]), int(parts[2])
        except ValueError:
            raise ValueError(
                f"Invalid coordinates in zone {name}: {parts[1]}, {parts[2]}")
        if len(parts) == 3:
            return Zone(name=name, coordinate=(x, y))
        metadata: str = parts[3].strip()
        if not (metadata.startswith('[') and metadata.endswith(']')):
            raise ValueError(
                f"Invalid metadata format in zone {name}: {metadata}")
        tags: List[str] = metadata[1:-1].split()
        seen_keys: Set[str] = set()
        zone: ZoneType = ZoneType.NORMAL
        color: Optional[str] = None
        max_drones: int = 1
        for tag in tags:
            if '=' not in tag:
                raise ValueError(
                    f"Invalid metadata entry in zone {name}: {tag}")
            key, value = tag.split('=', 1)
            if key in seen_keys:
                raise ValueError(
                    f"Duplicate metadata in zone {name}: {key}")
            seen_keys.add(key)
            if key == 'zone':
                try:
                    zone = ZoneType(value)
                except ValueError:
                    raise ValueError(
                        f"Invalid zone value in zone {name}: {value}")
            elif key == 'color':
                color = value
            elif key == 'max_drones':
                try:
                    max_drones = int(value)
                except ValueError:
                    raise ValueError(
                        f"Invalid max_drones in zone {name}: {value}")
            else:
                raise ValueError(
                    f"Unknown metadata key in zone {name}: {key}")
        return Zone(name=name, coordinate=(x, y),
                    zone=zone, color=color, max_drones=max_drones)

    def create_connection(config: str) -> Connection:
        """1行の文字列からConnectionオブジェクトの生成
        フォーマット:
            hub1-hub2 [max_link_capacity=...]
        """
        parts = config.split(maxsplit=1)
        if '-' not in parts[0]:
            raise ValueError(f"Invalid connection format: {config}")
        hub1, hub2 = parts[0].split('-', 1)
        if not hub1 or not hub2:
            raise ValueError(f"Invalid connection hubs: {parts[0]}")
        if '-' in hub1 or '-' in hub2:
            raise ValueError(f"Hub names cannot contain '-': {parts[0]}")
        hubs: Tuple[str, str] = (hub1, hub2)
        if len(parts) == 1:
            return Connection(hubs=hubs)
        metadata: str = parts[1].strip()
        if not (metadata.startswith('[') and metadata.endswith(']')):
            raise ValueError(
                f"Invalid metadata format in connection {parts[0]}: "
                f"{metadata}")
        tags: List[str] = metadata[1:-1].split()
        seen_keys: Set[str] = set()
        max_link_capacity: int = 1
        for tag in tags:
            if '=' not in tag:
                raise ValueError(
                    f"Invalid metadata entry in connection {parts[0]}: {tag}")
            key, value = tag.split('=', 1)
            if key in seen_keys:
                raise ValueError(
                    f"Duplicate metadata in connection {parts[0]}: {key}")
            seen_keys.add(key)
            if key == 'max_link_capacity':
                try:
                    max_link_capacity = int(value)
                except ValueError:
                    raise ValueError(
                        f"Invalid max_link_capacity in connection {parts[0]}: "
                        f"{value}")
            else:
                raise ValueError(
                    f"Unknown metadata key in connection {parts[0]}: {key}")
        return Connection(hubs=hubs, max_link_capacity=max_link_capacity)

    first: Optional[str] = next(
        (line.strip() for line in lines
         if line.strip() and not line.strip().startswith('#')), None
        )
    if not first or not first.startswith('nb_drones:'):
        raise ValueError("First meaningful line must be nb_drones")
    seen_label: Set[str] = set()
    single_labels: Set[str] = {'nb_drones', 'start_hub', 'end_hub'}
    nb_drones: Optional[int] = None
    start_hub: Optional[Zone] = None
    end_hub: Optional[Zone] = None
    hubs: List[Zone] = []
    connections: List[Connection] = []
    for line in lines:
        line = line.strip()
        if line.startswith('#') or not line:
            continue
        if ':' not in line:
            raise ValueError(f"Invalid line: {line}")
        parts: List[str] = line.split(':', 1)
        label, config = parts
        label = label.strip()
        config = config.strip()
        if label in single_labels:
            if label in seen_label:
                raise ValueError(f"Duplicate {label}")
            seen_label.add(label)
        if label == 'nb_drones':
            try:
                nb_drones = int(config)
            except ValueError as error:
                raise ValueError(f"Invalid nb_drones: {config}") from error
        elif label == 'start_hub':
            start_hub = create_zone(config)
        elif label == 'end_hub':
            end_hub = create_zone(config)
        elif label == 'hub':
            hubs.append(create_zone(config))
        elif label == 'connection':
            connections.append(create_connection(config))
        else:
            raise ValueError(f"Unknown label: {label}")
    if nb_drones is None:
        raise ValueError("Missing nb_drones")
    if start_hub is None:
        raise ValueError("Missing start_hub")
    if end_hub is None:
        raise ValueError("Missing end_hub")
    return DronesNetwork(
        nb_drones=nb_drones, start_hub=start_hub, end_hub=end_hub,
        hubs=hubs, connections=connections)
