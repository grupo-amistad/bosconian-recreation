import unittest

import esper
import pygame

from src.create.prefab_creator import (
    create_base,
    create_bullet,
    create_enemy,
    create_obstacle,
    create_player,
)
from src.ecs.components.c_combat import (
    CBaseState,
    CScore,
    CTagTurret,
)
from src.ecs.components.c_hitbox import CHitBox
from src.ecs.components.c_player import CPlayer
from src.ecs.components.c_tag_enemy import CTagEnemy
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.systems.s_combat import system_combat_collisions


class CombatSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.world = esper.World()

    def test_enemy_speed_and_hitbox_are_configured_independently(self):
        enemy_id = create_enemy(
            self.world,
            {
                "size": {"x": 16, "y": 16},
                "hitbox_size": {"x": 4, "y": 6},
                "velocity_min": 12,
                "velocity_max": 12,
                "health": 1,
                "score": 100,
                "behavior": "patrol",
            },
            pygame.Vector2(20, 30),
            "I",
        )
        hitbox = self.world.component_for_entity(enemy_id, CHitBox)
        velocity = self.world.component_for_entity(enemy_id, CVelocity)
        self.assertEqual(hitbox.size, pygame.Vector2(4, 6))
        self.assertAlmostEqual(velocity.vel.length(), 12)

    def test_open_core_destroys_base_and_all_remaining_turrets(self):
        base_id = create_base(
            self.world,
            {
                "size": {"x": 28, "y": 28},
                "core_hitbox_size": {"x": 8, "y": 8},
                "core_hitbox_offset": {"x": 10, "y": 10},
                "turret_count": 6,
                "turret_score": 100,
                "score": 1000,
            },
            pygame.Vector2(40, 50),
            1,
            {},
        )
        base_state = self.world.component_for_entity(base_id, CBaseState)
        base_transform = self.world.component_for_entity(base_id, CTransform)
        base_hitbox = self.world.component_for_entity(base_id, CHitBox)
        self.assertEqual(len(list(self.world.get_components(CTagTurret))), 6)

        bullet_pos = base_transform.pos + base_hitbox.offset
        create_bullet(
            self.world,
            pygame.Vector2(8, 8),
            bullet_pos,
            pygame.Vector2(),
            pygame.Color("white"),
            hitbox_size=base_hitbox.size,
        )
        system_combat_collisions(self.world, {})
        self.world.process()
        self.assertTrue(self.world.entity_exists(base_id))

        base_state.core_open = True
        create_bullet(
            self.world,
            pygame.Vector2(8, 8),
            bullet_pos,
            pygame.Vector2(),
            pygame.Color("white"),
            hitbox_size=base_hitbox.size,
        )
        system_combat_collisions(self.world, {})
        self.world.process()
        self.assertFalse(self.world.entity_exists(base_id))
        self.assertEqual(len(list(self.world.get_components(CTagTurret))), 0)

    def test_destroying_all_six_turrets_destroys_base(self):
        player_id = create_player(
            self.world,
            pygame.Vector2(16, 16),
            pygame.Vector2(100, 100),
            pygame.Vector2(),
            pygame.Color("white"),
        )
        self.world.add_component(
            player_id,
            CPlayer(20, {}, 4, pygame.Vector2(100, 100)),
        )
        self.world.add_component(player_id, CScore())
        base_id = create_base(
            self.world,
            {
                "size": {"x": 28, "y": 28},
                "core_hitbox_size": {"x": 8, "y": 8},
                "core_hitbox_offset": {"x": 10, "y": 10},
                "turret_count": 6,
                "turret_score": 100,
                "score": 1000,
            },
            pygame.Vector2(40, 50),
            1,
            {},
        )

        turret_ids = [
            entity
            for entity, _ in self.world.get_components(CTagTurret, CTransform)
        ]
        for turret_id in turret_ids:
            if not self.world.entity_exists(turret_id):
                continue
            position = self.world.component_for_entity(
                turret_id, CTransform
            ).pos.copy()
            create_bullet(
                self.world,
                pygame.Vector2(8, 8),
                position,
                pygame.Vector2(),
                pygame.Color("white"),
            )
            system_combat_collisions(self.world, {})
            self.world.process()

        self.assertFalse(self.world.entity_exists(base_id))
        self.assertEqual(len(list(self.world.get_components(CTagTurret))), 0)
        self.assertEqual(
            self.world.component_for_entity(player_id, CScore).points, 1600
        )

    def test_killing_enemy_awards_configured_score(self):
        player_id = create_player(
            self.world,
            pygame.Vector2(16, 16),
            pygame.Vector2(100, 100),
            pygame.Vector2(),
            pygame.Color("white"),
        )
        self.world.add_component(
            player_id,
            CPlayer(20, {}, 4, pygame.Vector2(100, 100)),
        )
        self.world.add_component(player_id, CScore())
        enemy_id = create_enemy(
            self.world,
            {
                "size": {"x": 16, "y": 16},
                "velocity_min": 0,
                "velocity_max": 0,
                "health": 1,
                "score": 250,
            },
            pygame.Vector2(20, 30),
            "I",
        )
        create_bullet(
            self.world,
            pygame.Vector2(4, 4),
            pygame.Vector2(20, 30),
            pygame.Vector2(),
            pygame.Color("white"),
        )

        system_combat_collisions(self.world, {})
        self.world.process()

        self.assertFalse(self.world.entity_exists(enemy_id))
        score = self.world.component_for_entity(player_id, CScore)
        self.assertEqual(score.points, 250)

    def test_combat_uses_the_central_score_table(self):
        player_id = create_player(
            self.world,
            pygame.Vector2(16, 16),
            pygame.Vector2(100, 100),
            pygame.Vector2(),
            pygame.Color("white"),
        )
        self.world.add_component(
            player_id,
            CPlayer(20, {}, 4, pygame.Vector2(100, 100)),
        )
        score = CScore()
        self.world.add_component(player_id, score)
        enemy_id = create_enemy(
            self.world,
            {
                "size": {"x": 16, "y": 16},
                "velocity_min": 0,
                "velocity_max": 0,
                "health": 1,
                "score": 999,
            },
            pygame.Vector2(20, 30),
            "EnemyI",
        )
        create_bullet(
            self.world,
            pygame.Vector2(4, 4),
            pygame.Vector2(20, 30),
            pygame.Vector2(),
            pygame.Color("white"),
        )

        system_combat_collisions(
            self.world, {}, score_table={"EnemyI": 50}
        )
        self.world.process()

        self.assertFalse(self.world.entity_exists(enemy_id))
        self.assertEqual(score.points, 50)

    def test_mine_detonation_is_lethal_and_scores_on_destruction(self):
        player_id = create_player(
            self.world,
            pygame.Vector2(8, 8),
            pygame.Vector2(10, 10),
            pygame.Vector2(),
            pygame.Color("white"),
        )
        player = CPlayer(20, {}, 4, pygame.Vector2(100, 100))
        self.world.add_component(player_id, player)
        score = CScore()
        self.world.add_component(player_id, score)
        mine_id = create_obstacle(
            self.world,
            {
                "type": "mine",
                "size": {"x": 12, "y": 12},
                "destructible": True,
                "lethal": True,
                "score": 50,
                "blast_radius": 30,
            },
            pygame.Vector2(10, 10),
        )
        create_bullet(
            self.world,
            pygame.Vector2(4, 4),
            pygame.Vector2(10, 10),
            pygame.Vector2(),
            pygame.Color("white"),
        )

        system_combat_collisions(self.world, {})
        self.world.process()

        self.assertFalse(self.world.entity_exists(mine_id))
        self.assertEqual(
            self.world.component_for_entity(player_id, CTransform).pos,
            pygame.Vector2(100, 100),
        )
        self.assertEqual(score.points, 50)

    def test_enemy_contact_removes_enemy_and_costs_player_a_life(self):
        player_id = create_player(
            self.world,
            pygame.Vector2(16, 16),
            pygame.Vector2(100, 100),
            pygame.Vector2(),
            pygame.Color("white"),
        )
        player = CPlayer(20, {}, 4, pygame.Vector2(100, 100))
        self.world.add_component(player_id, player)
        enemy_id = create_enemy(
            self.world,
            {
                "size": {"x": 16, "y": 16},
                "velocity_min": 0,
                "velocity_max": 0,
                "health": 1,
                "score": 100,
            },
            pygame.Vector2(100, 100),
            "I",
        )

        system_combat_collisions(self.world, {})
        self.world.process()

        self.assertFalse(self.world.entity_exists(enemy_id))
        self.assertEqual(player.lives, 3)
        self.assertEqual(
            self.world.component_for_entity(player_id, CTransform).pos,
            pygame.Vector2(100, 100),
        )


if __name__ == "__main__":
    unittest.main()
