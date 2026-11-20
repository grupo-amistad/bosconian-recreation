import pygame

from src.engine.camera import wrap_position


class MiniMap:
    """Screen-space radar showing wrapped world positions."""

    def __init__(self, size: tuple[int, int] = (58, 42)) -> None:
        self.size = pygame.Vector2(size)
        self.margin = 5

    def draw(self, target, world, world_size, player_position) -> None:
        from src.ecs.components.c_surface import CSurface
        from src.ecs.components.c_tag_enemy import CTagEnemy
        from src.ecs.components.c_transform import CTransform

        rect = pygame.Rect(target.get_width() - int(self.size.x) - self.margin,
                           self.margin, int(self.size.x), int(self.size.y))
        pygame.draw.rect(target, (0, 0, 0), rect)
        pygame.draw.rect(target, (80, 110, 150), rect, 1)

        def point(pos):
            wrapped = wrap_position(pos, world_size)
            return (rect.x + round(wrapped.x / world_size.x * (rect.w - 3)) + 1,
                    rect.y + round(wrapped.y / world_size.y * (rect.h - 3)) + 1)

        for _, (_, transform, _) in world.get_components(CTagEnemy, CTransform, CSurface):
            pygame.draw.circle(target, (255, 65, 65), point(transform.pos), 1)
        pygame.draw.circle(target, (80, 255, 120), point(player_position), 2)
