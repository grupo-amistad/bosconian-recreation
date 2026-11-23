import esper

from src.ecs.components.c_combat import CScore, CTagBase
from src.ecs.components.c_player import CPlayer
from src.engine.game_engine import GameEngine
from src.ui.score import ScoreManager


def test_level_is_not_cleared_while_a_base_remains():
    engine = GameEngine.__new__(GameEngine)
    engine.ecs_world = esper.World()
    engine._level_base_count = 2
    engine.ecs_world.create_entity(CTagBase())

    assert not engine._level_is_cleared()


def test_level_is_cleared_after_all_configured_bases_are_destroyed():
    engine = GameEngine.__new__(GameEngine)
    engine.ecs_world = esper.World()
    engine._level_base_count = 1

    assert engine._level_is_cleared()


def test_empty_level_does_not_trigger_victory():
    engine = GameEngine.__new__(GameEngine)
    engine.ecs_world = esper.World()
    engine._level_base_count = 0

    assert not engine._level_is_cleared()


def test_destroying_all_bases_advances_once_and_awards_clear_bonus():
    engine = GameEngine.__new__(GameEngine)
    engine.ecs_world = esper.World()
    engine._level_base_count = 1
    engine._level_transition_started = False
    engine.player_entity = engine.ecs_world.create_entity()
    player = CPlayer(20, {}, 4)
    engine.ecs_world.add_component(engine.player_entity, player)
    score = CScore()
    engine.ecs_world.add_component(engine.player_entity, score)
    engine.score_manager = ScoreManager(
        {
            "points": {"round_clear_bonus": 500},
            "max_lives": 6,
        }
    )
    engine.score = 0
    engine.complete_level_calls = 0

    def complete_level():
        engine.complete_level_calls += 1

    engine.complete_level = complete_level

    assert engine._advance_after_level_clear(player)
    assert not engine._advance_after_level_clear(player)
    assert engine.complete_level_calls == 1
    assert player.score == 500
    assert score.points == 500


def test_all_ten_levels_initialize_with_configured_entity_types():
    engine = GameEngine()
    try:
        for level in range(1, 11):
            engine.level = level
            engine.start_game()
            assert engine._level_base_count > 0
    finally:
        engine._clean()
