import random

import esper
import pygame

from src.ecs.components.c_combat import CTagEnemyBullet
from src.ecs.components.c_hitbox import CHitBox
from src.ecs.components.c_hunter import CHunter
from src.ecs.components.c_player import CPlayer
from src.ecs.components.c_player_bullet import CPlayerBullet
from src.ecs.components.c_player_life import CPlayerLife
from src.ecs.components.c_player_movement import CPlayerMovement
from src.ecs.components.c_state import CState
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.systems.s_collisions import _explode
from src.services import ServiceLocator

ALIVE = "ALIVE"
DYING = "DYING"
RESPAWNING = "RESPAWNING"
GAME_OVER = "GAME_OVER"

EXPLOSION_KEY = "player"


def player_explosion_config(explosion_config: dict | None) -> dict:
    
    config = explosion_config or {}
    block = config.get(EXPLOSION_KEY)
    return block if isinstance(block, dict) else config


def request_player_death(
    world: esper.World,
    player_id: int,
    explosion_config: dict | None = None,
    position=None,
) -> bool:
    
    player = world.try_component(player_id, CPlayer)
    if player is None:
        return False
    state = world.try_component(player_id, CState)
    life = world.try_component(player_id, CPlayerLife)
    transform = world.try_component(player_id, CTransform)
    if state is None or life is None or transform is None:
        _instant_death(world, player_id, player, transform, explosion_config, position)
        return True
    if state.name != ALIVE:
        return False

    player.lives = max(0, player.lives - 1)
    _set_state(state, DYING)
    life.explosions_spawned = 0
    life.death_position = transform.pos + player.size / 2
    _stop(world, player_id)
    _set_visible(world, player_id, life, False)
    _set_collidable(world, player_id, life, False)
    if life.config.death_sound:
        ServiceLocator.sounds.load(life.config.death_sound).play()
    return True


def system_player_life(
    world: esper.World,
    delta_time: float,
    explosion_config: dict | None = None,
) -> None:
    # The death sound plays once; the chained explosions stay silent.
    quiet_explosion = dict(player_explosion_config(explosion_config), sound=None)
    for entity, (player, life, state, transform) in list(
        world.get_components(CPlayer, CPlayerLife, CState, CTransform)
    ):
        state.elapsed += delta_time
        config = life.config
        if state.name == DYING:
            while (
                life.explosions_spawned < config.explosion_count
                and state.elapsed >= life.explosions_spawned * config.explosion_interval
            ):
                spread = config.explosion_spread
                offset = pygame.Vector2(
                    random.uniform(-spread, spread), random.uniform(-spread, spread)
                )
                _explode(world, life.death_position + offset, quiet_explosion)
                life.explosions_spawned += 1
            if state.elapsed >= config.death_duration:
                if player.lives <= 0:
                    player.dead = True
                    _set_state(state, GAME_OVER)
                else:
                    _respawn(world, entity, player, life, state, transform)
        elif state.name == RESPAWNING:
            life.blink_elapsed += delta_time
            if state.elapsed >= config.invulnerability:
                _set_visible(world, entity, life, True)
                _set_collidable(world, entity, life, True)
                _set_state(state, ALIVE)
            elif config.blink_interval > 0:
                blink_on = int(life.blink_elapsed / config.blink_interval) % 2 == 0
                _set_visible(world, entity, life, blink_on)


def _respawn(world, entity, player, life, state, transform) -> None:
    if player.spawn_position is not None:
        transform.pos.update(player.spawn_position)
    transform.angle = 0.0
    movement = world.try_component(entity, CPlayerMovement)
    if movement:
        movement.heading = 0.0
        movement.speed = 0.0
    _stop(world, entity)
    _clear_projectiles(world, entity)
    _reset_hunters(world, entity)
    life.blink_elapsed = 0.0
    _set_visible(world, entity, life, True)
    if life.config.invulnerability > 0:
        _set_state(state, RESPAWNING)
    else:
        _set_collidable(world, entity, life, True)
        _set_state(state, ALIVE)


def _instant_death(world, player_id, player, transform, explosion_config, position):
    _explode(
        world,
        pygame.Vector2(position or (0, 0)),
        player_explosion_config(explosion_config),
    )
    player.lives = max(0, player.lives - 1)
    if player.lives == 0:
        player.dead = True
    if transform is not None and player.spawn_position is not None:
        transform.pos.update(player.spawn_position)
    _stop(world, player_id)
    _reset_hunters(world, player_id)


def _set_state(state: CState, name: str) -> None:
    state.name = name
    state.elapsed = 0.0


def _stop(world, entity) -> None:
    velocity = world.try_component(entity, CVelocity)
    if velocity:
        velocity.vel.update(0, 0)


def _set_visible(world, entity, life: CPlayerLife, visible: bool) -> None:
    surface = world.try_component(entity, CSurface)
    if visible and surface is None and life.hidden_surface is not None:
        world.add_component(entity, life.hidden_surface)
        life.hidden_surface = None
    elif not visible and surface is not None:
        life.hidden_surface = world.remove_component(entity, CSurface)


def _set_collidable(world, entity, life: CPlayerLife, collidable: bool) -> None:
    hitbox = world.try_component(entity, CHitBox)
    if collidable and hitbox is None and life.hidden_hitbox is not None:
        world.add_component(entity, life.hidden_hitbox)
        life.hidden_hitbox = None
    elif not collidable and hitbox is not None:
        life.hidden_hitbox = world.remove_component(entity, CHitBox)


def _clear_projectiles(world, player_id) -> None:
    for entity, (bullet,) in list(world.get_components(CPlayerBullet)):
        if bullet.owner == player_id and world.entity_exists(entity):
            world.delete_entity(entity)
    for entity, _ in list(world.get_component(CTagEnemyBullet)):
        if world.entity_exists(entity):
            world.delete_entity(entity)


def _reset_hunters(world, player_id) -> None:
    for other_id, (hunter, transform, velocity) in list(
        world.get_components(CHunter, CTransform, CVelocity)
    ):
        if other_id != player_id:
            transform.pos.update(hunter.origin)
            velocity.vel.update(0, 0)
            hunter.returning = False
            hunter.paused_until_player_moves_away = True