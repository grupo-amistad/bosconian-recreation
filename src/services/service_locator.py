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

    def load(self, path: str) -> pygame.mixer.Sound:
        if not pygame.mixer.get_init():
            return _SilentSound()
        if path not in self._cache:
            self._cache[path] = pygame.mixer.Sound(self._resolve(path))
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
