import pygame

from src.engine.scene import Scene


class GameplayScene(Scene):
    """Scene adapter for the existing ECS gameplay systems."""

    def __init__(self, engine) -> None:
        self.engine = engine

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            self.engine.paused = not self.engine.paused

    def update(self, delta_time: float) -> None:
        self.engine.delta_time = delta_time
        self.engine._update()

    def draw(self, target: pygame.Surface) -> None:
        self.engine._draw(target)
