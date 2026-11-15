import esper
import pygame
from src.ecs.components.c_hunter import CHunter
from src.ecs.components.c_tag_player import CTagPlayer
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.c_animation import CAnimation
from src.ecs.components.c_surface import CSurface
from src.services import ServiceLocator


def system_hunter(world: esper.World, dt: float):
    del dt
    player_data = next(iter(world.get_components(CTagPlayer, CTransform, CSurface)), None)
    if not player_data:
        return
    _, (_, player_transform, player_surface) = player_data
    player_center = player_transform.pos + pygame.Vector2(player_surface.size) / 2
    for _, (hunter, transform, velocity, surface) in world.get_components(
        CHunter, CTransform, CVelocity, CSurface
    ):
        hunter_center = transform.pos + pygame.Vector2(surface.size) / 2
        offset = hunter_center - (hunter.origin + pygame.Vector2(surface.size) / 2)
        player_distance = hunter_center.distance_to(player_center)
        if hunter.paused_until_player_moves_away:
            velocity.vel.update(0, 0)
            if player_distance > hunter.aggro_range:
                hunter.paused_until_player_moves_away = False
            else:
                continue
        if offset.length() > hunter.leash_range:
            hunter.returning = True
        if hunter.returning:
            target = hunter.origin
            if hunter_center.distance_to(target + pygame.Vector2(surface.size) / 2) < max(2, hunter.return_speed * .02):
                transform.pos.update(target)
                hunter.returning = False
                velocity.vel.update(0, 0)
                continue
        elif hunter_center.distance_to(player_center) <= hunter.aggro_range:
            target = player_center
            if not hunter.was_chasing and hunter.chase_sound:
                ServiceLocator.sounds.load(hunter.chase_sound).play()
            hunter.was_chasing = True
        else:
            velocity.vel.update(0, 0)
            hunter.was_chasing = False
            continue
        target_center = pygame.Vector2(target) + pygame.Vector2(surface.size) / 2 if hunter.returning else pygame.Vector2(target)
        direction = target_center - hunter_center
        if direction.length_squared():
            velocity.vel = direction.normalize() * (hunter.return_speed if hunter.returning else hunter.speed)


def system_moving_animation(world: esper.World):
    for _, (anim, velocity) in world.get_components(CAnimation, CVelocity):
        if "MOVE" in anim.animations and "IDLE" in anim.animations:
            anim.play("MOVE" if velocity.vel.length_squared() else "IDLE")
