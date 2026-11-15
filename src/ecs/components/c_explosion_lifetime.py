class CExplosionLifetime:
    """Independent cleanup timer for an explosion entity."""

    def __init__(self, duration: float = 0.25) -> None:
        self.duration = duration
        self.elapsed = 0.0
