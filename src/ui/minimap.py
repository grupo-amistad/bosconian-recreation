import pygame

from src.engine.camera import wrap_position


class MiniMap:
    """Fixed Bosconian radar drawn inside the right-side HUD panel."""

    def __init__(self, size: tuple[int, int] = (72, 92)) -> None:
        self.size = pygame.Vector2(size)

    def draw(self, target, world, world_size, player_position) -> None:
        from src.ecs.components.c_surface import CSurface
        from src.ecs.components.c_tag_enemy import CTagEnemy
        from src.ecs.components.c_transform import CTransform

        panel_x = target.get_width() - 80
        rect = pygame.Rect(panel_x + 4, 64, int(self.size.x), int(self.size.y))
        pygame.draw.rect(target, (126, 116, 229), rect)

        def point(pos):
            wrapped = wrap_position(pos, world_size)
            return (
                rect.x + 2 + round(wrapped.x / world_size.x * (rect.w - 5)),
                rect.y + 2 + round(wrapped.y / world_size.y * (rect.h - 5)),
            )

        enemy_font = pygame.font.Font(None, 8)
        for _, (_, transform, _) in world.get_components(CTagEnemy, CTransform, CSurface):
            target.blit(enemy_font.render("H", False, (0, 255, 40)), point(transform.pos))
        pygame.draw.rect(target, (0, 0, 0), (*point(player_position), 2, 2))
