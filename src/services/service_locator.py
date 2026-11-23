import json
from pathlib import Path

import pygame


class ConfigsService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._cache: dict[str, dict] = {}

    def load(self, path: str) -> dict:
        if path not in self._cache:
            with (self.root / path).open(encoding="utf-8") as file:
                self._cache[path] = json.load(file)
        return self._cache[path]


class ImagesService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._cache: dict[str, pygame.Surface] = {}

    def load(self, path: str) -> pygame.Surface:
        if path not in self._cache:
            self._cache[path] = pygame.image.load(self._resolve(path)).convert_alpha()
        return self._cache[path]

    def _resolve(self, path: str) -> Path:
        candidate = self.root / path
        if candidate.exists():
            return candidate
        return self.root / path.replace("assets/", "", 1)


class SoundsService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._cache: dict[str, pygame.mixer.Sound] = {}
        self._path_volumes: dict[str, float] = {}
        self.volume = 0.7

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, float(volume)))
        for path, sound in self._cache.items():
            sound.set_volume(self._effective_volume(path))

    def set_path_volume(self, path: str, volume: float) -> None:
        volume = max(0.0, min(1.0, float(volume)))
        self._path_volumes[path] = volume
        if path in self._cache:
            self._cache[path].set_volume(volume)

    def _effective_volume(self, path: str) -> float:
        return self._path_volumes.get(path, self.volume)

    def load(self, path: str) -> pygame.mixer.Sound:
        if not pygame.mixer.get_init():
            return _SilentSound()
        if path not in self._cache:
            sound = pygame.mixer.Sound(self._resolve(path))
            sound.set_volume(self._effective_volume(path))
            self._cache[path] = sound
        return self._cache[path]

    def _resolve(self, path: str) -> Path:
        candidate = self.root / path
        if candidate.exists():
            return candidate
        return self.root / path.replace("assets/", "", 1)


class FontsService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._cache: dict[tuple[str, int], pygame.font.Font] = {}

    def load(self, path: str, size: int) -> pygame.font.Font:
        key = (path, size)
        if key not in self._cache:
            candidate = self.root / path
            if not candidate.exists():
                relative_path = path.replace("assets/", "", 1)
                candidate = self.root / "assets" / relative_path
            if not candidate.exists() and path.startswith("assets/"):
                candidate = self.root / path.removeprefix("assets/")
            self._cache[key] = pygame.font.Font(candidate, size)
        return self._cache[key]


class _SilentSound:
    def play(self) -> None:
        return None


class ServiceLocator:
    configs: ConfigsService
    images: ImagesService
    sounds: SoundsService
    fonts: FontsService

    @classmethod
    def initialize(cls, root: Path) -> None:
        cls.configs = ConfigsService(root)
        cls.images = ImagesService(root)
        cls.sounds = SoundsService(root)
        cls.fonts = FontsService(root)
