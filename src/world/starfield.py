import math
import random
import pygame
from src.services import ServiceLocator


class Starfield:
    """Fondo espacial con estrellas de colores, parpadeo y paralaje multicapa."""

    DEFAULT_COLORS = [(213, 0, 0), (118, 255, 3), (65, 105, 225)]
    PARALLAX_LAYERS = (0.35, 0.65, 1.0)

    def __init__(self, size: tuple[int, int], count: int | None = None, world_cfg: dict | None = None) -> None:
        if world_cfg is None:
            try:
                world_cfg = ServiceLocator.configs.load("assets/cfg/world.json")
            except Exception:
                world_cfg = {}

        self.size = pygame.Vector2(max(1, size[0]), max(1, size[1]))
        star_count = count if count is not None else int(world_cfg.get("stars_number", 100))
        base_parallax = float(world_cfg.get("stars_parallax_factor", 1.0))

        raw_colors = world_cfg.get("star_colors", [])
        colors = [
            (int(c["r"]), int(c["g"]), int(c["b"]))
            for c in raw_colors
            if all(k in c for k in ("r", "g", "b"))
        ] or list(self.DEFAULT_COLORS)

        blink_cfg = world_cfg.get("stars_blink_speed", {})
        blink_min = float(blink_cfg.get("min", 0.25))
        blink_max = float(blink_cfg.get("max", 0.50))
        if blink_max < blink_min:
            blink_max = blink_min

        rng = random.Random(23)
        self.stars: list[dict] = []
        for idx in range(star_count):
            layer_factor = self.PARALLAX_LAYERS[idx % len(self.PARALLAX_LAYERS)] * base_parallax
            star_size = 2 if layer_factor >= 0.95 and idx % 4 == 0 else 1
            self.stars.append(
                {
                    "x": rng.uniform(0.0, self.size.x),
                    "y": rng.uniform(0.0, self.size.y),
                    "color": colors[idx % len(colors)],
                    "layer": layer_factor,
                    "size": star_size,
                    "blink_period": rng.uniform(blink_min, blink_max),
                    "blink_timer": rng.uniform(0.0, blink_max),
                    "visible": True,
                    "phase": rng.uniform(0.0, math.tau),
                }
            )

        self.elapsed = 0.0
        self.menu_drift_speed = pygame.Vector2(-18.0, 12.0)

    def update(self, dt: float, camera_delta: pygame.Vector2 | None = None) -> None:
        self.elapsed += dt
        for star in self.stars:
            # Parpadeo configurable
            star["blink_timer"] += dt
            if star["blink_timer"] >= star["blink_period"]:
                star["blink_timer"] %= star["blink_period"]
                star["visible"] = not star["visible"]

            # Movimiento diferenciado: desplazamiento continuo en menús vs paralaje por cámara en juego
            if camera_delta is None:
                star["x"] = (star["x"] + self.menu_drift_speed.x * star["layer"] * dt) % self.size.x
                star["y"] = (star["y"] + self.menu_drift_speed.y * star["layer"] * dt) % self.size.y
            else:
                star["x"] = (star["x"] - camera_delta.x * star["layer"] * 0.45) % self.size.x
                star["y"] = (star["y"] - camera_delta.y * star["layer"] * 0.45) % self.size.y

    def draw(self, target: pygame.Surface) -> None:
        for star in self.stars:
            if not star["visible"]:
                continue
            pulse = 0.7 + 0.3 * abs(math.sin(self.elapsed * 2.5 + star["phase"]))
            r, g, b = star["color"]
            shaded = (
                max(20, min(255, int(r * pulse))),
                max(20, min(255, int(g * pulse))),
                max(20, min(255, int(b * pulse))),
            )
            sz = star["size"]
            target.fill(shaded, (int(star["x"]), int(star["y"]), sz, sz))