import pygame
from src.ecs.components.c_combat import CBaseState, CTagBase
from src.ecs.components.c_transform import CTransform
from src.engine.camera import wrap_position
from src.services import ServiceLocator


class MiniMap:
    """Radar fijo en el panel derecho que rastrea al jugador y las bases enemigas."""

    def __init__(self, size: tuple[int, int] = (72, 76), interface_cfg: dict | None = None) -> None:
        if interface_cfg is None:
            try:
                interface_cfg = ServiceLocator.configs.load("assets/cfg/interface.json")
            except Exception:
                interface_cfg = {}

        mm_cfg = interface_cfg.get("minimap", {})
        self.size = pygame.Vector2(size)
        self.bg_color = tuple(mm_cfg.get("bg_color", [0, 16, 32]))
        self.border_color = tuple(mm_cfg.get("border_color", [65, 105, 225]))
        self.player_color = tuple(mm_cfg.get("player_color", [255, 255, 255]))
        self.base_color = tuple(mm_cfg.get("base_color", [0, 255, 80]))
        self.marker_size = int(mm_cfg.get("marker_size", 3))
        self._blink_timer = 0.0

    def draw(
        self,
        target: pygame.Surface,
        world,
        world_size: pygame.Vector2,
        player_position: pygame.Vector2,
        panel_width: int = 80,
    ) -> None:
        panel_x = target.get_width() - panel_width
        rect = pygame.Rect(panel_x + 4, 66, int(self.size.x), int(self.size.y))
        pygame.draw.rect(target, self.bg_color, rect)
        pygame.draw.rect(target, self.border_color, rect, 1)

        safe_w = max(1.0, float(world_size.x))
        safe_h = max(1.0, float(world_size.y))
        ms = self.marker_size

        def to_radar_point(pos: pygame.Vector2) -> tuple[int, int]:
            wrapped = wrap_position(pos, world_size)
            rx = rect.x + 2 + int((wrapped.x / safe_w) * max(1, rect.w - ms - 4))
            ry = rect.y + 2 + int((wrapped.y / safe_h) * max(1, rect.h - ms - 4))
            return rx, ry

        # Rastrear todas las bases activas
        drawn_bases: set[int] = set()
        for ent, (_, transform) in world.get_components(CTagBase, CTransform):
            drawn_bases.add(ent)
            bx, by = to_radar_point(transform.pos)
            pygame.draw.rect(target, self.base_color, (bx, by, ms, ms))

        # Respaldo por si una base tiene CBaseState sin CTagBase
        for ent, (_, transform) in world.get_components(CBaseState, CTransform):
            if ent in drawn_bases:
                continue
            bx, by = to_radar_point(transform.pos)
            pygame.draw.rect(target, self.base_color, (bx, by, ms, ms))

        # Rastrear posición del jugador (con ligero parpadeo para distinguirlo)
        self._blink_timer = (self._blink_timer + 1) % 30
        if self._blink_timer < 22:
            px, py = to_radar_point(player_position)
            pygame.draw.rect(target, self.player_color, (px, py, ms, ms))