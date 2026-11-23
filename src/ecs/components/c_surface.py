import pygame
from src.services import ServiceLocator


class CSurface:
    """Renderable texture and the source rectangle used as its sprite."""

    def __init__(self, image=None, area=None, size=None, color=None, frames=1) -> None:
        if image:
            try:
                self.surf = ServiceLocator.images.load(image)
                if size:
                    target_size = (
                        max(1, int(size.x * frames)),
                        max(1, int(size.y)),
                    )
                    self.surf = pygame.transform.scale(self.surf, target_size)
            except (FileNotFoundError, pygame.error):
                # Keep the prototype playable while optional/configured sprites
                # are still absent from the repository.
                image = None
        if not image:
            size = size or pygame.Vector2(16, 16)
            frame_count = max(1, int(frames))
            self.surf = pygame.Surface(
                (
                    max(1, int(size.x)) * frame_count,
                    max(1, int(size.y)),
                ),
                pygame.SRCALPHA,
            )
            base_color = color or pygame.Color("white")
            for frame in range(frame_count):
                shade = 0.7 + 0.3 * frame / max(1, frame_count - 1)
                frame_color = pygame.Color(
                    min(255, int(base_color.r * shade)),
                    min(255, int(base_color.g * shade)),
                    min(255, int(base_color.b * shade)),
                    base_color.a,
                )
                frame_rect = pygame.Rect(
                    frame * max(1, int(size.x)),
                    0,
                    max(1, int(size.x)),
                    max(1, int(size.y)),
                )
                pygame.draw.ellipse(self.surf, frame_color, frame_rect)
                if frame_count > 1:
                    pygame.draw.circle(
                        self.surf,
                        pygame.Color("white"),
                        (frame_rect.centerx, frame_rect.centery),
                        max(1, min(frame_rect.size) // 5),
                    )
        self.area = pygame.Rect(area) if area else self.surf.get_rect()
        if not image and not area:
            self.area.size = (max(1, int(size.x)), max(1, int(size.y)))
        self.base_image = self.surf.copy()

    @property
    def size(self):
        return self.area.size
