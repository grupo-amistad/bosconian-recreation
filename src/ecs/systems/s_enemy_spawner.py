import random

import esper
import pygame

from src.ecs.components.c_enemy_spawner import CEnemySpawner
from src.create.prefab_creator import create_enemy
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

            pos = pygame.Vector2(event["position"]["x"], event["position"]["y"])
            _spawn_enemy(world, event["enemy_type"], enemy_config, pos)
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
    create_enemy(world, enemy_config, pos, enemy_type)
    _play_spawn_sound(enemy_config)


def _play_spawn_sound(enemy_config: dict) -> None:
    sound_path = enemy_config.get("sound_spawn")
    if sound_path:
        ServiceLocator.sounds.load(sound_path).play()
