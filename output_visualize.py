import pygame
from typing import Dict, List, Tuple, Optional
from parse_input_file import Zone, ZoneType


# 拡大倍率
SCALE = 160
# 画面上の位置調整
ZONE_SIZE = max(8, SCALE // 5)
MULTI_ZONE_SIZE = max(10, ZONE_SIZE * 1.2)
ANN_ZONE_SIZE = SCALE // 6
DRONE_RADIUS = max(2, SCALE // 10)
LINK_WIDTH_UNIT = max(1, SCALE // 16)
FONT = max(1, SCALE // 4)
ZONE_FONT = max(1, SCALE // 6)
MARGIN = SCALE // 2
HUD_TOP = SCALE * 2
ANNOTATION = SCALE // 4

FPS = 60

BG_COLOR = (30, 30, 30)
LINK_COLOR = (80, 80, 80)
WHITE = (220, 220, 220)
RED = (255, 0, 0)
MUTED_RED = (255, 80, 80)
LIGHT_PINK = (255, 180, 180)
YELLOW = (255, 255, 80)
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
    font = pygame.font.Font(None, FONT)
    zone_font = pygame.font.Font(None, ZONE_FONT)

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
        for zone in zones:
            x, y = to_screen(zone, offset_x, offset_y)
            zone_color = parse_color(zone.color)
            if zone.max_drones > 1:
                # 四角形(left, top, width, height)
                rect = pygame.Rect(x - MULTI_ZONE_SIZE, y - MULTI_ZONE_SIZE,
                                   MULTI_ZONE_SIZE * 2, MULTI_ZONE_SIZE * 2)
                pygame.draw.rect(screen, WHITE, rect, 0)
            rect = pygame.Rect(
                x - ZONE_SIZE, y - ZONE_SIZE, ZONE_SIZE * 2, ZONE_SIZE * 2)
            pygame.draw.rect(screen, zone_color, rect, 0)
            name_color = (RED if zone.zone == ZoneType.RESTRICTED else (
                YELLOW if zone.zone == ZoneType.PRIORITY else WHITE
            ))
            zone_name = zone_font.render(zone.name, True, name_color)
            screen.blit(zone_name, (x - MULTI_ZONE_SIZE, y + MULTI_ZONE_SIZE))

        # --- drones ---
        curr = (movements[turn + 1]
                if turn != len(movements) - 1 else movements[turn])
        prev = movements[turn]

        for drone_id in curr:
            x, y = interpolate_position(prev[drone_id], curr[drone_id],
                                        progress, offset_x, offset_y)
            pygame.draw.circle(
                screen, MUTED_RED, (x, y), DRONE_RADIUS)
            drone_label = font.render(f"D{drone_id}", True, LIGHT_PINK)
            screen.blit(drone_label, (x + (SCALE // 10), y))

        # 注記
        turn_label = font.render(f"Turn: {turn}", True, TEXT_COLOR)
        screen.blit(turn_label, (ANNOTATION, ANNOTATION))
        outer_rect = pygame.Rect(
            ANNOTATION, ANNOTATION * 2, ANN_ZONE_SIZE, ANN_ZONE_SIZE)
        pygame.draw.rect(screen, WHITE, outer_rect, 2)
        legend_text = font.render("Capacity >= 2", True, TEXT_COLOR)
        screen.blit(legend_text, (ANNOTATION * 2, ANNOTATION * 2))
        restricted_text = font.render("Restricted Zone", True, RED)
        screen.blit(restricted_text, (ANNOTATION, ANNOTATION * 3))
        priority_text = font.render("Priority Zone", True, YELLOW)
        screen.blit(priority_text, (ANNOTATION, ANNOTATION * 4))
        pygame.display.flip()
    pygame.time.wait(2000)
    pygame.quit()


def get_screen_layout(
        graph: Dict[Zone, List[Tuple[Zone, int]]]
        ) -> Tuple[int, int, int, int]:
    """グラフ全体が収まる画面サイズとオフセットを返す"""
    x_list: List[int] = [zone.coordinate[0] for zone in graph]
    y_list: List[int] = [zone.coordinate[1] for zone in graph]
    min_x: int = min(x_list)
    max_x: int = max(x_list)
    min_y: int = min(y_list)
    max_y: int = max(y_list)
    graph_width: int = (max_x - min_x) * SCALE
    graph_height: int = (max_y - min_y) * SCALE
    width: int = graph_width + MARGIN * 2
    height: int = HUD_TOP + graph_height + MARGIN * 2
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


def advance_turn_progress(progress: float, dt: float,
                          turn: int) -> Tuple[float, int]:
    """経過時間からターンの進行度とターン番号を更新する"""
    # ターン内の進行度を更新（0.0〜1.0）
    progress += dt

    # 1ターン分進んだら次のターンへ
    if progress >= 1.0:
        progress = 0.0
        turn += 1
    return progress, turn


def interpolate_position(prev_zones: List[Zone], curr_zones: List[Zone],
                         progress_in_turn: float,
                         ox, oy) -> Tuple[int, int]:
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
    return (int(px + (cx - px) * progress_in_turn),
            int(py + (cy - py) * progress_in_turn))


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
