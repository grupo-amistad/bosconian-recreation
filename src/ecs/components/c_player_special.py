from src.player.player_config import SpecialConfig


class CPlayerSpecial:

    def __init__(self, config: SpecialConfig) -> None:
        self.config = config
        self.uses_left = config.uses_per_level if config.enabled else 0
        self.cooldown_remaining = 0.0