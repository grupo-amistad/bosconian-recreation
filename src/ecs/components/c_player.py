class CPlayer:
    def __init__(
        self,
        input_velocity: float,
        bullet_config: dict,
        max_bullets: int,
        spawn_position=None,
    ) -> None:
        self.input_velocity = input_velocity
        self.bullet_config = bullet_config
        self.max_bullets = max_bullets
        self.spawn_position = spawn_position
        self.sound_elapsed = 0.0
        self.lives = 4
        self.score = 0
        self.dead = False
