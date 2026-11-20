import random
import math
import pygame


class Starfield:
    def __init__(self, size: tuple[int, int], count: int = 55) -> None:
        rng = random.Random(23)
        self.size = pygame.Vector2(size)
        self.stars = [
            [rng.randrange(size[0]), rng.randrange(size[1]), rng.choice((1, 1, 2)), rng.randrange(45, 150), rng.random() * 6.3]
            for _ in range(count)
        ]
        self.elapsed = 0.0

    def update(self, dt: float, camera_delta=None) -> None:
        self.elapsed += dt
        if camera_delta is not None:
            for star in self.stars:
                star[0] = (star[0] - camera_delta.x * .12) % self.size.x
                star[1] = (star[1] - camera_delta.y * .12) % self.size.y

    def draw(self, target) -> None:
        for x, y, radius, brightness, phase in self.stars:
            pulse = .65 + .35 * abs(math.sin(self.elapsed * 1.8 + phase))
            shade = max(25, min(210, round(brightness * pulse)))
            target.fill((shade, shade, min(255, shade + 35)), (round(x), round(y), radius, radius))
