import pygame

from src.engine.scene import Scene
from src.player.player_commands import release_input_commands


class GameplayScene(Scene):

    def __init__(self, engine) -> None:
        self.engine = engine

    def on_enter(self) -> None:
        release_input_commands(self.engine.ecs_world)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            self.engine.pause(self)

    def update(self, delta_time: float) -> None:
        self.engine.delta_time = delta_time
        self.engine._update()

    def draw(self, target: pygame.Surface) -> None:
        self.engine._draw(target)
