import math

import esper
import pygame

from src.ecs.components.c_sprite_rotation import CSpriteRotation
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.c_tag_enemy import CTagEnemy


def _rotated(base: pygame.Surface, angle: float) -> pygame.Surface:
    # pygame rotates counter-clockwise; headings are clockwise.
    rotated = pygame.transform.rotate(base, -angle)
    image = pygame.Surface(base.get_size(), pygame.SRCALPHA)
    image.blit(rotated, rotated.get_rect(center=image.get_rect().center))
    return image


def system_sprite_rotation(world: esper.World) -> None:
    for _, (_, _, transform, velocity) in world.get_components(
        CTagEnemy, CSpriteRotation, CTransform, CVelocity
    ):
        if velocity.vel.length_squared() > 0.01:
            transform.angle = math.degrees(
                math.atan2(velocity.vel.x, -velocity.vel.y)
            ) % 360

    for _, (rotation, transform, surface) in world.get_components(
        CSpriteRotation, CTransform, CSurface
    ):
        step = rotation.step if rotation.step > 0 else 1.0
        angle = (round(transform.angle / step) * step) % 360
        if angle == rotation.current_angle and surface.surf is rotation.cache.get(angle):
            continue
        if angle not in rotation.cache:
            rotation.cache[angle] = _rotated(rotation.base_image, angle)
        surface.surf = rotation.cache[angle]
        surface.area = surface.surf.get_rect()
        rotation.current_angle = angle
