import math
import random

import esper
import pygame

from src.create.prefab_creator import create_square
from src.ecs.components.c_enemy_spawner import CEnemySpawner
from src.create.prefab_creator import create_entity, animations_from_config, animation_frame_count
from src.ecs.components.c_tag_enemy import CTagEnemy
from src.ecs.components.c_hunter import CHunter
from src.services import ServiceLocator


def system_enemy_spawner(world: esper.World, delta_time: float) -> None:
    components = world.get_components(CEnemySpawner)

    for _, (spawner,) in components:
        spawner.elapsed_time += delta_time

        for event in spawner.spawn_events:
            if event["spawned"] or spawner.elapsed_time < event["time"]:
                continue

            enemy_config = spawner.enemy_configs.get(event["enemy_type"])
            if enemy_config is None:
                raise ValueError(
                    f"Unknown enemy type: {event['enemy_type']}"
                )

            speed_min = enemy_config.get("velocity_min", 0)
            speed_max = enemy_config.get("velocity_max", speed_min)
            speed = random.uniform(speed_min, speed_max)
            angle = random.uniform(0, math.tau)
            velocity = pygame.Vector2(
                math.cos(angle) * speed,
                math.sin(angle) * speed,
            )

            pos = pygame.Vector2(event["position"]["x"], event["position"]["y"])
            color_data = enemy_config.get("color", {"r": 100, "g": 100, "b": 255})
            hunter = event["enemy_type"].lower() == "hunter" or enemy_config.get("type") == "hunter"
            if hunter:
                velocity.update(0, 0)
            extra = CHunter(pos,
                            enemy_config.get("aggro_distance", enemy_config.get("distance_start_chase", 180)),
                            enemy_config.get("return_distance", enemy_config.get("distance_start_return", 260)),
                            enemy_config.get("hunt_speed", enemy_config.get("velocity_chase", 70)),
                            enemy_config.get("velocity_return", enemy_config.get("velocity_chase", 70)),
                            enemy_config.get("sound_chase")) if hunter else None
            image = enemy_config.get("image")
            create_entity(world, pos, velocity if not hunter else pygame.Vector2(), CTagEnemy,
                          image=image,
                          size=pygame.Vector2(enemy_config.get("size", {}).get("x", 32), enemy_config.get("size", {}).get("y", 32)),
                          color=pygame.Color(color_data["r"], color_data["g"], color_data["b"]),
                          animations=animations_from_config(enemy_config),
                          frames=animation_frame_count(enemy_config), extra=extra)
            _play_spawn_sound(enemy_config)
            event["spawned"] = True

        dynamic = spawner.dynamic_config
        if not dynamic or spawner.elapsed_time < spawner.next_wave_time:
            continue

        interval = max(1.0, dynamic.get("interval", 6.0))
        initial_count = dynamic.get("initial_count", 2)
        increase_every = max(1, dynamic.get("increase_every", 3))
        increase_amount = dynamic.get("increase_amount", 1)
        count = initial_count + (
            spawner.wave_number // increase_every
        ) * increase_amount
        enemy_types = dynamic.get(
            "enemy_types", ["AsteroidA", "AsteroidB", "Hunter"]
        )
        area = dynamic.get(
            "spawn_area", {"min_x": 35, "max_x": 605, "min_y": 75, "max_y": 295}
        )
        for _ in range(count):
            enemy_type = random.choice(enemy_types)
            enemy_config = spawner.enemy_configs.get(enemy_type)
            if enemy_config is None:
                raise ValueError(f"Unknown enemy type: {enemy_type}")
            _spawn_enemy(
                world,
                enemy_type,
                enemy_config,
                pygame.Vector2(
                    random.uniform(area["min_x"], area["max_x"]),
                    random.uniform(area["min_y"], area["max_y"]),
                ),
            )
        spawner.wave_number += 1
        spawner.next_wave_time += interval


def _spawn_enemy(
    world: esper.World,
    enemy_type: str,
    enemy_config: dict,
    pos: pygame.Vector2,
) -> None:
    speed_min = enemy_config.get("velocity_min", 0)
    speed_max = enemy_config.get("velocity_max", speed_min)
    speed = random.uniform(speed_min, speed_max)
    angle = random.uniform(0, math.tau)
    velocity = pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
    color_data = enemy_config.get("color", {"r": 100, "g": 100, "b": 255})
    hunter = enemy_type.lower() == "hunter" or enemy_config.get("type") == "hunter"
    if hunter:
        velocity.update(0, 0)
    extra = CHunter(
        pos,
        enemy_config.get("aggro_distance", enemy_config.get("distance_start_chase", 180)),
        enemy_config.get("return_distance", enemy_config.get("distance_start_return", 260)),
        enemy_config.get("hunt_speed", enemy_config.get("velocity_chase", 70)),
        enemy_config.get("velocity_return", enemy_config.get("velocity_chase", 70)),
        enemy_config.get("sound_chase"),
    ) if hunter else None
    create_entity(
        world,
        pos,
        pygame.Vector2() if hunter else velocity,
        CTagEnemy,
        image=enemy_config.get("image"),
        size=pygame.Vector2(
            enemy_config.get("size", {}).get("x", 32),
            enemy_config.get("size", {}).get("y", 32),
        ),
        color=pygame.Color(color_data["r"], color_data["g"], color_data["b"]),
        animations=animations_from_config(enemy_config),
        frames=animation_frame_count(enemy_config),
        extra=extra,
    )
    _play_spawn_sound(enemy_config)


def _play_spawn_sound(enemy_config: dict) -> None:
    sound_path = enemy_config.get("sound_spawn", enemy_config.get("sound"))
    if sound_path:
        ServiceLocator.sounds.load(sound_path).play()
