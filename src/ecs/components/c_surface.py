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
            self.surf = pygame.Surface(
                (max(1, int(size.x * frames)), max(1, int(size.y))), pygame.SRCALPHA
            )
            self.surf.fill(color or pygame.Color("white"))
        self.area = pygame.Rect(area) if area else self.surf.get_rect()
        if not image and not area:
            self.area.size = (max(1, int(size.x)), max(1, int(size.y)))

    @property
    def size(self):
        return self.area.size
