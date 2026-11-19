import pygame


class CHitBox:
    """Axis-aligned collision box, independent of the rendered sprite."""

    def __init__(
        self,
        size: pygame.Vector2,
        offset: pygame.Vector2 | None = None,
    ) -> None:
        self.size = pygame.Vector2(size)
        self.offset = pygame.Vector2(offset or (0, 0))

    def rect_at(self, position: pygame.Vector2) -> pygame.Rect:
        top_left = pygame.Vector2(position) + self.offset
        return pygame.Rect(
            round(top_left.x),
            round(top_left.y),
            max(1, round(self.size.x)),
            max(1, round(self.size.y)),
        )
