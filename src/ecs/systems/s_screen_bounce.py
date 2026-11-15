

import esper
import pygame

from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_tag_enemy import CTagEnemy

def system_screen_bounce(world:esper.World, screen:pygame.Surface):
    screen_rect = screen.get_rect()
    components = world.get_components(
        CTagEnemy, CTransform, CVelocity, CSurface
    )

    c_t:CTransform
    c_v:CVelocity
    c_s:CSurface
    for _, (_, c_t, c_v, c_s) in components:
        cuad_rect = pygame.Rect(
            int(c_t.pos.x), int(c_t.pos.y), *c_s.size
        )
        if cuad_rect.left < 0 or cuad_rect.right > screen_rect.width:
            if c_v.vel.x:
                c_v.vel.x *= -1
            cuad_rect.clamp_ip(screen_rect)
            c_t.pos.x = float(cuad_rect.x)

        if cuad_rect.top < 0 or cuad_rect.bottom > screen_rect.height:
            if c_v.vel.y:
                c_v.vel.y *= -1
            cuad_rect.clamp_ip(screen_rect)
            c_t.pos.y = float(cuad_rect.y)
