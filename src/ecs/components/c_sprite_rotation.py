import pygame


class CSpriteRotation:
   
    def __init__(self, base_image: pygame.Surface, step: float = 45.0) -> None:
        self.base_image = base_image
        self.step = step
        self.cache: dict[float, pygame.Surface] = {0.0: base_image}
        self.current_angle = 0.0