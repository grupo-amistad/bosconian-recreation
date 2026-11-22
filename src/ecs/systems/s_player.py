import esper
import pygame

from src.create.prefab_creator import create_bullet
from src.ecs.components.c_bullet_lifetime import CBulletLifetime
from src.ecs.components.c_input_command import CInputCommand
from src.ecs.components.c_player import CPlayer
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_tag_bullet import CTagBullet
from src.ecs.components.c_tag_player import CTagPlayer
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.services import ServiceLocator


def system_player_input(world: esper.World, delta_time: float, camera=None, world_size=None) -> None:
    commands = {
        command.action: command
        for _, (command,) in world.get_components(CInputCommand)
    }

    for _, (player, transform, velocity) in world.get_components(
        CPlayer, CTransform, CVelocity
    ):
        player.fire_cooldown_remaining = max(
            0.0, player.fire_cooldown_remaining - delta_time
        )
        for action, direction, angle in (
            ("PLAYER_UP", (0, -1), 0),
            ("PLAYER_RIGHT", (1, 0), -90),
            ("PLAYER_DOWN", (0, 1), 180),
            ("PLAYER_LEFT", (-1, 0), 90),
        ):
            if commands[action].pressed:
                player.facing.update(direction)
                player.facing_angle = angle
                surface = next(
                    (surf for _, (_, surf) in world.get_components(CTagPlayer, CSurface)),
                    None,
                )
                if surface is not None:
                    base_image = getattr(surface, "base_image", surface.surf)
                    surface.surf = pygame.transform.rotate(base_image, angle)
                    surface.area = surface.surf.get_rect()

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
        if fire_command.pressed and player.fire_cooldown_remaining <= 0:
            if _fire_bullet(world, player, transform, camera, world_size):
                player.fire_cooldown_remaining = 0.12


def _fire_bullet(
    world: esper.World,
    player: CPlayer,
    transform: CTransform,
    camera=None,
    world_size=None,
) -> bool:
    mouse_screen = pygame.Vector2(pygame.mouse.get_pos())
    if camera is not None and mouse_screen.x >= camera.viewport_size.x:
        return False
    bullet_count = len(list(world.get_components(CTagBullet)))
    if bullet_count >= player.max_bullets:
        return False

    mouse_position = mouse_screen
    if camera is not None:
        mouse_position = camera.screen_to_world(mouse_position)
    center = transform.pos + pygame.Vector2(*player_size(world)) / 2
    direction = mouse_position - center
    if world_size is not None:
        direction.x = (direction.x + world_size.x / 2) % world_size.x - world_size.x / 2
        direction.y = (direction.y + world_size.y / 2) % world_size.y - world_size.y / 2
    if direction.length_squared() == 0:
        return False
    direction.normalize_ip()

    config = player.bullet_config
    size_data = config.get("size", {"x": 18, "y": 18})
    size = pygame.Vector2(size_data["x"], size_data["y"])
    image = config.get("image")
    if image:
        image = image
    bullet_entity = create_bullet(
        world,
        size,
        center - size / 2,
        direction * config["velocity"],
        pygame.Color(*[config.get("color", {"r":255,"g":255,"b":255})[k] for k in ("r", "g", "b")]), image=image,
        hitbox_size=config.get("hitbox_size"),
        hitbox_offset=config.get("hitbox_offset"),
    )
    world.add_component(
        bullet_entity,
        CBulletLifetime(player.bullet_config.get("lifetime", 1.4)),
    )
    sound_path = config.get("sound")
    if sound_path:
        ServiceLocator.sounds.load(sound_path).play()
    return True


def player_size(world: esper.World) -> tuple[float, float]:
    for _, (_, surface) in world.get_components(CTagPlayer, CSurface):
        return surface.size
    return 0, 0
