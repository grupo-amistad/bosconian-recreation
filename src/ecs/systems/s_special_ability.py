import esper
import pygame

from src.ecs.components.c_special_ability import CSpecialAbility
from src.ecs.components.c_input_command import CInputCommand
from src.ecs.components.c_tag_enemy import CTagEnemy
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_tag_player import CTagPlayer
from src.ecs.components.c_surface import CSurface


def system_special_ability(world: esper.World, dt: float) -> None:
    command = next(
        (command for _, (command,) in world.get_components(CInputCommand)
         if command.action == "PLAYER_SPECIAL"),
        None,
    )
    player_data = next(iter(world.get_components(CTagPlayer, CTransform)), None)
    ability_data = next(iter(world.get_components(CSpecialAbility)), None)
    if not command or not player_data or not ability_data:
        return
    _, (_, player_transform) = player_data
    _, (ability,) = ability_data
    ability.cooldown_remaining = max(0.0, ability.cooldown_remaining - dt)
    ability.active_for = max(0.0, ability.active_for - dt)
    if command.pressed and ability.cooldown_remaining == 0:
        ability.active_for = ability.duration
        ability.cooldown_remaining = ability.cooldown
    if ability.active_for <= 0:
        return
    for entity, (_, transform, surface) in list(world.get_components(CTagEnemy, CTransform, CSurface)):
        enemy_center = transform.pos + pygame.Vector2(surface.size) / 2
        player_center = player_transform.pos
        if enemy_center.distance_to(player_center) <= ability.radius:
            world.delete_entity(entity)
