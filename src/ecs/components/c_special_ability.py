class CSpecialAbility:
    def __init__(self, duration: float = 2.0, cooldown: float = 5.0, radius: float = 140.0) -> None:
        self.duration = duration
        self.cooldown = cooldown
        self.radius = radius
        self.active_for = 0.0
        self.cooldown_remaining = 0.0
