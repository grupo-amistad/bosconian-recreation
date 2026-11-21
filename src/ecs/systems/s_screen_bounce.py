

import esper
import pygame

from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_tag_enemy import CTagEnemy
from src.ecs.components.c_combat import CTagObstacle

def system_screen_bounce(world:esper.World, screen:pygame.Surface):
    screen_rect = screen.get_rect()
    components = world.get_components(
        CTagEnemy, CTransform, CVelocity, CSurface
    )

    c_t:CTransform
    c_v:CVelocity
    c_s:CSurface
    for _, (_, c_t, c_v, c_s) in components:
        _bounce_inside(c_t, c_v, c_s, screen_rect)
    obstacles = world.get_components(
        CTagObstacle, CTransform, CVelocity, CSurface
    )
    for _, (_, c_t, c_v, c_s) in obstacles:
        _bounce_inside(c_t, c_v, c_s, screen_rect)


def _bounce_inside(transform, velocity, surface, bounds):
    rect = pygame.Rect(int(transform.pos.x), int(transform.pos.y), *surface.size)
    if rect.left < bounds.left or rect.right > bounds.right:
        velocity.vel.x *= -1
        rect.clamp_ip(bounds)
        transform.pos.x = float(rect.x)
    if rect.top < bounds.top or rect.bottom > bounds.bottom:
        velocity.vel.y *= -1
        rect.clamp_ip(bounds)
        transform.pos.y = float(rect.y)
