from src.player.player_config import ShotConfig


class CPlayerWeapon:

    def __init__(self, config: ShotConfig) -> None:
        self.config = config
        self.cooldown_remaining = 0.0