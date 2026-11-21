import esper
import math
import pygame
import random
from src.ecs.components.c_combat import (
    CBaseState,
    CCombatStats,
    CEnemyBehavior,
    CObstacleState,
    CTagBase,
    CTagBaseCore,
    CTagEnemyBullet,
    CTagObstacle,
    CTagTurret,
    CTurretState,
)
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.c_state import CState
from src.ecs.components.c_hitbox import CHitBox
from src.ecs.components.c_world_entity import CWorldEntity
from src.ecs.components.c_tag_bullet import CTagBullet
from src.ecs.components.c_tag_enemy import CTagEnemy
from src.ecs.components.c_tag_player import CTagPlayer
from src.ecs.components.c_animation import Animation, CAnimation
from src.ecs.components.c_hunter import CHunter


def animations_from_config(config):
    data = config.get("animations", [])
    if isinstance(data, dict):
        data = data.get("list", [])
    return [Animation(a["name"], a["start"], a["end"], a["framerate"])
            for a in data]


def animation_frame_count(config):
    data = config.get("animations", {})
    return data.get("number_frames", config.get("frames", 1)) if isinstance(data, dict) else config.get("frames", 1)


def create_entity(world, pos, vel, tag, image=None, size=None, color=None,
                  area=None, animations=None, frames=1, extra=None,
                  hitbox_size=None, hitbox_offset=None):
    entity = world.create_entity()
    surface = CSurface(image=image, area=area, size=size, color=color, frames=frames)
    if animations and frames > 1:
        frame_width = surface.surf.get_width() // frames
        surface.area = pygame.Rect(0, 0, frame_width, surface.surf.get_height())
    world.add_component(entity, surface)
    world.add_component(entity, CTransform(pygame.Vector2(pos)))
    world.add_component(entity, CVelocity(pygame.Vector2(vel)))
    world.add_component(entity, CWorldEntity())
    collision_size = (
        _vector(hitbox_size)
        if hitbox_size is not None
        else pygame.Vector2(surface.size)
    )
    collision_offset = (
        _vector(hitbox_offset)
        if hitbox_offset is not None
        else pygame.Vector2()
    )
    world.add_component(entity, CHitBox(collision_size, collision_offset))
    if tag:
        world.add_component(entity, tag() if isinstance(tag, type) else tag)
    if animations:
        world.add_component(entity, CAnimation(frames, animations))
    if extra:
        world.add_component(entity, extra)
    return entity


def create_square(world, size, pos, vel, col, **kwargs):
    return create_entity(world, pos, vel, CTagEnemy, size=size, color=col, **kwargs)


def create_player(world, size, pos, vel, col, **kwargs):
    return create_entity(world, pos, vel, CTagPlayer, size=size, color=col, **kwargs)


def create_bullet(world, size, pos, vel, col, **kwargs):
    return create_entity(world, pos, vel, CTagBullet, size=size, color=col, **kwargs)


def create_enemy(world, config, pos, kind):
    size_data = config.get("size", {"x": 16, "y": 16})
    size = pygame.Vector2(size_data["x"], size_data["y"])
    is_hunter = kind == "Hunter" or config.get("type") == "hunter"
    speed = random.uniform(
        config.get("velocity_min", config.get("speed", config.get("velocity_chase", 0))),
        config.get("velocity_max", config.get("speed", config.get("velocity_chase", 0))),
    )
    angle = random.uniform(0, math.tau)
    behavior_mode = config.get("behavior", "patrol")
    velocity = (
        pygame.Vector2()
        if is_hunter
        else pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
    )
    entity = create_entity(
        world,
        pos,
        velocity,
        CTagEnemy(kind),
        image=config.get("image"),
        size=size,
        color=_color(config.get("color"), (100, 100, 255)),
        animations=animations_from_config(config),
        frames=animation_frame_count(config),
        hitbox_size=config.get("hitbox_size"),
        hitbox_offset=config.get("hitbox_offset"),
        extra=CCombatStats(
            config.get("health", 1), config.get("score", 100), kind
        ),
    )
    if is_hunter:
        world.add_component(
            entity,
            CHunter(
                pygame.Vector2(pos),
                config.get("aggro_distance", config.get("distance_start_chase", 180)),
                config.get("return_distance", config.get("distance_start_return", 260)),
                config.get("hunt_speed", config.get("velocity_chase", 70)),
                config.get("velocity_return", config.get("velocity_chase", 70)),
                config.get("sound_chase"),
            ),
        )
        return entity
    world.add_component(
        entity,
        CEnemyBehavior(
            behavior_mode,
            speed,
            config.get("turn_rate", 180),
            config.get("fire_interval", 0),
            0.0,
            config.get("bullet_speed", 55),
            (
                config.get("bullet_size", {}).get("x", 4),
                config.get("bullet_size", {}).get("y", 4),
            ),
            _as_tuple(config.get("bullet_hitbox_size")),
            _as_tuple(config.get("bullet_hitbox_offset")),
        ),
    )
    world.add_component(entity, CState(behavior_mode))
    return entity


