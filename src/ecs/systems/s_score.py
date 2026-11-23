import esper
from src.ecs.components.c_combat import CScore
from src.ecs.components.c_player import CPlayer
from src.ui.score import ScoreManager


def system_score(world: esper.World, score_manager: ScoreManager) -> None:
    """
    Sincroniza el puntaje entre CPlayer, CScore y ScoreManager,
    otorgando vidas extra cuando se alcanzan los umbrales de 1UP.
    """
    for ent, c_player in world.get_component(CPlayer):
        c_score = world.try_component(ent, CScore)
        current_points = c_player.score
        if c_score is not None:
            current_points = max(current_points, c_score.points)

        gained_lives = score_manager.set_score(current_points)
        if gained_lives > 0 and not c_player.dead:
            c_player.lives = min(score_manager.max_lives, c_player.lives + gained_lives)

        c_player.score = score_manager.score
        if c_score is not None:
            c_score.points = score_manager.score