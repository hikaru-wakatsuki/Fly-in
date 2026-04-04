from typing import Dict, List, Tuple
import pygame


class PygameVisualizer:
    def __init__(self, zones:)































"""
output_visualized.py

Simple pygame visualizer for drone simulation.
Press SPACE to advance one turn.
"""

from typing import Dict, List, Tuple
import pygame


class PygameVisualizer:
    def __init__(
        self,
        zones: Dict[str, Tuple[int, int]],
        connections: List[Tuple[str, str]],
        turns: List[List[str]],
        zone_types: Dict[str, str],
    ) -> None:
        self.zones = zones
        self.connections = connections
        self.turns = turns
        self.zone_types = zone_types

        self.drone_positions: Dict[str, str] = {}
        self.current_turn: int = 0

        pygame.init()
        self.screen = pygame.display.set_mode((900, 700))
        pygame.display.set_caption("Drone Simulation")

        self.clock = pygame.time.Clock()

        self.scale = 40
        self.offset_x = 100
        self.offset_y = 100

    # -----------------------------
    # Utils
    # -----------------------------
    def to_screen(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        x, y = pos
        return (
            x * self.scale + self.offset_x,
            y * self.scale + self.offset_y,
        )

    def get_zone_color(self, zone: str) -> Tuple[int, int, int]:
        ztype = self.zone_types.get(zone, "normal")

        if ztype == "normal":
            return (200, 200, 200)
        if ztype == "restricted":
            return (255, 100, 100)
        if ztype == "priority":
            return (100, 255, 100)
        if ztype == "blocked":
            return (80, 80, 80)

        return (200, 200, 200)

    # -----------------------------
    # Simulation update
    # -----------------------------
    def update_positions(self) -> None:
        if self.current_turn >= len(self.turns):
            return

        for move in self.turns[self.current_turn]:
            drone, destination = move.split("-")
            self.drone_positions[drone] = destination

        self.current_turn += 1

    # -----------------------------
    # Draw functions
    # -----------------------------
    def draw_connections(self) -> None:
        for a, b in self.connections:
            pygame.draw.line(
                self.screen,
                (120, 120, 120),
                self.to_screen(self.zones[a]),
                self.to_screen(self.zones[b]),
                2,
            )

    def draw_zones(self) -> None:
        for name, pos in self.zones.items():
            pygame.draw.circle(
                self.screen,
                self.get_zone_color(name),
                self.to_screen(pos),
                10,
            )

    def draw_drones(self) -> None:
        for drone, zone in self.drone_positions.items():
            pygame.draw.circle(
                self.screen,
                (0, 200, 255),
                self.to_screen(self.zones[zone]),
                6,
            )

    def draw_text(self) -> None:
        font = pygame.font.SysFont(None, 28)
        text = font.render(f"Turn: {self.current_turn}", True, (255, 255, 255))
        self.screen.blit(text, (20, 20))

    # -----------------------------
    # Main loop
    # -----------------------------
    def run(self) -> None:
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.update_positions()

            self.screen.fill((30, 30, 30))

            self.draw_connections()
            self.draw_zones()
            self.draw_drones()
            self.draw_text()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    zones = {
        "hub": (0, 0),
        "roof1": (3, 4),
        "corridorA": (4, 3),
        "tunnelB": (7, 4),
        "goal": (10, 10),
    }

    connections = [
        ("hub", "roof1"),
        ("hub", "corridorA"),
        ("roof1", "corridorA"),
        ("corridorA", "tunnelB"),
        ("tunnelB", "goal"),
    ]

    zone_types = {
        "hub": "normal",
        "roof1": "restricted",
        "corridorA": "priority",
        "tunnelB": "normal",
        "goal": "normal",
    }

    turns = [
        ["D1-roof1", "D2-corridorA"],
        ["D1-corridorA", "D2-tunnelB"],
        ["D1-tunnelB", "D2-goal"],
        ["D1-goal"],
    ]

    visualizer = PygameVisualizer(zones, connections, turns, zone_types)
    visualizer.run()
🎯 これでできること
ノード表示（色付
