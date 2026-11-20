class CBulletLifetime:
    """Limits projectile lifetime so wrapped bullets cannot block firing forever."""

    def __init__(self, lifetime: float) -> None:
        self.lifetime = max(0.0, lifetime)
        self.elapsed = 0.0
