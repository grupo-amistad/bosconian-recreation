"""
Pruebas unitarias para ScoreManager, system_score, AlertController (State) y system_alert.
Ejecutar con:
    py -m unittest tests/test_score_and_alerts.py -v
"""

import tempfile
import unittest
from pathlib import Path
import esper

from src.ecs.components.c_alert import CAlert
from src.ecs.components.c_combat import CScore
from src.ecs.components.c_player import CPlayer
from src.ecs.systems.s_alert import system_alert
from src.ecs.systems.s_score import system_score
from src.ui.alert_system import AlertController, GreenAlertState, RedAlertState, YellowAlertState
from src.ui.score import ScoreManager


class TestScoreAndAlerts(unittest.TestCase):
    def setUp(self):
        self.score_cfg = {
            "initial_lives": 4,
            "max_lives": 6,
            "default_high_score": 20000,
            "extra_life": {
                "first_threshold": 10000,
                "repeat_every": 25000,
            },
            "points": {
                "EnemyI": 50,
                "turret": 200,
                "base_core": 1500,
            },
        }

    def test_score_highscore_and_extra_lives(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save_file = Path(tmpdir) / "highscore.json"
            mgr = ScoreManager(self.score_cfg, save_path=save_file)

            self.assertEqual(mgr.score, 0)
            self.assertEqual(mgr.high_score, 20000)

            # Llegar a 10,000 otorga 1 vida extra (1UP)
            gained = mgr.set_score(10000)
            self.assertEqual(gained, 1)
            self.assertEqual(mgr.next_extra_life_score, 35000)
            self.assertEqual(mgr.high_score, 20000)

            # Superar 20,000 actualiza HI-SCORE y lo guarda en disco
            gained = mgr.set_score(22500)
            self.assertEqual(gained, 0)
            self.assertEqual(mgr.high_score, 22500)

            # Llegar a 35,000 otorga la segunda vida extra
            gained = mgr.set_score(35000)
            self.assertEqual(gained, 1)
            self.assertEqual(mgr.next_extra_life_score, 60000)

            # Nueva instancia recupera el HI-SCORE persistido
            mgr2 = ScoreManager(self.score_cfg, save_path=save_file)
            self.assertEqual(mgr2.high_score, 35000)

    def test_ecs_system_score_sync(self):
        world = esper.World()
        mgr = ScoreManager(self.score_cfg)

        ent = world.create_entity()
        player = CPlayer.__new__(CPlayer)
        player.lives = 4
        player.score = 0
        player.dead = False
        world.add_component(ent, player)
        world.add_component(ent, CScore(points=10500))

        system_score(world, mgr)

        self.assertEqual(mgr.score, 10500)
        self.assertEqual(player.score, 10500)
        self.assertEqual(player.lives, 5)

    def test_alert_state_transitions_by_time(self):
        world = esper.World()
        controller = AlertController(interface_cfg={}, audio_cfg={})
        ent = world.create_entity()
        c_alert = CAlert(red_threshold=60.0, yellow_ratio=0.5)
        controller.reset(c_alert, red_threshold=60.0)
        world.add_component(ent, c_alert)

        self.assertIsInstance(controller.state, GreenAlertState)
        self.assertEqual(c_alert.level_name, "GREEN")

        # Avanza 30s (50% de 60s) -> pasa a YELLOW
        system_alert(world, 30.0, controller)
        self.assertIsInstance(controller.state, YellowAlertState)
        self.assertEqual(c_alert.level_name, "YELLOW")

        # Avanza otros 30s (total 60s) -> pasa a RED por tiempo de espera
        system_alert(world, 30.0, controller)
        self.assertIsInstance(controller.state, RedAlertState)
        self.assertEqual(c_alert.level_name, "RED")
        self.assertTrue(c_alert.is_red)
        self.assertEqual(c_alert.spawn_rate_multiplier, 1.5)


if __name__ == "__main__":
    unittest.main()