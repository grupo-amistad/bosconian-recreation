import esper
import pygame

from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_world_entity import CWorldEntity
from src.engine.camera import wrap_position


def system_wraparound(world: esper.World, world_size: pygame.Vector2) -> None:
    for _, (_, transform) in world.get_components(CWorldEntity, CTransform):
        transform.pos.update(wrap_position(transform.pos, world_size))
