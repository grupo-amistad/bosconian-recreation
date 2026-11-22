from src.player.player_config import MovementConfig


class CPlayerMovement:
    
    def __init__(self, config: MovementConfig, heading: float = 0.0) -> None:
        self.config = config
        self.heading = heading
        self.speed = 0.0