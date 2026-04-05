import pygame
from typing import Dict, List, Tuple, Optional
from parse_input_file import Zone


def visualize(
    logs: List[List[str]], graph: Dict[Zone, List[Tuple[Zone, int]]]) -> None:
    # 初期化
    pygame.init()
    screen = pygame.display.set_mode((1800, 600))
    pygame.display.set_caption("Fly-in Visualization")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 20)

    # 拡大倍率
    SCALE = 80
    # 画面上の位置調整
    OFFSET_X = 30
    OFFSET_Y = 300

    # 色変換
    def parse_color(color: Optional[str]) -> Tuple[int, int, int]:
        if color is None:
            return (120, 200, 255)
        try:
            c = pygame.Color(color)
            return (c.r, c.g, c.b)
        except ValueError:
            return (120, 200, 255)

    # 座標変換
    def to_screen(zone: Zone) -> Tuple[int, int]:
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
            for zone_name in zone_names:
                if zone_name in zone_map:
                    # zone追加
                    turn_state[drone_id].append(zone_map[zone_name])
        drone_movements.append(turn_state)

    t = 0
    running = True

    while running:
        screen.fill((20, 20, 20))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # edge draw
        for from_zone, edges in graph.items():
            x1, y1 = to_screen(from_zone)
            for to_zone, _ in edges:
                x2, y2 = to_screen(to_zone)
                pygame.draw.line(screen, (80, 80, 80), (x1, y1), (x2, y2), 1)

        # zone draw
        for zone in zone_map.values():
            x, y = to_screen(zone)
            zone_color = parse_color(zone.color)

            pygame.draw.circle(screen, zone_color, (x, y), 18)

            if zone.max_drones > 1:
                pygame.draw.circle(screen, (220, 220, 220), (x, y), 24, 1)

            label = font.render(zone.name, True, (220, 220, 220))
            screen.blit(label, (x + 10, y + 10))

        # drone draw
        if 0 <= t < len(drone_movements):
            for drone_id, zone in drone_movements[t].items():
                x, y = to_screen(zone)

                pygame.draw.circle(screen, (255, 80, 80), (x, y), 6)
                drone_label = font.render(f"D{drone_id}", True, (255, 180, 180))
                screen.blit(drone_label, (x + 8, y - 18))

        turn_label = font.render(f"Turn: {t}", True, (255, 255, 255))
        screen.blit(turn_label, (20, 20))

        pygame.display.flip()

        if t < len(drone_movements) - 1:
            t += 1

        clock.tick(2)

    pygame.quit()
