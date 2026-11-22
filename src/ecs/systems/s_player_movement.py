import math

import esper
import pygame

from src.ecs.components.c_player import CPlayer
from src.ecs.components.c_player_intent import CPlayerIntent
from src.ecs.components.c_player_movement import CPlayerMovement
from src.ecs.components.c_state import CState
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity

CONTROLLABLE_STATES = {"ALIVE", "RESPAWNING"}


def heading_to_vector(heading: float) -> pygame.Vector2:
    radians = math.radians(heading)
    return pygame.Vector2(math.sin(radians), -math.cos(radians))


def vector_to_heading(direction: pygame.Vector2) -> float:
    return math.degrees(math.atan2(direction.x, -direction.y)) % 360


def snap_heading(heading: float, step: float) -> float:
    if step <= 0:
        return heading % 360
    return (round(heading / step) * step) % 360


def _approach(value: float, target: float, max_delta: float) -> float:
    if value < target:
        return min(target, value + max_delta)
    return max(target, value - max_delta)


def _turn(heading: float, target: float, max_turn: float) -> float:
    difference = (target - heading + 180) % 360 - 180
    if max_turn <= 0 or abs(difference) <= max_turn:
        return target % 360
    return (heading + math.copysign(max_turn, difference)) % 360


def system_player_movement(world: esper.World, delta_time: float) -> None:
   
    for _, (player, intent, movement, transform, velocity, state) in world.get_components(
        CPlayer, CPlayerIntent, CPlayerMovement, CTransform, CVelocity, CState
    ):
        if state.name not in CONTROLLABLE_STATES:
            continue
        config = movement.config
        wanted = pygame.Vector2(intent.move)
        if not config.allow_diagonals and wanted.x and wanted.y:
            wanted.y = 0

        if wanted.length_squared():
            target = vector_to_heading(wanted)
            movement.heading = _turn(
                movement.heading, target, config.turn_speed * delta_time
            )
            movement.speed = _approach(
                movement.speed, config.max_speed, config.acceleration * delta_time
            )
        else:
            rate = (
                config.deceleration
                if movement.speed > config.cruise_speed
                else config.acceleration
            )
            movement.speed = _approach(
                movement.speed, config.cruise_speed, rate * delta_time
            )

        direction = heading_to_vector(movement.heading)
        velocity.vel = direction * movement.speed
        transform.angle = snap_heading(movement.heading, config.rotation_step)
        player.facing.update(heading_to_vector(transform.angle))
        player.facing_angle = transform.angle