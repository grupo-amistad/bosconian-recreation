from abc import ABC, abstractmethod

import pygame


class Scene(ABC):
    """Lifecycle and frame contract shared by all game scenes."""

    def on_enter(self) -> None:
        """Prepare scene state; the game engine owns the Pygame display."""

    def on_exit(self) -> None:
        """Release scene-owned state without shutting down Pygame."""

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle one event delivered by the shared game loop."""

    @abstractmethod
    def update(self, delta_time: float) -> None:
        """Advance this scene by delta_time seconds."""

    @abstractmethod
    def draw(self, target: pygame.Surface) -> None:
        """Draw this scene onto the engine-owned display surface."""
