from dataclasses import dataclass, field


class CTagEnemyBullet:
    pass


class CTagBase:
    pass


class CTagBaseCore:
    pass


class CTagTurret:
    pass


class CTagObstacle:
    pass


@dataclass
class CCombatStats:
    health: int
    score: int
    kind: str = ""


@dataclass
class CEnemyBehavior:
    mode: str
    speed: float
    turn_rate: float = 180.0
    fire_interval: float = 0.0
    fire_elapsed: float = 0.0
    bullet_speed: float = 55.0
    bullet_size: tuple[int, int] = (4, 4)
    bullet_hitbox_size: tuple[int, int] | None = None
    bullet_hitbox_offset: tuple[int, int] | None = None


@dataclass
class CBaseState:
    level: int
    open_duration: float
    closed_duration: float
    e_spawn_level: int
    e_spawn_interval: float
    enemy_configs: dict
    rotation_speed: float = 0.0
    bullet_speed: float = 50.0
    core_entity: int | None = None
    core_open_color: tuple[int, int, int] = (255, 240, 120)
    core_closed_color: tuple[int, int, int] = (70, 90, 50)
    bullet_hitbox_size: tuple[int, int] = (4, 4)
    bullet_hitbox_offset: tuple[int, int] | None = None
    elapsed: float = 0.0
    core_open: bool = False
    e_spawn_elapsed: float = 0.0
    turret_ids: set[int] = field(default_factory=set)


@dataclass
class CTurretState:
    base_id: int
    radius: float
    orbit_angle: float
    fire_interval: float
    elapsed: float = 0.0


@dataclass
class CObstacleState:
    kind: str
    destructible: bool
    lethal: bool
    score: int
    damage: int = 1
    blast_radius: float = 24.0


@dataclass
class CScore:
    points: int = 0
