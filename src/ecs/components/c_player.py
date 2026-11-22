import pygame


class CPlayer:
    def __init__(
        self,
        input_velocity: float = 0.0,
        bullet_config: dict | None = None,
        max_bullets: int = 4,
        spawn_position=None,
        lives: int = 4,
        size=None,
    ) -> None:
        self.input_velocity = input_velocity
        self.bullet_config = bullet_config or {}
        self.max_bullets = max_bullets
        self.spawn_position = (
            pygame.Vector2(spawn_position) if spawn_position is not None else None
        )
        self.size = pygame.Vector2(size or (16, 16))
        self.sound_elapsed = 0.0
        self.lives = lives
        self.score = 0
        self.dead = False
        self.facing = pygame.Vector2(0, -1)
        self.facing_angle = 0
        self.fire_cooldown_remaining = 0.0
