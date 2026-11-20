import esper
import pygame
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_hitbox import CHitBox
from src.ecs.components.c_tag_bullet import CTagBullet
from src.ecs.components.c_tag_enemy import CTagEnemy
from src.ecs.components.c_tag_player import CTagPlayer
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_tag_explosion import CTagExplosion
from src.ecs.components.c_animation import Animation, CAnimation
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.c_hunter import CHunter
from src.ecs.components.c_player import CPlayer
from src.ecs.components.c_explosion_lifetime import CExplosionLifetime
from src.services import ServiceLocator
from src.ecs.components.c_world_entity import CWorldEntity


def _rect(transform, hitbox):
    return hitbox.rect_at(transform.pos)


def _explode(world, position, config=None):
    config = config or {}
    image = config.get("image")
    if image:
        from pathlib import Path
        image = image
    surf = CSurface(image=image, size=pygame.Vector2(8, 8), color=pygame.Color("orange"))
    animation_config = config.get("animations", {})
    frames = animation_config.get("number_frames", config.get("frames", 1))
    animation_list = animation_config.get("list", [])
    animation_data = animation_list[0] if animation_list else config.get(
        "animation", {"name": "EXPLODE", "start": 0, "end": 0, "framerate": 8}
    )
    # Never slice a sprite sheet into more frames than its width supports.
    if image:
        # Make the impact readable at the game's current display scale.
        surf.surf = pygame.transform.scale_by(surf.surf, 2)
        frames = max(1, min(frames, surf.surf.get_width()))
    if image:
        frame_width = surf.surf.get_width() // frames
        surf.area = pygame.Rect(0, 0, frame_width, surf.surf.get_height())
    entity = world.create_entity()
    world.add_component(entity, surf)
    world.add_component(entity, CWorldEntity())
    frame_width = surf.surf.get_width() // frames
    world.add_component(entity, CTransform(pygame.Vector2(position) - pygame.Vector2(frame_width, surf.surf.get_height()) / 2))
    world.add_component(entity, CTagExplosion())
    # The lifetime timer is the final cleanup guard; the animation itself stops
    # on its last frame and cannot loop forever.
    anim = CAnimation(
        frames,
        [Animation(animation_data["name"], animation_data["start"], animation_data["end"], animation_data["framerate"])],
        animation_data["name"],
        True,
        False,
    )
    world.add_component(entity, anim)
    world.add_component(entity, CExplosionLifetime(
        (animation_data["end"] - animation_data["start"] + 1) / animation_data["framerate"]
    ))
    sound_path = config.get("sound")
    if sound_path:
        ServiceLocator.sounds.load(sound_path).play()


def _overlaps_wrapped(first, second, world_size):
    if world_size is None:
        return first.colliderect(second)
    for dx in (-world_size.x, 0, world_size.x):
        for dy in (-world_size.y, 0, world_size.y):
            if first.colliderect(second.move(dx, dy)):
                return True
    return False


def system_bullet_enemy_collision(world: esper.World, explosion_config=None, world_size=None) -> None:
    bullets = list(world.get_components(CTagBullet, CTransform, CHitBox))
    enemies = list(world.get_components(CTagEnemy, CTransform, CHitBox))
    for bullet_id, (_, bt, bh) in bullets:
        for enemy_id, (_, et, eh) in enemies:
            if not world.entity_exists(bullet_id) or not world.entity_exists(enemy_id):
                continue
            enemy_rect = _rect(et, eh)
            if _overlaps_wrapped(_rect(bt, bh), enemy_rect, world_size):
                _explode(world, pygame.Vector2(enemy_rect.center), explosion_config)
                world.delete_entity(bullet_id)
                world.delete_entity(enemy_id)
                break


def system_player_enemy_collision(world: esper.World, explosion_config=None, screen_size=None, world_size=None) -> None:
    players = list(world.get_components(CTagPlayer, CTransform, CHitBox, CPlayer))
    enemies = list(world.get_components(CTagEnemy, CTransform, CHitBox))
    for player_id, (_, pt, ph, player) in players:
        for enemy_id, (_, et, eh) in enemies:
            enemy_rect = _rect(et, eh)
            if world.entity_exists(player_id) and world.entity_exists(enemy_id) and _overlaps_wrapped(_rect(pt, ph), enemy_rect, world_size):
                _explode(world, pygame.Vector2(enemy_rect.center), explosion_config)
                world.delete_entity(enemy_id)
                # Put the other Hunters back at their spawn points and pause them
                # until the player leaves their aggro radius, preventing an
                # immediate chain of collisions after the respawn.
                for other_id, (hunter, hunter_transform, hunter_velocity) in list(
                    world.get_components(CHunter, CTransform, CVelocity)
                ):
                    if other_id != enemy_id:
                        hunter_transform.pos.update(hunter.origin)
                        hunter_velocity.vel.update(0, 0)
                        hunter.returning = False
                        hunter.paused_until_player_moves_away = True
                player.lives = max(0, player.lives - 1)
                if player.lives == 0:
                    player.dead = True
                pt.pos.update(player.spawn_position)
                velocity = world.try_component(player_id, CVelocity)
                if velocity:
                    velocity.vel.update(0, 0)
                break
