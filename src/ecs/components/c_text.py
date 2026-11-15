import pygame


class CText:
    def __init__(self, text: str, font: pygame.font.Font, color: pygame.Color, pos: pygame.Vector2) -> None:
        self.text = text
        self.font = font
        self.color = color
        self.pos = pygame.Vector2(pos)
        self.surface = font.render(text, True, color)

    def set_text(self, text: str) -> None:
        if text != self.text:
            self.text = text
            self.surface = self.font.render(text, True, self.color)
