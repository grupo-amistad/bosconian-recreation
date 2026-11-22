

from dataclasses import dataclass, field, fields

from src.player.player_commands import DEFAULT_CONTROLS


def _xy(value, default):
    if value is None:
        return default
    if isinstance(value, dict):
        return float(value["x"]), float(value["y"])
    return float(value[0]), float(value[1])


def _rgb(value, default):
    if value is None:
        return default
    if isinstance(value, dict):
        return int(value["r"]), int(value["g"]), int(value["b"])
    return tuple(int(channel) for channel in value[:3])


def _build(cls, data: dict | None, **overrides):
    known = {item.name for item in fields(cls)}
    values = {key: value for key, value in (data or {}).items() if key in known}
    values.update({key: value for key, value in overrides.items() if value is not None})
    return cls(**values)


@dataclass
class MovementConfig:
    max_speed: float = 64.0
    cruise_speed: float = 32.0
    acceleration: float = 160.0
    deceleration: float = 96.0
    turn_speed: float = 720.0
    allow_diagonals: bool = True
    rotation_step: float = 45.0


@dataclass
class ShotConfig:

    speed: float = 180.0
    range: float = 120.0
    cooldown: float = 0.12
    max_bullets: int = 4
    autofire: bool = False
    inherit_ship_velocity: bool = True
    muzzle_offset: float = 6.0
    offscreen_margin: float = 8.0
    size: tuple[float, float] = (3.0, 3.0)
    hitbox_size: tuple[float, float] | None = None
    hitbox_offset: tuple[float, float] | None = None
    color: tuple[int, int, int] = (255, 255, 255)
    image: str | None = None
    sound: str | None = "assets/sfx/player_shoot.ogg"


@dataclass
class SpecialConfig:

    enabled: bool = False
    uses_per_level: int = 3
    bullet_count: int = 3
    spread_degrees: float = 15.0
    cooldown: float = 0.4
    speed: float | None = None
    range: float | None = None
    sound: str | None = "assets/sfx/player_special.ogg"


@dataclass
class LifeConfig:
    initial_lives: int = 4
    death_duration: float = 1.6
    explosion_count: int = 5
    explosion_interval: float = 0.18
    explosion_spread: float = 10.0
    invulnerability: float = 2.0
    blink_interval: float = 0.1
    death_sound: str | None = "assets/sfx/player_death.ogg"


@dataclass
class PlayerConfig:
    image: str | None = "assets/img/Hero.png"
    size: tuple[float, float] = (16.0, 16.0)
    hitbox_size: tuple[float, float] | None = None
    hitbox_offset: tuple[float, float] | None = None
    color: tuple[int, int, int] = (255, 255, 255)
    controls: dict[str, list[str]] = field(default_factory=lambda: dict(DEFAULT_CONTROLS))
    movement: MovementConfig = field(default_factory=MovementConfig)
    shot: ShotConfig = field(default_factory=ShotConfig)
    special: SpecialConfig = field(default_factory=SpecialConfig)
    life: LifeConfig = field(default_factory=LifeConfig)

    @classmethod
    def from_dicts(
        cls,
        player_cfg: dict | None,
        bullet_cfg: dict | None = None,
        spawn_cfg: dict | None = None,
    ) -> "PlayerConfig":
        player_cfg = player_cfg or {}
        spawn_cfg = spawn_cfg or {}
        movement_data = dict(player_cfg.get("movement", {}))
        if "max_speed" not in movement_data and "input_velocity" in player_cfg:
            movement_data["max_speed"] = player_cfg["input_velocity"]
        return cls(
            image=player_cfg.get("image", cls.image),
            size=_xy(player_cfg.get("size"), cls.size),
            hitbox_size=_xy(player_cfg.get("hitbox_size"), None),
            hitbox_offset=_xy(player_cfg.get("hitbox_offset"), None),
            color=_rgb(player_cfg.get("color"), cls.color),
            controls=player_cfg.get("controls", dict(DEFAULT_CONTROLS)),
            movement=_build(MovementConfig, movement_data),
            shot=_shot_config(bullet_cfg or {}, spawn_cfg),
            special=_build(
                SpecialConfig,
                player_cfg.get("special"),
                enabled=spawn_cfg.get("special_ability"),
                uses_per_level=spawn_cfg.get("special_uses"),
            ),
            life=_build(LifeConfig, player_cfg.get("life")),
        )


def _shot_config(bullet_cfg: dict, spawn_cfg: dict) -> ShotConfig:
    data = {
        key: value
        for key, value in bullet_cfg.items()
        if key not in ("size", "hitbox_size", "hitbox_offset", "color")
    }
    data.setdefault("speed", bullet_cfg.get("velocity", ShotConfig.speed))
    return _build(
        ShotConfig,
        data,
        size=_xy(bullet_cfg.get("size"), None),
        hitbox_size=_xy(bullet_cfg.get("hitbox_size"), None),
        hitbox_offset=_xy(bullet_cfg.get("hitbox_offset"), None),
        color=_rgb(bullet_cfg.get("color"), None),
        max_bullets=spawn_cfg.get("max_bullets"),
    )