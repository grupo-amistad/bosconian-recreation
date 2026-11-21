import esper
import pygame

from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_tag_bullet import CTagBullet
from src.ecs.components.c_tag_player import CTagPlayer
from src.ecs.components.c_combat import CTagEnemyBullet
from src.ecs.components.c_transform import CTransform


def system_player_boundary(world: esper.World, screen: pygame.Surface) -> None:
    screen_rect = screen.get_rect()
    for _, (_, transform, surface) in world.get_components(
        CTagPlayer, CTransform, CSurface
    ):
        max_x = screen_rect.right - surface.size[0]
        max_y = screen_rect.bottom - surface.size[1]
        transform.pos.x = max(screen_rect.left, min(transform.pos.x, max_x))
        transform.pos.y = max(screen_rect.top, min(transform.pos.y, max_y))


def system_bullet_boundary(world: esper.World, screen: pygame.Surface) -> None:
    screen_rect = screen.get_rect()
    bullets = list(world.get_components(CTagBullet, CTransform, CSurface))
    bullets.extend(world.get_components(CTagEnemyBullet, CTransform, CSurface))
    for entity, (_, transform, surface) in bullets:
        rect = pygame.Rect(round(transform.pos.x), round(transform.pos.y), *surface.size)
        if not screen_rect.colliderect(rect):
            world.delete_entity(entity)
