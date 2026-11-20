
import esper
import pygame

from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_world_entity import CWorldEntity


def system_rendering(world: esper.World, screen: pygame.Surface, camera=None):
    components = world.get_components(CTransform, CSurface)
    world_entities = {
        entity for entity, _ in world.get_components(CWorldEntity)
    }
    for entity, (transform, surface) in components:
        if camera is not None and entity in world_entities:
            for screen_pos in camera.render_positions(transform.pos, pygame.Vector2(surface.size)):
                screen.blit(surface.surf, screen_pos, surface.area)
        else:
            screen.blit(surface.surf, transform.pos, surface.area)
