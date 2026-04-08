import pygame
from typing import Dict, List, Tuple, Optional
from parse_input_file import Zone, ZoneType


def visualize(logs: List[List[str]],
              graph: Dict[Zone, List[Tuple[Zone, int]]]) -> None:
    """ドローンシミュレーション結果をPygameで可視化

    ログを元に、ゾーン・リンク・ドローンの動きをターンごとに描画

    描画内容:
        - ゾーン（四角形）
            - 色: zone.color（未指定はグレー）
            - max_drones >= 2 の場合は外枠表示
            - RESTRICTEDゾーンは赤文字
        - リンク（線）
            - 太さは max_link_capacity に比例
        - ドローン（円）
            - ゾーン上またはリンク中間に描画
        - ターン表示および凡例
    """
    # pygameスタート
    pygame.init()

    max_x = max(zone.coordinate[0] for zone in graph.keys())
    min_x = min(zone.coordinate[0] for zone in graph.keys())
    max_y = max(zone.coordinate[1] for zone in graph.keys())
    min_y = min(zone.coordinate[1] for zone in graph.keys())

    # 拡大倍率
    SCALE = 80
    # 画面上の位置調整
    MARGIN = 50
    width = (max_x - min_x) * SCALE + MARGIN * 2
    height = (max_y - min_y) * SCALE + MARGIN * 2
    OFFSET_X = -min_x * SCALE + MARGIN
    OFFSET_Y = -min_y * SCALE + MARGIN

    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Fly-in Visualization")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 28)
    zone_font = pygame.font.Font(None, 14)

    # 色変換
    def parse_color(color: Optional[str]) -> Tuple[int, int, int]:
        """文字列カラーをRGBタプルに変換"""
        if color is None:
            return (120, 120, 120)
        try:
            c = pygame.Color(color)
            return (c.r, c.g, c.b)
        except ValueError as error:
            raise ValueError(f"Invalid color value: '{color}'") from error

    # 座標変換
    def to_screen(zone: Zone) -> Tuple[int, int]:
        """ゾーン座標を画面座標へ変換"""
        x, y = zone.coordinate
        return (
            x * SCALE + OFFSET_X,
            y * SCALE + OFFSET_Y,
        )
    # Zoneの辞書化
    zone_map: Dict[str, Zone] = {}
    for from_zone, edges in graph.items():
        zone_map[from_zone.name] = from_zone
        for to_zone, _ in edges:
            zone_map[to_zone.name] = to_zone

    # logs → state変換
    drone_movements: List[Dict[int, List[Zone]]] = []
    for turn in logs:
        turn_state: Dict[int, List[Zone]] = {}
        for item in turn:
            parts = item.split("-")
            # key=ドローン番号
            drone_id = int(parts[0][1:])
            turn_state[drone_id] = []
            zone_names = parts[1:]
            for zone_key in zone_names:
                if zone_key in zone_map:
                    # zone追加
                    turn_state[drone_id].append(zone_map[zone_key])
        drone_movements.append(turn_state)

    turn: int = 1
    running = True

    while running:
        # 画面リセット
        screen.fill((20, 20, 20))
        # イベント：ユーザがpygameを閉じた場合
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Zoneのlinkに線を引く
        for from_zone, edges in graph.items():
            x1, y1 = to_screen(from_zone)
            for to_zone, max_link_capacity in edges:
                x2, y2 = to_screen(to_zone)
                max_link_capacity *= 5
                pygame.draw.line(
                    screen, (80, 80, 80), (x1, y1), (x2, y2),
                    max_link_capacity)

        # Zoneを描写
        for zone in zone_map.values():
            x, y = to_screen(zone)
            zone_color = parse_color(zone.color)
            if zone.max_drones > 1:
                rect = pygame.Rect(x - 21, y - 21, 42, 42)
                pygame.draw.rect(screen, (220, 220, 220), rect, 0)
            # 四角形(left, top, width, height)
            rect = pygame.Rect(x - 18, y - 18, 36, 36)
            pygame.draw.rect(screen, zone_color, rect, 0)
            name_color = ((255, 0, 0) if zone.zone == ZoneType.RESTRICTED
                          else (220, 220, 220))
            zone_name = zone_font.render(zone.name, True, name_color)
            screen.blit(zone_name, (x - 9 - len(zone.name), y - 35))

        # Droneを描写
        if turn - 1 < len(drone_movements):
            for drone_id, zones in drone_movements[turn - 1].items():
                # 到着
                if len(zones) == 1:
                    x, y = to_screen(zones[0])
                # link上
                if len(zones) == 2:
                    x1, y1 = to_screen(zones[0])
                    x2, y2 = to_screen(zones[1])
                    x, y = (x1 + x2) / 2, (y1 + y2) / 2
                pygame.draw.circle(screen, (255, 80, 80), (x, y), 8)
                drone_label = font.render(f"D{drone_id}",
                                          True, (255, 180, 180))
                screen.blit(drone_label, (x + 8, y - 18))

        turn_label = font.render(f"Turn: {turn}", True, (255, 255, 255))
        screen.blit(turn_label, (20, 20))
        # ① max_drones >= 2
        outer_rect = pygame.Rect(20, 50, 20, 20)
        pygame.draw.rect(screen, (220, 220, 220), outer_rect, 2)
        legend_text = font.render("Capacity >= 2", True, (255, 255, 255))
        screen.blit(legend_text, (50, 50))

        # ② restricted zone
        restricted_text = font.render("Restricted Zone", True, (255, 0, 0))
        screen.blit(restricted_text, (20, 80))
        pygame.display.flip()

        if turn < len(drone_movements):
            turn += 1

        clock.tick(1)

    pygame.quit()
