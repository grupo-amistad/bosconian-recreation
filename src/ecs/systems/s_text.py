import esper
import pygame

from src.ecs.components.c_text import CText


def system_text_rendering(world: esper.World, screen: pygame.Surface) -> None:
    for _, (text,) in world.get_components(CText):
        screen.blit(text.surface, text.pos)
