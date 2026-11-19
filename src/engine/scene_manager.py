import pygame

from src.engine.scene import Scene


class SceneManager:
    """Dispatch frame work and switch scenes without restarting Pygame."""

    def __init__(self) -> None:
        self.current_scene: Scene | None = None
        self._pending_scene: Scene | None = None

    def start(self, scene: Scene) -> None:
        if self.current_scene is not None:
            raise RuntimeError("The scene manager has already started.")
        self._activate(scene)

    def request_change(self, scene: Scene) -> None:
        """Queue a scene change for the end of the current callback."""
        self._pending_scene = scene

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.current_scene is not None:
            self.current_scene.handle_event(event)
            self._apply_pending_change()

    def update(self, delta_time: float) -> None:
        if self.current_scene is not None:
            self.current_scene.update(delta_time)
            self._apply_pending_change()

    def draw(self, target: pygame.Surface) -> None:
        if self.current_scene is not None:
            self.current_scene.draw(target)

    def close(self) -> None:
        self._pending_scene = None
        if self.current_scene is not None:
            self.current_scene.on_exit()
            self.current_scene = None

    def _apply_pending_change(self) -> None:
        if self._pending_scene is not None:
            next_scene = self._pending_scene
            self._pending_scene = None
            self._activate(next_scene)

    def _activate(self, scene: Scene) -> None:
        if self.current_scene is not None:
            self.current_scene.on_exit()
        self.current_scene = scene
        self.current_scene.on_enter()
