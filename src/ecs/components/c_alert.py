from dataclasses import dataclass


@dataclass
class CAlert:
    """Componente ECS que almacena el estado de alerta actual del nivel."""
    level_name: str = "GREEN"
    elapsed_time: float = 0.0
    red_threshold: float = 90.0
    yellow_ratio: float = 0.5
    active_enemies: int = 0
    music_changed_to_red: bool = False

    @property
    def is_red(self) -> bool:
        return self.level_name == "RED"

    @property
    def spawn_rate_multiplier(self) -> float:
        if self.level_name == "RED":
            return 1.5
        if self.level_name == "YELLOW":
            return 1.2
        return 1.0