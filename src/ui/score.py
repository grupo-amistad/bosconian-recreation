import json
from pathlib import Path
import pygame
from src.services import ServiceLocator


class ScoreManager:
    """Gestiona puntaje (1UP), puntaje máximo (HI-SCORE) y vidas extra."""

    def __init__(self, score_cfg: dict | None = None, save_path: Path | None = None) -> None:
        if score_cfg is None:
            try:
                score_cfg = ServiceLocator.configs.load("assets/cfg/score.json")
            except Exception:
                score_cfg = {}

        self.initial_lives: int = int(score_cfg.get("initial_lives", 4))
        self.max_lives: int = int(score_cfg.get("max_lives", 6))
        self.points_table: dict[str, int] = dict(score_cfg.get("points", {}))

        extra_cfg = score_cfg.get("extra_life", {})
        self.first_extra_life: int = int(extra_cfg.get("first_threshold", 10000))
        self.repeat_extra_life: int = int(extra_cfg.get("repeat_every", 25000))

        self.save_path = save_path
        default_hi = int(score_cfg.get("default_high_score", 20000))
        self.high_score: int = self._load_persisted_high_score(default_hi)

        self.score: int = 0
        self.next_extra_life_score: int = self.first_extra_life
        self.extra_lives_awarded: int = 0

    def _load_persisted_high_score(self, fallback: int) -> int:
        if self.save_path and self.save_path.exists():
            try:
                with self.save_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                return max(fallback, int(data.get("high_score", fallback)))
            except Exception:
                return fallback
        return fallback

    def _save_high_score(self) -> None:
        if not self.save_path:
            return
        try:
            self.save_path.parent.mkdir(parents=True, exist_ok=True)
            with self.save_path.open("w", encoding="utf-8") as f:
                json.dump({"high_score": self.high_score}, f, indent=2)
        except Exception:
            pass

    def reset_for_new_game(self) -> None:
        """Reinicia el puntaje de la partida actual conservando el HI-SCORE."""
        self.score = 0
        self.next_extra_life_score = self.first_extra_life
        self.extra_lives_awarded = 0

    def set_score(self, new_score: int) -> int:
        """
        Actualiza el puntaje actual, actualiza HI-SCORE si fue superado y
        calcula cuántas vidas extra (1UP) se ganaron en esta actualización.
        """
        new_score = max(0, int(new_score))
        self.score = new_score

        if self.score > self.high_score:
            self.high_score = self.score
            self._save_high_score()

        gained_lives = 0
        while self.score >= self.next_extra_life_score:
            gained_lives += 1
            self.extra_lives_awarded += 1
            if self.next_extra_life_score == self.first_extra_life:
                self.next_extra_life_score += self.repeat_extra_life
            else:
                self.next_extra_life_score += self.repeat_extra_life

        if gained_lives > 0:
            self._play_extra_life_sound()

        return gained_lives

    def add_points_for(self, entity_type: str) -> tuple[int, int]:
        """Suma puntos según la tabla de score.json. Retorna (puntos_sumados, vidas_ganadas)."""
        pts = int(self.points_table.get(entity_type, 0))
        if pts <= 0:
            return 0, 0
        gained = self.set_score(self.score + pts)
        return pts, gained

    @staticmethod
    def _play_extra_life_sound() -> None:
        if not pygame.get_init() or not pygame.mixer.get_init():
            return
        try:
            audio_cfg = ServiceLocator.configs.load("assets/cfg/audio.json")
            sfx_path = audio_cfg.get("sfx", {}).get("extra_life", "assets/sfx/extra_life.ogg")
            ServiceLocator.sounds.load(sfx_path).play()
        except Exception:
            pass

    def formatted_score(self, digits: int = 6) -> str:
        return f"{self.score:0{digits}d}"

    def formatted_high_score(self, digits: int = 6) -> str:
        return f"{self.high_score:0{digits}d}"