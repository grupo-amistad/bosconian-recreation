import esper

from src.ecs.components.c_combat import CTagBase
from src.engine.game_engine import GameEngine


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
