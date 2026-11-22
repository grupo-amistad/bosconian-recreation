
import esper
import pygame

from src.create.prefab_creator import create_bullet, create_player
from src.ecs.components.c_bullet_lifetime import CBulletLifetime
from src.ecs.components.c_combat import CScore
from src.ecs.components.c_player import CPlayer
from src.ecs.components.c_player_intent import CPlayerIntent
from src.ecs.components.c_player_bullet import CPlayerBullet
from src.ecs.components.c_player_life import CPlayerLife
from src.ecs.components.c_player_movement import CPlayerMovement
from src.ecs.components.c_player_special import CPlayerSpecial
from src.ecs.components.c_player_weapon import CPlayerWeapon
from src.ecs.components.c_sprite_rotation import CSpriteRotation
from src.ecs.components.c_state import CState
from src.ecs.components.c_surface import CSurface
from src.player.player_config import PlayerConfig, ShotConfig


def create_player_entity(
    world: esper.World,
    config: PlayerConfig,
    spawn_position: pygame.Vector2,
    lives: int | None = None,
    score: int = 0,
) -> int:
    size = pygame.Vector2(config.size)
    entity = create_player(
        world,
        size,
        pygame.Vector2(spawn_position),
        pygame.Vector2(),
        pygame.Color(*config.color),
        image=config.image,
        hitbox_size=config.hitbox_size,
        hitbox_offset=config.hitbox_offset,
    )
    player = CPlayer(
        config.movement.max_speed,
        max_bullets=config.shot.max_bullets,
        spawn_position=pygame.Vector2(spawn_position),
        lives=config.life.initial_lives if lives is None else lives,
        size=size,
    )
    player.score = score
    world.add_component(entity, player)
    world.add_component(entity, CScore(points=score))
    world.add_component(entity, CPlayerIntent())
    world.add_component(entity, CPlayerMovement(config.movement))
    world.add_component(entity, CPlayerWeapon(config.shot))
    world.add_component(entity, CPlayerSpecial(config.special))
    world.add_component(entity, CPlayerLife(config.life))
    world.add_component(entity, CState("ALIVE"))
    surface = world.component_for_entity(entity, CSurface)
    world.add_component(
        entity, CSpriteRotation(surface.surf, config.movement.rotation_step)
    )
    return entity


def create_player_bullet(
    world: esper.World,
    owner: int,
    ship_center: pygame.Vector2,
    direction: pygame.Vector2,
    ship_velocity: pygame.Vector2,
    config: ShotConfig,
    kind: str = "normal",
) -> int:
    direction = pygame.Vector2(direction).normalize()
    size = pygame.Vector2(config.size)
    velocity = direction * config.speed
    if config.inherit_ship_velocity:
        velocity += ship_velocity
    position = ship_center + direction * config.muzzle_offset - size / 2
    entity = create_bullet(
        world,
        size,
        position,
        velocity,
        pygame.Color(*config.color),
        image=config.image,
        hitbox_size=config.hitbox_size,
        hitbox_offset=config.hitbox_offset,
    )
    world.add_component(entity, CPlayerBullet(owner, kind))
    lifetime = config.range / config.speed if config.speed > 0 else 0.0
    world.add_component(entity, CBulletLifetime(lifetime))
    return entity