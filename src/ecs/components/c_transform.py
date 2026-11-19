import pygame


class CTransform:
    """World position and orientation, measured in pixels and degrees."""

    def __init__(self, pos: pygame.Vector2, angle: float = 0.0) -> None:
        self.pos = pygame.Vector2(pos)
        self.angle = float(angle)
