from dataclasses import replace

import esper
import pygame

from src.ecs.components.c_player import CPlayer
from src.ecs.components.c_player_bullet import CPlayerBullet
from src.ecs.components.c_player_intent import CPlayerIntent
from src.ecs.components.c_player_special import CPlayerSpecial
from src.ecs.components.c_player_weapon import CPlayerWeapon
from src.ecs.components.c_state import CState
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.systems.s_player_movement import CONTROLLABLE_STATES, heading_to_vector
from src.player.player_factory import create_player_bullet
from src.services import ServiceLocator


def count_player_bullets(world: esper.World, owner: int, kind: str = "normal") -> int:
    return sum(
        1
        for entity, (bullet,) in world.get_components(CPlayerBullet)
        if bullet.owner == owner
        and bullet.kind == kind
        and world.entity_exists(entity)
    )


def ship_center(player: CPlayer, transform: CTransform) -> pygame.Vector2:
    return transform.pos + player.size / 2


def play_sound(path: str | None) -> None:
    if path:
        ServiceLocator.sounds.load(path).play()


def system_player_shooting(world: esper.World, delta_time: float) -> None:
    for entity, (player, intent, weapon, transform, velocity, state) in list(
        world.get_components(
            CPlayer, CPlayerIntent, CPlayerWeapon, CTransform, CVelocity, CState,
        )
    ):
        weapon.cooldown_remaining = max(0.0, weapon.cooldown_remaining - delta_time)
        if state.name not in CONTROLLABLE_STATES:
            continue
        config = weapon.config
        wants_to_fire = intent.fire or (config.autofire and intent.fire_held)
        if not wants_to_fire or weapon.cooldown_remaining > 0:
            continue
        if count_player_bullets(world, entity) + 2 > config.max_bullets:
            continue

        forward = heading_to_vector(transform.angle)
        center = ship_center(player, transform)
        for direction in (forward, -forward):
            create_player_bullet(
                world, entity, center, direction, velocity.vel, config
            )
        weapon.cooldown_remaining = config.cooldown
        play_sound(config.sound)


def system_player_special(world: esper.World, delta_time: float) -> None:
    for entity, (player, intent, special, weapon, transform, velocity, state) in list(
        world.get_components(
            CPlayer, CPlayerIntent, CPlayerSpecial, CPlayerWeapon,
            CTransform, CVelocity, CState,
        )
    ):
        special.cooldown_remaining = max(0.0, special.cooldown_remaining - delta_time)
        if (
            state.name not in CONTROLLABLE_STATES
            or not intent.special
            or not special.config.enabled
            or special.uses_left <= 0
            or special.cooldown_remaining > 0
        ):
            continue
        config = special.config
        shot = replace(
            weapon.config,
            speed=config.speed or weapon.config.speed,
            range=config.range or weapon.config.range,
        )
        center = ship_center(player, transform)
        front_count = max(1, config.bullet_count)
        middle = (front_count - 1) / 2
        for index in range(front_count):
            heading = transform.angle + (index - middle) * config.spread_degrees
            create_player_bullet(
                world, entity, center, heading_to_vector(heading),
                velocity.vel, shot, kind="special",
            )
        # Cuarta bala trasera según especificación de Bosconian (3 al frente + 1 atrás)
        rear_direction = -heading_to_vector(transform.angle)
        create_player_bullet(
            world, entity, center, rear_direction,
            velocity.vel, shot, kind="special",
        )
        special.uses_left -= 1
        special.cooldown_remaining = config.cooldown
        play_sound(config.sound)


def system_player_bullet_bounds(world: esper.World, camera=None) -> None:
    if camera is None:
        return
    for entity, (bullet, transform) in list(
        world.get_components(CPlayerBullet, CTransform)
    ):
        weapon = world.try_component(bullet.owner, CPlayerWeapon)
        margin = weapon.config.offscreen_margin if weapon else 8.0
        screen = camera.world_to_screen(transform.pos)
        if (
            screen.x < -margin
            or screen.y < -margin
            or screen.x > camera.viewport_size.x + margin
            or screen.y > camera.viewport_size.y + margin
        ) and world.entity_exists(entity):
            world.delete_entity(entity)