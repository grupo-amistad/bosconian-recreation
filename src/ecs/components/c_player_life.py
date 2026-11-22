from src.player.player_config import LifeConfig


class CPlayerLife:
    
    def __init__(self, config: LifeConfig) -> None:
        self.config = config
        self.explosions_spawned = 0
        self.blink_elapsed = 0.0
        self.death_position = None
        self.hidden_surface = None
        self.hidden_hitbox = None