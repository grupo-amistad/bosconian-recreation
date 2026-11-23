from abc import ABC, abstractmethod
import pygame
from src.ecs.components.c_alert import CAlert
from src.services import ServiceLocator


class AlertState(ABC):
    """Patrón State: clase base para los estados de alerta (GREEN, YELLOW, RED)."""

    name: str = "GREEN"

    def on_enter(self, controller: "AlertController", c_alert: CAlert) -> None:
        c_alert.level_name = self.name

    @abstractmethod
    def update(self, controller: "AlertController", c_alert: CAlert, delta_time: float) -> None:
        """Actualiza temporizadores y evalúa transiciones de estado."""

    def on_event(self, controller: "AlertController", c_alert: CAlert, event_name: str) -> None:
        """Permite transiciones inmediatas por eventos del juego (ej. espía escapa, base atacada)."""
        if event_name == "force_red":
            controller.change_state(RedAlertState(), c_alert)
        elif event_name == "reset":
            controller.change_state(GreenAlertState(), c_alert)


class GreenAlertState(AlertState):
    name = "GREEN"

    def on_enter(self, controller: "AlertController", c_alert: CAlert) -> None:
        super().on_enter(controller, c_alert)
        c_alert.music_changed_to_red = False

    def update(self, controller: "AlertController", c_alert: CAlert, delta_time: float) -> None:
        if c_alert.elapsed_time >= c_alert.red_threshold:
            controller.change_state(RedAlertState(), c_alert)
        elif c_alert.elapsed_time >= c_alert.red_threshold * c_alert.yellow_ratio or c_alert.active_enemies >= 3:
            controller.change_state(YellowAlertState(), c_alert)

    def on_event(self, controller: "AlertController", c_alert: CAlert, event_name: str) -> None:
        super().on_event(controller, c_alert, event_name)
        if event_name in ("enemy_engaged", "turret_damaged"):
            controller.change_state(YellowAlertState(), c_alert)


class YellowAlertState(AlertState):
    name = "YELLOW"

    def on_enter(self, controller: "AlertController", c_alert: CAlert) -> None:
        super().on_enter(controller, c_alert)
        controller.play_sfx("alert_yellow")

    def update(self, controller: "AlertController", c_alert: CAlert, delta_time: float) -> None:
        if c_alert.elapsed_time >= c_alert.red_threshold:
            controller.change_state(RedAlertState(), c_alert)


class RedAlertState(AlertState):
    name = "RED"

    def on_enter(self, controller: "AlertController", c_alert: CAlert) -> None:
        super().on_enter(controller, c_alert)
        controller.play_sfx("alert_red")
        controller.trigger_red_alert_music(c_alert)

    def update(self, controller: "AlertController", c_alert: CAlert, delta_time: float) -> None:
        # Permanece en alerta roja hasta completar el nivel o reiniciar
        return None


class AlertController:
    """Administra el estado de alerta activo y provee datos listos para el HUD y audio."""

    DEFAULT_ALERTS = {
        "GREEN": {"text": "CONDITION GREEN", "short_text": "GREEN", "color": [0, 220, 80]},
        "YELLOW": {"text": "CONDITION YELLOW", "short_text": "YELLOW", "color": [255, 220, 0]},
        "RED": {"text": "CONDITION RED", "short_text": "RED!", "color": [255, 40, 40]},
    }

    def __init__(self, interface_cfg: dict | None = None, audio_cfg: dict | None = None) -> None:
        if interface_cfg is None:
            try:
                interface_cfg = ServiceLocator.configs.load("assets/cfg/interface.json")
            except Exception:
                interface_cfg = {}
        if audio_cfg is None:
            try:
                audio_cfg = ServiceLocator.configs.load("assets/cfg/audio.json")
            except Exception:
                audio_cfg = {}

        self.alerts_cfg: dict = interface_cfg.get("alerts", self.DEFAULT_ALERTS)
        self.audio_cfg: dict = audio_cfg
        self.state: AlertState = GreenAlertState()

    def reset(self, c_alert: CAlert, red_threshold: float = 90.0) -> None:
        c_alert.elapsed_time = 0.0
        c_alert.red_threshold = max(1.0, float(red_threshold))
        c_alert.active_enemies = 0
        c_alert.music_changed_to_red = False
        self.change_state(GreenAlertState(), c_alert)

    def change_state(self, new_state: AlertState, c_alert: CAlert) -> None:
        if type(self.state) is type(new_state) and c_alert.level_name == new_state.name:
            return
        self.state = new_state
        self.state.on_enter(self, c_alert)

    def update(self, c_alert: CAlert, delta_time: float) -> None:
        c_alert.elapsed_time += max(0.0, delta_time)
        self.state.update(self, c_alert, delta_time)

    def notify_event(self, c_alert: CAlert, event_name: str) -> None:
        self.state.on_event(self, c_alert, event_name)

    def get_hud_display(self, c_alert: CAlert | None = None) -> tuple[str, tuple[int, int, int]]:
        key = c_alert.level_name if c_alert else self.state.name
        info = self.alerts_cfg.get(key, self.DEFAULT_ALERTS.get(key, self.DEFAULT_ALERTS["GREEN"]))
        text = info.get("short_text", key)
        col = tuple(info.get("color", [0, 220, 80]))
        return text, col  # type: ignore[return-value]

    def play_sfx(self, sfx_key: str) -> None:
        if not pygame.get_init() or not pygame.mixer.get_init():
            return
        try:
            path = self.audio_cfg.get("sfx", {}).get(sfx_key)
            if path:
                ServiceLocator.sounds.load(path).play()
        except Exception:
            pass

    def trigger_red_alert_music(self, c_alert: CAlert) -> None:
        if c_alert.music_changed_to_red:
            return
        c_alert.music_changed_to_red = True
        if not pygame.get_init() or not pygame.mixer.get_init():
            return
        try:
            music_path = self.audio_cfg.get("music", {}).get("alert_red")
            if music_path:
                resolved = ServiceLocator.sounds._resolve(music_path)
                pygame.mixer.music.load(resolved)
                pygame.mixer.music.set_volume(
                    self.audio_cfg.get("volumes", {}).get("music", 0.5)
                )
                pygame.mixer.music.play(-1)
        except Exception:
            pass