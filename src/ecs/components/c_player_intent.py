import pygame


class CPlayerIntent:
    
    def __init__(self) -> None:
        self.move = pygame.Vector2()
        self.fire = False
        self.fire_held = False
        self.special = False