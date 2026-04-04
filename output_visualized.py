import pygame
from typing import Dict, List, Tuple

from parse_input_file import Zone


def visualize(logs: List[List[str]],
              graph: Dict[Zone, List[Tuple[Zone, int]]]) -> None:
    pygame.init()

    screen = pygame.display.set_mode((1000, 800))
    clock = pygame.time.Clock()

    # =========================
    # Zone一覧取得
    # =========================
    zones = set()
    for turn in logs:
        for item in turn:
            parts = item.split("-")
            for p in parts[1:]:
                zones.add(p)

    # graphにもいるので統合
    zones.update(graph.keys())

    # =========================
    # 仮座標生成（本番はここ差し替え）
    # =========================
    pos: Dict[Zone, Tuple[int, int]] = {}

    for i, z in enumerate(zones):
        pos[z] = (
            100 + (i * 80) % 800,
            100 + ((i * 80) // 800) * 120
        )

    # =========================
    # logsパース（turn -> drone -> zone）
    # =========================
    state: List[Dict[int, Zone]] = []

    for turn in logs:
        frame = {}
        for item in turn:
            parts = item.split("-")

            drone_id = int(parts[0][1:])  # D1 → 1
            zone_name = parts[-1]

            frame[drone_id] = zone_name

        state.append(frame)

    # =========================
    # pygame loop
    # =========================
    t = 0
    running = True

    while running:
        screen.fill((20, 20, 20))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # =========================
        # graph描画（edge）
        # =========================
        for from_zone, edges in graph.items():
            if from_zone not in pos:
                continue

            x1, y1 = pos[from_zone]

            for to_zone, _ in edges:
                if to_zone not in pos:
                    continue

                x2, y2 = pos[to_zone]
                pygame.draw.line(screen, (80, 80, 80), (x1, y1), (x2, y2), 1)

        # =========================
        # zone描画
        # =========================
        for z, (x, y) in pos.items():
            pygame.draw.circle(screen, (120, 200, 255), (x, y), 18)

        # =========================
        # drone描画
        # =========================
        if t < len(state):
            for drone_id, zone in state[t].items():
                if zone in pos:
                    x, y = pos[zone]
                    pygame.draw.circle(screen, (255, 80, 80), (x, y), 6)

        pygame.display.flip()

        t += 1
        if t >= len(state):
            t = len(state) - 1

        clock.tick(5)

    pygame.quit()
