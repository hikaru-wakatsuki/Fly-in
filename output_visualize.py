import pygame
from typing import Dict, List, Tuple, Optional
from parse_input_file import Zone, ZoneType


# 拡大倍率
SCALE = 80
# 画面上の位置調整
MARGIN = 50


def visualize(logs: List[List[str]],
              graph: Dict[Zone, List[Tuple[Zone, int]]],
              start: Zone, drone_count: int) -> None:
    """ドローンシミュレーション結果をPygameで可視化

    ログを元に、ゾーン・リンク・ドローンの動きをターンごとに描画

    描画内容:
        - ゾーン（四角形）
            - 色: zone.color(未指定はグレー)
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

    width = (max_x - min_x) * SCALE + MARGIN * 2
    height = (max_y - min_y) * SCALE + MARGIN * 2
    OFFSET_X = -min_x * SCALE + MARGIN
    OFFSET_Y = -min_y * SCALE + MARGIN

    zones = list(graph.keys())
    movements = build_movements(logs, graph, start, drone_count)

    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Fly-in Visualization")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 28)
    zone_font = pygame.font.Font(None, 14)

    turn: int = 0
    progress_in_turn: float = 0.0
    FPS = 60

    running = True

    while running:
        # 時間更新
        dt = clock.tick(FPS) / 1000.0
        progress_in_turn, turn = advance_turn_progress(progress_in_turn, dt, turn)

        # 画面リセット
        screen.fill((20, 20, 20))

        # イベント：ユーザがpygameを閉じた場合
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- links ---
        for from_zone, edges in graph.items():
            x1, y1 = to_screen(from_zone, OFFSET_X, OFFSET_Y)
            for to_zone, max_link_capacity in edges:
                x2, y2 = to_screen(to_zone, OFFSET_X, OFFSET_Y)
                pygame.draw.line(screen, (80, 80, 80), (x1, y1), (x2, y2),
                                 max_link_capacity * 5)

        # --- zones ---
        for zone in zones:
            x, y = to_screen(zone, OFFSET_X, OFFSET_Y)
            zone_color = parse_color(zone.color)
            diameter: int = SCALE // 5
            if zone.max_drones > 1:
                white_diameter: int = diameter + 5
                rect = pygame.Rect(
                    x - white_diameter, y - white_diameter,
                    white_diameter * 2, white_diameter * 2)
                pygame.draw.rect(screen, (220, 220, 220), rect, 0)
            # 四角形(left, top, width, height)
            rect = pygame.Rect(
                x - diameter, y - diameter, diameter * 2, diameter * 2)
            pygame.draw.rect(screen, zone_color, rect, 0)
            name_color = ((255, 0, 0) if zone.zone == ZoneType.RESTRICTED
                          else (220, 220, 220))
            zone_name = zone_font.render(zone.name, True, name_color)
            screen.blit(zone_name, (x - 9 - len(zone.name), y - 35))

        # --- drones ---
        curr = movements[turn]
        prev = movements[turn - 1] if turn > 0 else curr

        for drone_id in curr:
            x, y = interpolate_position(prev[drone_id], curr[drone_id], progress_in_turn,
                                        OFFSET_X, OFFSET_Y)

            pygame.draw.circle(screen, (255, 80, 80), (int(x), int(y)), 8)
            drone_label = font.render(f"D{drone_id}",
                                        True, (255, 180, 180))
            screen.blit(drone_label, (int(x) + 8, int(y) - 18))

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

    pygame.quit()


def to_screen(zone: Zone, offset_x: int, offset_y: int) -> Tuple[int, int]:
    """ゾーン座標を画面座標へ変換"""
    x, y = zone.coordinate
    return (x * SCALE + offset_x, y * SCALE + offset_y)


def parse_color(color: Optional[str]) -> Tuple[int, int, int]:
    """文字列カラーをRGBタプルに変換"""
    if color is None:
        color = 'gray'
    try:
        c = pygame.Color(color)
        return (c.r, c.g, c.b)
    except ValueError:
        return parse_color('gray')


def advance_turn_progress(progress_in_turn, dt, turn, turn_duration=1.0):
    """経過時間からターンの進行度とターン番号を更新する"""
    # ターン内の進行度を更新（0.0〜1.0）
    progress_in_turn += dt / turn_duration

    # 1ターン分進んだら次のターンへ
    if progress_in_turn >= 1.0:
        progress_in_turn = 0.0
        turn += 1
    return progress_in_turn, turn


def interpolate_position(prev_zones: List[Zone], curr_zones: List[Zone],
                         progress_in_turn: float, ox, oy) -> Tuple[float, float]:
    """前ターン→現在ターンを補間"""
    def get_pos(zones):
        if len(zones) == 1:
            return to_screen(zones[0], ox, oy)
        else:
            x1, y1 = to_screen(zones[0], ox, oy)
            x2, y2 = to_screen(zones[1], ox, oy)
            return ((x1 + x2) / 2, (y1 + y2) / 2)

    px, py = get_pos(prev_zones)
    cx, cy = get_pos(curr_zones)
    return (px + (cx - px) * progress_in_turn, py + (cy - py) * progress_in_turn)


def draw_drones(screen, movements, turn, frame_progress, font):
    if turn >= len(movements):
        return
    curr = movements[turn]
    prev = movements[turn - 1] if turn > 0 else curr

    for drone_id in curr.keys():
        curr_zones = curr[drone_id]
        prev_zones = prev.get(drone_id, curr_zones)

        x, y = interpolate_position(prev_zones, curr_zones, frame_progress, to_screen)


def build_movements(logs: List[List[str]],
                 graph: Dict[Zone, List[Tuple[Zone, int]]],
                 start: Zone, drone_count: int) -> List[Dict[int, List[Zone]]]:
    """ログをターンごとの状態に変換"""
    # Zone名の辞書
    zone_map: Dict[str, Zone] = {}
    for from_zone, edges in graph.items():
        zone_map[from_zone.name] = from_zone
        for to_zone, _ in edges:
            zone_map[to_zone.name] = to_zone

    movements: List[Dict[int, List[Zone]]] = []
    # 初期位置
    current_movement: Dict[int, List[Zone]] = {i: [start] for i in range(1, drone_count + 1)}
    movements.append(current_movement.copy())

    for turn in logs:
        next_movement: Dict[int, List[Zone]] = current_movement.copy()
        for item in turn:
            parts: List[str] = item.split("-")
            # key=ドローン識別番号
            drone_id: int = int(parts[0][1:])
            # len(Zone)==1:Zone到着、len(Zone)==2:link
            zones: List[Zone] = [zone_map[name] for name in parts[1:]]
            next_movement[drone_id] = zones
        movements.append(next_movement)
        current_movement = next_movement

    return movements
