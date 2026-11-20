import esper
import pygame
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.c_hitbox import CHitBox
from src.ecs.components.c_world_entity import CWorldEntity
from src.ecs.components.c_tag_bullet import CTagBullet
from src.ecs.components.c_tag_enemy import CTagEnemy
from src.ecs.components.c_tag_player import CTagPlayer
from src.ecs.components.c_animation import Animation, CAnimation


def animations_from_config(config):
    data = config.get("animations", [])
    if isinstance(data, dict):
        data = data.get("list", [])
    return [Animation(a["name"], a["start"], a["end"], a["framerate"])
            for a in data]


def animation_frame_count(config):
    data = config.get("animations", {})
    return data.get("number_frames", config.get("frames", 1)) if isinstance(data, dict) else config.get("frames", 1)


def create_entity(world, pos, vel, tag, image=None, size=None, color=None,
                  area=None, animations=None, frames=1, extra=None,
                  hitbox_size=None, hitbox_offset=None):
    entity = world.create_entity()
    surface = CSurface(image=image, area=area, size=size, color=color, frames=frames)
    if image and animations and frames > 1:
        frame_width = surface.surf.get_width() // frames
        surface.area = pygame.Rect(0, 0, frame_width, surface.surf.get_height())
    world.add_component(entity, surface)
    world.add_component(entity, CTransform(pygame.Vector2(pos)))
    world.add_component(entity, CVelocity(pygame.Vector2(vel)))
    world.add_component(entity, CWorldEntity())
    collision_size = (
        pygame.Vector2(hitbox_size)
        if hitbox_size is not None
        else pygame.Vector2(surface.size)
    )
    collision_offset = (
        pygame.Vector2(hitbox_offset)
        if hitbox_offset is not None
        else pygame.Vector2()
    )
    world.add_component(entity, CHitBox(collision_size, collision_offset))
    if tag:
        world.add_component(entity, tag())
    if animations:
        world.add_component(entity, CAnimation(frames, animations))
    if extra:
        world.add_component(entity, extra)
    return entity


def create_square(world, size, pos, vel, col, **kwargs):
    return create_entity(world, pos, vel, CTagEnemy, size=size, color=col, **kwargs)


def create_player(world, size, pos, vel, col, **kwargs):
    return create_entity(world, pos, vel, CTagPlayer, size=size, color=col, **kwargs)


def create_bullet(world, size, pos, vel, col, **kwargs):
    return create_entity(world, pos, vel, CTagBullet, size=size, color=col, **kwargs)
