import pygame
from typing import Dict, List, Tuple, Optional
from parse_input_file import Zone, ZoneType


# 拡大倍率
SCALE = 80
# 画面上の位置調整
ZONE_SIZE = max(8, SCALE // 5)
DRONE_RADIUS = max(4, SCALE // 10)
LINK_WIDTH_UNIT = max(1, SCALE // 16)

MARGIN = SCALE // 2
HUD_TOP = SCALE * 2
FPS = 60

BG_COLOR = (20, 20, 20)
LINK_COLOR = (80, 80, 80)
TEXT_COLOR = (255, 255, 255)


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

    width, height, offset_x, offset_y = get_screen_layout(graph)
    zones = list(graph.keys())
    movements = build_movements(logs, graph, start, drone_count)

    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Fly-in Visualization")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 28)
    zone_font = pygame.font.Font(None, 14)

    turn: int = 0
    progress: float = 0.0

    while turn < len(movements) - 1:
        # 時間更新
        dt = clock.tick(FPS) / 1000.0
        progress, turn = advance_turn_progress(
            progress, dt, turn)

        # 画面リセット
        screen.fill(BG_COLOR)

        # イベント：ユーザがpygameを閉じた場合
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        # --- links ---
        for from_zone, edges in graph.items():
            x1, y1 = to_screen(from_zone, offset_x, offset_y)
            for to_zone, capacity in edges:
                x2, y2 = to_screen(to_zone, offset_x, offset_y)
                pygame.draw.line(screen, LINK_COLOR, (x1, y1), (x2, y2),
                                 capacity * 5)

        # --- zones ---
        diameter: int = SCALE // 5
        for zone in zones:
            x, y = to_screen(zone, offset_x, offset_y)
            zone_color = parse_color(zone.color)
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
        curr = (movements[turn + 1]
                if turn != len(movements) - 1 else movements[turn])
        prev = movements[turn]

        for drone_id in curr:
            x, y = interpolate_position(prev[drone_id], curr[drone_id],
                                        progress, offset_x, offset_y)

            pygame.draw.circle(screen, (255, 80, 80), (int(x), int(y)), 8)
            drone_label = font.render(f"D{drone_id}", True, (255, 180, 180))
            screen.blit(drone_label, (int(x) + 8, int(y) - 18))

        turn_label = font.render(f"Turn: {turn}", True, TEXT_COLOR)
        screen.blit(turn_label, (20, 20))
        # ① max_drones >= 2
        outer_rect = pygame.Rect(20, 50, 20, 20)
        pygame.draw.rect(screen, (220, 220, 220), outer_rect, 2)
        legend_text = font.render("Capacity >= 2", True, TEXT_COLOR)
        screen.blit(legend_text, (50, 50))

        # ② restricted zone
        restricted_text = font.render("Restricted Zone", True, (255, 0, 0))
        screen.blit(restricted_text, (20, 80))
        pygame.display.flip()
    pygame.time.wait(2000)
    pygame.quit()


def get_screen_layout(graph: Dict[Zone, List[Tuple[Zone, int]]]) -> Tuple[int, int, int, int]:
    """グラフ全体が収まる画面サイズとオフセットを返す"""
    x_list: List[int] = [zone.coordinate[0] for zone in graph]
    y_list: List[int] = [zone.coordinate[1] for zone in graph]
    min_x: int = min(x_list)
    max_x: int = max(x_list)
    min_y: int = min(y_list)
    max_y: int = max(y_list)
    graph_width: int = (max_x - min_x) * SCALE
    graph_heigth: int = (max_y - min_y) * SCALE
    width: int = graph_width + MARGIN * 2
    height: int = HUD_TOP + graph_heigth + MARGIN * 2
    offset_x: int = MARGIN - min_x * SCALE
    offset_y: int = HUD_TOP + MARGIN - min_y * SCALE
    return (width, height, offset_x, offset_y)


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
                         progress_in_turn: float,
                         ox, oy) -> Tuple[float, float]:
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
    return (px + (cx - px) * progress_in_turn,
            py + (cy - py) * progress_in_turn)


def build_movements(logs: List[List[str]],
                    graph: Dict[Zone, List[Tuple[Zone, int]]],
                    start: Zone,
                    drone_count: int) -> List[Dict[int, List[Zone]]]:
    """ログをターンごとの状態に変換"""
    # Zone名の辞書
    zone_map: Dict[str, Zone] = {}
    for from_zone, edges in graph.items():
        zone_map[from_zone.name] = from_zone
        for to_zone, _ in edges:
            zone_map[to_zone.name] = to_zone

    movements: List[Dict[int, List[Zone]]] = []
    # 初期位置
    current_movement: Dict[int, List[Zone]] = {
        i: [start] for i in range(1, drone_count + 1)}
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
