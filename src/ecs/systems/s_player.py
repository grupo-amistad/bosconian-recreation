import esper
import pygame

from src.create.prefab_creator import create_bullet
from src.ecs.components.c_input_command import CInputCommand
from src.ecs.components.c_player import CPlayer
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_tag_bullet import CTagBullet
from src.ecs.components.c_tag_player import CTagPlayer
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
import os
from src.services import ServiceLocator


def system_player_input(world: esper.World, delta_time: float) -> None:
    commands = {
        command.action: command
        for _, (command,) in world.get_components(CInputCommand)
    }

    for _, (player, transform, velocity) in world.get_components(
        CPlayer, CTransform, CVelocity
    ):
        velocity.vel.update(0, 0)
        if commands["PLAYER_LEFT"].active:
            velocity.vel.x -= player.input_velocity
        if commands["PLAYER_RIGHT"].active:
            velocity.vel.x += player.input_velocity
        if commands["PLAYER_UP"].active:
            velocity.vel.y -= player.input_velocity
        if commands["PLAYER_DOWN"].active:
            velocity.vel.y += player.input_velocity
        if velocity.vel.length_squared() > player.input_velocity ** 2:
            velocity.vel.scale_to_length(player.input_velocity)
        player.sound_elapsed = max(0.0, player.sound_elapsed - delta_time)
        if velocity.vel.length_squared() and player.sound_elapsed == 0 and getattr(player, "move_sound", None):
            player.move_sound.play()
            player.sound_elapsed = 0.12

        fire_command = commands["PLAYER_FIRE"]
        if fire_command.pressed:
            _fire_bullet(world, player, transform)


def _fire_bullet(
    world: esper.World,
    player: CPlayer,
    transform: CTransform,
) -> None:
    bullet_count = len(list(world.get_components(CTagBullet)))
    if bullet_count >= player.max_bullets:
        return

    mouse_position = pygame.Vector2(pygame.mouse.get_pos())
    direction = mouse_position - (transform.pos + pygame.Vector2(*player_size(world)) / 2)
    if direction.length_squared() == 0:
        return
    direction.normalize_ip()

    config = player.bullet_config
    size_data = config.get("size", {"x": 18, "y": 18})
    size = pygame.Vector2(size_data["x"], size_data["y"])
    center = transform.pos + pygame.Vector2(*player_size(world)) / 2
    image = config.get("image")
    if image:
        image = image
    create_bullet(
        world,
        size,
        center - size / 2,
        direction * config["velocity"],
        pygame.Color(*[config.get("color", {"r":255,"g":255,"b":255})[k] for k in ("r", "g", "b")]), image=image,
    )
    sound_path = config.get("sound")
    if sound_path:
        ServiceLocator.sounds.load(sound_path).play()


def player_size(world: esper.World) -> tuple[float, float]:
    for _, (_, surface) in world.get_components(CTagPlayer, CSurface):
        return surface.size
    return 0, 0