def create_enemy_bullet(
    world, pos, velocity, size=None, hitbox_size=None, hitbox_offset=None
):
    size = pygame.Vector2(size or (4, 4))
    return create_entity(
        world,
        pos,
        velocity,
        CTagEnemyBullet,
        size=size,
        color=pygame.Color(255, 80, 80),
        hitbox_size=hitbox_size if hitbox_size is not None else size,
        hitbox_offset=hitbox_offset,
    )


def create_base(world, config, pos, level, enemy_configs):
    size_data = config.get("size", {"x": 28, "y": 28})
    size = pygame.Vector2(size_data["x"], size_data["y"])
    base_id = create_entity(
        world,
        pos,
        pygame.Vector2(),
        CTagBase,
        image=config.get("image"),
        size=size,
        color=_color(config.get("color"), (180, 180, 80)),
        hitbox_size=config.get("core_hitbox_size", size),
        hitbox_offset=config.get("core_hitbox_offset"),
        extra=CCombatStats(
            config.get("health", 1), config.get("score", 1000), "base"
        ),
    )
    state = CBaseState(
        level,
        config.get("core_open_duration", 2.0),
        config.get("core_closed_duration", 5.0),
        config.get("e_spawn_level", 4),
        config.get("e_spawn_interval", 12.0),
        enemy_configs,
        config.get("rotation_speed", 0),
        config.get("bullet_speed", 50),
        bullet_hitbox_size=(
            _as_tuple(config.get("bullet_hitbox_size")) or (4, 4)
        ),
        bullet_hitbox_offset=_as_tuple(
            config.get("bullet_hitbox_offset")
        ),
    )
    world.add_component(base_id, state)
    world.add_component(base_id, CState("CORE_CLOSED"))

    center = pygame.Vector2(pos) + size / 2
    core_size = _vector(config.get("core_hitbox_size", size))
    core_offset = _vector(config.get("core_hitbox_offset", (0, 0)))
    core_open_color = _color(
        config.get("core_open_color"), (255, 240, 120)
    )
    core_closed_color = _color(
        config.get("core_closed_color"), (70, 90, 50)
    )
    state.core_open_color = tuple(core_open_color)[:3]
    state.core_closed_color = tuple(core_closed_color)[:3]
    state.core_entity = create_entity(
        world,
        pygame.Vector2(pos) + core_offset,
        pygame.Vector2(),
        CTagBaseCore,
        size=core_size,
        color=core_closed_color,
    )
    turret_count = config.get("turret_count", 6)
    radius = config.get("turret_radius", max(size) / 2 + 5)
    for index in range(turret_count):
        angle = config.get("orientation", 0) + index * 360 / turret_count
        radians = math.radians(angle)
        turret_size = pygame.Vector2(8, 8)
        turret_id = create_entity(
            world,
            center + pygame.Vector2(math.cos(radians), math.sin(radians)) * radius - turret_size / 2,
            pygame.Vector2(),
            CTagTurret,
            image=config.get("turret_image"),
            size=turret_size,
            color=_color(config.get("turret_color"), (255, 220, 80)),
            hitbox_size=config.get("turret_hitbox_size"),
            hitbox_offset=config.get("turret_hitbox_offset"),
            extra=CCombatStats(
                config.get("turret_health", 1),
                config.get("turret_score", 100),
                "turret",
            ),
        )
        world.add_component(
            turret_id,
            CTurretState(
                base_id,
                radius,
                angle,
                config.get("turret_fire_interval", 2.5),
            ),
        )
        state.turret_ids.add(turret_id)
    return base_id


def create_obstacle(world, config, pos):
    size_data = config.get("size", {"x": 16, "y": 16})
    size = pygame.Vector2(size_data["x"], size_data["y"])
    kind = config.get("type", "rock")
    destructible = config.get("destructible", kind == "mine")
    velocity_data = config.get("velocity", {"x": 0, "y": 0})
    entity = create_entity(
        world,
        pos,
        pygame.Vector2(velocity_data["x"], velocity_data["y"]),
        CTagObstacle,
        image=config.get("image"),
        size=size,
        color=_color(config.get("color"), (130, 130, 130)),
        animations=animations_from_config(config),
        frames=animation_frame_count(config),
        hitbox_size=config.get("hitbox_size"),
        hitbox_offset=config.get("hitbox_offset"),
        extra=CObstacleState(
            kind,
            destructible,
            config.get("lethal", kind == "mine"),
            config.get("score", 50),
            config.get("damage", 1),
            config.get("blast_radius", 24),
        ),
    )
    if destructible:
        world.add_component(
            entity,
            CCombatStats(config.get("health", 1), 0, kind),
        )
    return entity


def _color(color_data, default):
    if color_data is None:
        return pygame.Color(*default)
    return pygame.Color(color_data["r"], color_data["g"], color_data["b"])


def _vector(value):
    if isinstance(value, dict):
        return pygame.Vector2(value["x"], value["y"])
    return pygame.Vector2(value)


def _as_tuple(value):
    if value is None:
        return None
    if isinstance(value, dict):
        return value["x"], value["y"]
    return tuple(value)
