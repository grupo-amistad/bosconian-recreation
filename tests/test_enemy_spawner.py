import unittest
from unittest.mock import patch

import esper

from src.ecs.components.c_enemy_spawner import CEnemySpawner
from src.ecs.systems.s_enemy_spawner import system_enemy_spawner


class EnemySpawnerTests(unittest.TestCase):
    @patch("src.ecs.systems.s_enemy_spawner._play_spawn_sound")
    @patch("src.ecs.systems.s_enemy_spawner.create_enemy")
    def test_scheduled_spawn_plays_sound_once(self, create_enemy, play_sound):
        world = esper.World()
        spawner = CEnemySpawner(
            [
                {
                    "time": 1.0,
                    "enemy_type": "EnemyI",
                    "position": {"x": 10, "y": 20},
                }
            ],
            {"EnemyI": {"sound_spawn": "spawn.ogg"}},
        )
        world.add_component(world.create_entity(), spawner)

        system_enemy_spawner(world, 1.0)

        create_enemy.assert_called_once()
        play_sound.assert_called_once_with({"sound_spawn": "spawn.ogg"})
        self.assertTrue(spawner.spawn_events[0]["spawned"])

    def test_alert_multiplier_increases_dynamic_spawn_rate(self):
        world = esper.World()
        entity = world.create_entity()
        spawner = CEnemySpawner(
            [],
            {},
            {
                "start_time": 1.0,
                "interval": 6.0,
                "initial_count": 0,
                "enemy_types": [],
            },
        )
        world.add_component(entity, spawner)

        system_enemy_spawner(world, 1.0, spawn_rate_multiplier=1.5)

        self.assertAlmostEqual(spawner.next_wave_time, 5.0)
        self.assertEqual(spawner.wave_number, 1)


if __name__ == "__main__":
    unittest.main()
