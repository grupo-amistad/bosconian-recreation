import pygame


class Camera:
    """Maps toroidal world coordinates to a fixed screen viewport."""

    def __init__(self, world_size: pygame.Vector2, viewport_size: pygame.Vector2) -> None:
        self.world_size = pygame.Vector2(world_size)
        self.viewport_size = pygame.Vector2(viewport_size)
        if min(self.world_size) <= 0 or min(self.viewport_size) <= 0:
            raise ValueError("Camera world and viewport dimensions must be positive.")
        self.center = self.world_size / 2
        self.delta = pygame.Vector2()

    def follow(self, position: pygame.Vector2) -> pygame.Vector2:
        next_center = wrap_position(position, self.world_size)
        self.delta = shortest_delta(self.center, next_center, self.world_size)
        self.center = next_center
        return pygame.Vector2(self.delta)

    def world_to_screen(self, position: pygame.Vector2) -> pygame.Vector2:
        offset = shortest_delta(self.center, position, self.world_size)
        return self.viewport_size / 2 + offset

    def screen_to_world(self, position: pygame.Vector2) -> pygame.Vector2:
        offset = pygame.Vector2(position) - self.viewport_size / 2
        return wrap_position(self.center + offset, self.world_size)

    def render_positions(
        self,
        position: pygame.Vector2,
        sprite_size: pygame.Vector2,
    ) -> list[pygame.Vector2]:
        """Return wrapped sprite copies that intersect the viewport."""
        base = self.world_to_screen(position)
        viewport = pygame.Rect((0, 0), self.viewport_size)
        visible: list[pygame.Vector2] = []
        x_offsets = (-self.world_size.x, 0, self.world_size.x)
        y_offsets = (-self.world_size.y, 0, self.world_size.y)
        for x_offset in x_offsets:
            for y_offset in y_offsets:
                candidate = base + pygame.Vector2(x_offset, y_offset)
                rect = pygame.Rect(
                    round(candidate.x),
                    round(candidate.y),
                    round(sprite_size.x),
                    round(sprite_size.y),
                )
                if viewport.colliderect(rect) and candidate not in visible:
                    visible.append(candidate)
        return visible


def wrap_position(position: pygame.Vector2, world_size: pygame.Vector2) -> pygame.Vector2:
    return pygame.Vector2(position.x % world_size.x, position.y % world_size.y)


def shortest_delta(
    start: pygame.Vector2,
    end: pygame.Vector2,
    world_size: pygame.Vector2,
) -> pygame.Vector2:
    """Shortest signed displacement from start to end on a wrapped world."""
    delta = pygame.Vector2(end) - pygame.Vector2(start)
    delta.x = (delta.x + world_size.x / 2) % world_size.x - world_size.x / 2
    delta.y = (delta.y + world_size.y / 2) % world_size.y - world_size.y / 2
    return delta
