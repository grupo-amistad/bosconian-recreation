import pygame
from src.ecs.components.c_alert import CAlert
from src.ecs.components.c_player import CPlayer
from src.ecs.components.c_special_ability import CSpecialAbility
from src.services import ServiceLocator
from src.ui.alert_system import AlertController
from src.ui.minimap import MiniMap
from src.ui.score import ScoreManager


class HUD:
    """Panel lateral fijo con HI-SCORE, 1UP, alertas, minimapa, vidas y ronda."""

    def __init__(self, panel_width: int = 80, interface_cfg: dict | None = None) -> None:
        if interface_cfg is None:
            try:
                interface_cfg = ServiceLocator.configs.load("assets/cfg/interface.json")
            except Exception:
                interface_cfg = {}

        self.panel_width = panel_width
        self.interface_cfg = interface_cfg
        self.hud_cfg = interface_cfg.get("hud", {})
        self.colors = self.hud_cfg.get("colors", {})
        self.font_path = interface_cfg.get("font", "assets/fnt/PressStart2P.ttf")
        self.font_size = max(8, int(self.hud_cfg.get("font_size", 8)))
        self.minimap = MiniMap(size=(panel_width - 8, 76), interface_cfg=interface_cfg)
        self._font: pygame.font.Font | None = None
        self._life_icon: pygame.Surface | None = None

    def _get_font(self) -> pygame.font.Font:
        if self._font is None:
            try:
                self._font = ServiceLocator.fonts.load(self.font_path, self.font_size)
            except Exception:
                self._font = pygame.font.SysFont("monospace", self.font_size)
        return self._font

    def _get_life_icon(self) -> pygame.Surface | None:
        if self._life_icon is None:
            try:
                raw = ServiceLocator.images.load("assets/img/Hero.png")
                self._life_icon = pygame.transform.scale(raw, (10, 10))
            except Exception:
                self._life_icon = None
        return self._life_icon

    def draw(
        self,
        target: pygame.Surface,
        world,
        world_size: pygame.Vector2,
        player_position: pygame.Vector2,
        level: int,
        score_manager: ScoreManager,
        alert_controller: AlertController,
        player_entity: int | None = None,
    ) -> None:
        panel_x = target.get_width() - self.panel_width
        height = target.get_height()

        bg_col = tuple(self.hud_cfg.get("panel_bg_color", [12, 12, 24]))
        border_col = tuple(self.hud_cfg.get("panel_border_color", [65, 105, 225]))
        pygame.draw.rect(target, bg_col, (panel_x, 0, self.panel_width, height))
        pygame.draw.line(target, border_col, (panel_x, 0), (panel_x, height), 1)

        font = self._get_font()
        c_red = tuple(self.colors.get("label_red", [220, 40, 40]))
        c_white = tuple(self.colors.get("label_white", [255, 255, 255]))
        c_yellow = tuple(self.colors.get("value_yellow", [255, 235, 0]))

        x_pad = panel_x + 4

        # HI-SCORE
        hi_label = self.hud_cfg.get("high_score_label", "HI-SCORE")
        target.blit(font.render(hi_label, False, c_red), (x_pad, 6))
        hi_surf = font.render(score_manager.formatted_high_score(6), False, c_white)
        target.blit(hi_surf, (target.get_width() - hi_surf.get_width() - 4, 17))

        # 1UP (Puntaje actual)
        sc_label = self.hud_cfg.get("score_label", "1UP")
        target.blit(font.render(sc_label, False, c_red), (x_pad, 30))
        sc_surf = font.render(score_manager.formatted_score(6), False, c_white)
        target.blit(sc_surf, (target.get_width() - sc_surf.get_width() - 4, 41))

        # Banner de Alerta (GREEN / YELLOW / RED!)
        c_alert = None
        for _, comp in world.get_component(CAlert):
            c_alert = comp
            break
        alert_text, alert_color = alert_controller.get_hud_display(c_alert)
        banner_rect = pygame.Rect(x_pad, 52, self.panel_width - 8, 12)
        pygame.draw.rect(target, alert_color, banner_rect)
        alert_surf = font.render(alert_text, False, (0, 0, 0))
        target.blit(
            alert_surf,
            (
                banner_rect.x + max(0, (banner_rect.w - alert_surf.get_width()) // 2),
                banner_rect.y + 2,
            ),
        )

        # Minimapa
        self.minimap.draw(target, world, world_size, player_position, panel_width=self.panel_width)

        # Ronda actual
        round_label = self.hud_cfg.get("round_label", "ROUND")
        target.blit(font.render(round_label, False, c_white), (x_pad, 148))
        round_val = font.render(f"{level:02d}", False, c_yellow)
        target.blit(round_val, (target.get_width() - round_val.get_width() - 4, 148))

        # Vidas restantes
        player = None
        special = None
        if player_entity is not None and world.entity_exists(player_entity):
            player = world.try_component(player_entity, CPlayer)
            special = world.try_component(player_entity, CSpecialAbility)

        lives = max(0, min(6, player.lives if player else 0))
        icon = self._get_life_icon()
        for idx in range(lives):
            ix = x_pad + idx * 12
            iy = 162
            if icon is not None:
                target.blit(icon, (ix, iy))
            else:
                ship = pygame.Surface((10, 10), pygame.SRCALPHA)
                pygame.draw.polygon(ship, c_white, [(5, 0), (9, 9), (5, 7), (1, 9)])
                target.blit(ship, (ix, iy))

        # Indicador de habilidad especial del nivel
        sp_enabled = bool(special.enabled) if special is not None else False
        sp_text = "SPC:ON" if sp_enabled else "SPC:OFF"
        sp_col = tuple(self.colors.get("special_on", [0, 255, 120])) if sp_enabled else tuple(
            self.colors.get("special_off", [120, 120, 120])
        )
        target.blit(font.render(sp_text, False, sp_col), (x_pad, 180))