import pygame


class CVelocity:
    """World velocity in pixels per second."""

    def __init__(self, vel: pygame.Vector2) -> None:
        self.vel = pygame.Vector2(vel)
