import math

import esper
import pygame

from src.create.prefab_creator import create_enemy, create_enemy_bullet
from src.ecs.components.c_combat import (
    CBaseState,
    CCombatStats,
    CEnemyBehavior,
    CObstacleState,
    CScore,
    CTagBase,
    CTagEnemyBullet,
    CTagObstacle,
    CTagTurret,
    CTurretState,
)
from src.ecs.components.c_hitbox import CHitBox
from src.ecs.components.c_player import CPlayer
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_hunter import CHunter
from src.ecs.components.c_state import CState
from src.ecs.components.c_tag_bullet import CTagBullet
from src.ecs.components.c_tag_enemy import CTagEnemy
from src.ecs.components.c_tag_player import CTagPlayer
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.systems.s_collisions import _explode
from src.engine.camera import shortest_delta


def system_enemy_behavior(
    world: esper.World,
    delta_time: float,
    world_size: pygame.Vector2 | None = None,
) -> None:
    player_data = next(
        iter(world.get_components(CTagPlayer, CTransform, CHitBox)), None
    )
    player_position = None
    if player_data:
        _, (_, player_transform, player_hitbox) = player_data
        player_position = pygame.Vector2(_rect(player_transform, player_hitbox).center)

    bases = [
        transform.pos
        for _, (_, transform, _) in world.get_components(
            CTagBase, CTransform, CHitBox
        )
    ]
    for _, (_, behavior, transform, velocity, state) in world.get_components(
        CTagEnemy, CEnemyBehavior, CTransform, CVelocity, CState
    ):
        state.elapsed += delta_time
        state.name = behavior.mode.upper()
        target = None
        if behavior.mode == "seek_player":
            target = player_position
        elif behavior.mode == "seek_base" and bases:
            target = min(
                bases,
                key=lambda position: shortest_delta(
                    transform.pos, position, world_size
                ).length_squared(),
            )
        if target is not None:
            direction = shortest_delta(transform.pos, target, world_size)
            if direction.length_squared():
                desired = direction.normalize() * behavior.speed
                if velocity.vel.length_squared():
                    angle = velocity.vel.angle_to(desired)
                    max_turn = behavior.turn_rate * delta_time
                    velocity.vel.rotate_ip(max(-max_turn, min(max_turn, angle)))
                    velocity.vel.scale_to_length(behavior.speed)
                else:
                    velocity.vel = desired
        elif velocity.vel.length_squared() and behavior.speed:
            velocity.vel.scale_to_length(behavior.speed)

        if behavior.fire_interval <= 0 or player_position is None:
            continue
        behavior.fire_elapsed += delta_time
        if behavior.fire_elapsed < behavior.fire_interval:
            continue
        direction = shortest_delta(transform.pos, player_position, world_size)
        if direction.length_squared():
            create_enemy_bullet(
                world,
                transform.pos,
                direction.normalize() * behavior.bullet_speed,
                behavior.bullet_size,
                behavior.bullet_hitbox_size,
                behavior.bullet_hitbox_offset,
            )
        behavior.fire_elapsed = 0.0


def system_base_behavior(
    world: esper.World,
    delta_time: float,
    world_size: pygame.Vector2 | None = None,
) -> None:
    player_data = next(
        iter(world.get_components(CTagPlayer, CTransform, CHitBox)), None
    )
    player_position = None
    if player_data:
        _, (_, transform, hitbox) = player_data
        player_position = pygame.Vector2(_rect(transform, hitbox).center)

    for base_id, (base, base_transform, base_hitbox, state, gameplay_state) in list(
        world.get_components(
            CTagBase, CTransform, CHitBox, CBaseState, CState
        )
    ):
        state.elapsed += delta_time
        gameplay_state.elapsed += delta_time
        period = state.open_duration if state.core_open else state.closed_duration
        if period > 0 and state.elapsed >= period:
            state.elapsed %= period
            state.core_open = not state.core_open
            gameplay_state.name = (
                "CORE_OPEN" if state.core_open else "CORE_CLOSED"
            )
            gameplay_state.elapsed = 0.0

        center = pygame.Vector2(_rect(base_transform, base_hitbox).center)
        if state.core_entity is not None and world.entity_exists(state.core_entity):
            core_transform = world.try_component(state.core_entity, CTransform)
            core_surface = world.try_component(state.core_entity, CSurface)
            if core_transform:
                core_transform.pos.update(base_transform.pos + base_hitbox.offset)
            if core_surface:
                core_color = (
                    state.core_open_color if state.core_open
                    else state.core_closed_color
                )
                core_surface.surf.fill(core_color)
        for turret_id in list(state.turret_ids):
            if not world.entity_exists(turret_id):
                state.turret_ids.discard(turret_id)
                continue
            turret_transform = world.try_component(turret_id, CTransform)
            turret = world.try_component(turret_id, CTurretState)
            if turret_transform is None or turret is None:
                continue
            turret.orbit_angle += state.rotation_speed * delta_time
            angle = math.radians(turret.orbit_angle)
            turret_transform.pos.update(
                center.x + math.cos(angle) * turret.radius - 4,
                center.y + math.sin(angle) * turret.radius - 4,
            )
            if player_position is None or turret.fire_interval <= 0:
                continue
            turret.elapsed += delta_time
            if turret.elapsed < turret.fire_interval:
                continue
            aim = shortest_delta(
                turret_transform.pos + pygame.Vector2(4, 4),
                player_position,
                world_size,
            )
            if aim.length_squared():
                create_enemy_bullet(
                    world,
                    turret_transform.pos + pygame.Vector2(2, 2),
                    aim.normalize() * state.bullet_speed,
                    pygame.Vector2(state.bullet_hitbox_size),
                    state.bullet_hitbox_size,
                    state.bullet_hitbox_offset,
                )
            turret.elapsed = 0.0

        if (
            state.level >= state.e_spawn_level
            and state.e_spawn_interval > 0
            and state.enemy_configs.get("E")
        ):
            state.e_spawn_elapsed += delta_time
            if state.e_spawn_elapsed >= state.e_spawn_interval:
                state.e_spawn_elapsed = 0.0
                create_enemy(
                    world,
                    state.enemy_configs["E"],
                    center,
                    "E",
                )


def system_obstacle_motion(world: esper.World, delta_time: float) -> None:
    del delta_time
    rocks = [
        (entity, transform, hitbox)
        for entity, (_, transform, hitbox, obstacle) in world.get_components(
            CTagObstacle, CTransform, CHitBox, CObstacleState
        )
        if obstacle.kind == "rock"
    ]
    for _, (_, base_transform, base_hitbox) in world.get_components(
        CTagBase, CTransform, CHitBox
    ):
        base_rect = _rect(base_transform, base_hitbox)
        for entity, transform, hitbox in rocks:
            if not world.entity_exists(entity):
                continue
            if _rect(transform, hitbox).colliderect(base_rect):
                _resolve_solid_collision(
                    world,
                    entity,
                    transform,
                    hitbox,
                    base_transform,
                    base_hitbox,
                )


def system_combat_collisions(
    world: esper.World,
    explosion_config: dict | None = None,
    world_size: pygame.Vector2 | None = None,
) -> None:
    destroyed: set[int] = set()
    bullets = list(world.get_components(CTagBullet, CTransform, CHitBox))
    enemy_bullets = list(
        world.get_components(CTagEnemyBullet, CTransform, CHitBox)
    )
    enemies = list(
        world.get_components(
            CTagEnemy, CTransform, CHitBox, CCombatStats
        )
    )
    players = list(
        world.get_components(CTagPlayer, CTransform, CHitBox, CPlayer)
    )
    turrets = list(
        world.get_components(
            CTagTurret, CTransform, CHitBox, CCombatStats
        )
    )
    bases = list(
        world.get_components(
            CTagBase, CTransform, CHitBox, CCombatStats, CBaseState
        )
    )
    obstacles = list(
        world.get_components(
            CTagObstacle, CTransform, CHitBox, CObstacleState
        )
    )

    for bullet_id, (_, bullet_transform, bullet_hitbox) in bullets:
        if not world.entity_exists(bullet_id):
            continue
        bullet_rect = _rect(bullet_transform, bullet_hitbox)
        hit = False
        for target_list in (enemies, turrets):
            for target_id, components in target_list:
                _, target_transform, target_hitbox, stats = components
                if target_id in destroyed or not _overlaps(bullet_rect, target_transform, target_hitbox, world_size):
                    continue
                if _damage(
                    world, target_id, stats, 1, bullet_rect.center,
                    explosion_config, destroyed
                ):
                    _score(world, stats.score)
                world.delete_entity(bullet_id)
                destroyed.add(bullet_id)
                hit = True
                break
            if hit:
                break
        if hit:
            continue

        for base_id, components in bases:
            _, base_transform, base_hitbox, stats, state = components
            if base_id in destroyed or not _overlaps(bullet_rect, base_transform, base_hitbox, world_size):
                continue
            if state.core_open and _damage(
                world, base_id, stats, stats.health, bullet_rect.center,
                explosion_config, destroyed
            ):
                _score(world, stats.score)
            world.delete_entity(bullet_id)
            destroyed.add(bullet_id)
            hit = True
            break
        if hit:
            continue
        for obstacle_id, components in obstacles:
            _, transform, hitbox, obstacle = components
            if obstacle_id in destroyed or not _overlaps(bullet_rect, transform, hitbox, world_size):
                continue
            if obstacle.destructible:
                stats = world.try_component(obstacle_id, CCombatStats)
                if stats:
                    if _damage(
                        world, obstacle_id, stats, stats.health, bullet_rect.center,
                        explosion_config, destroyed
                    ):
                        _score(world, obstacle.score)
                else:
                    _destroy(world, obstacle_id, bullet_rect.center, explosion_config, destroyed)
                    _score(world, obstacle.score)
            world.delete_entity(bullet_id)
            destroyed.add(bullet_id)
            break

    for bullet_id, (_, bullet_transform, bullet_hitbox) in enemy_bullets:
        if bullet_id in destroyed or not world.entity_exists(bullet_id):
            continue
        for player_id, (_, player_transform, player_hitbox, _) in players:
            if player_id in destroyed or not _overlaps(_rect(bullet_transform, bullet_hitbox), player_transform, player_hitbox, world_size):
                continue
            _hurt_player(
                world, player_id, player_transform, explosion_config,
                bullet_transform.pos, destroyed
            )
            world.delete_entity(bullet_id)
            destroyed.add(bullet_id)
            break
        if bullet_id in destroyed:
            continue
        for obstacle_id, (_, transform, hitbox, obstacle) in obstacles:
            if obstacle_id in destroyed or not _overlaps(
                _rect(bullet_transform, bullet_hitbox), transform, hitbox,
                world_size
            ):
                continue
            if obstacle.destructible:
                stats = world.try_component(obstacle_id, CCombatStats)
                if stats:
                    _damage(
                        world,
                        obstacle_id,
                        stats,
                        stats.health,
                        _rect(transform, hitbox).center,
                        explosion_config,
                        destroyed,
                    )
                else:
                    _destroy(
                        world,
                        obstacle_id,
                        _rect(transform, hitbox).center,
                        explosion_config,
                        destroyed,
                    )
            world.delete_entity(bullet_id)
            destroyed.add(bullet_id)
            break

    for enemy_id, (_, enemy_transform, enemy_hitbox, _) in enemies:
        if enemy_id in destroyed or not world.entity_exists(enemy_id):
            continue
        for player_id, (_, player_transform, player_hitbox, _) in players:
            if player_id in destroyed or not _overlaps(_rect(enemy_transform, enemy_hitbox), player_transform, player_hitbox, world_size):
                continue
            _hurt_player(
                world, player_id, player_transform, explosion_config,
                enemy_transform.pos, destroyed
            )
            _destroy(world, enemy_id, _rect(enemy_transform, enemy_hitbox).center, explosion_config, destroyed)
            break

    for player_id, (_, player_transform, player_hitbox, _) in players:
        if player_id in destroyed:
            continue
        for target_id, (_, transform, hitbox, *_) in (*bases, *turrets):
            if target_id not in destroyed and _overlaps(
                _rect(player_transform, player_hitbox), transform, hitbox,
                world_size
            ):
                _hurt_player(
                    world, player_id, player_transform, explosion_config,
                    transform.pos, destroyed
                )
                break

    for player_id, (_, player_transform, player_hitbox, _) in players:
        if player_id in destroyed:
            continue
        for obstacle_id, (_, transform, hitbox, obstacle) in obstacles:
            if obstacle_id in destroyed or not _overlaps(_rect(player_transform, player_hitbox), transform, hitbox, world_size):
                continue
            if obstacle.lethal:
                _hurt_player(
                    world, player_id, player_transform, explosion_config,
                    transform.pos, destroyed
                )
                if obstacle.destructible:
                    _destroy(world, obstacle_id, _rect(transform, hitbox).center, explosion_config, destroyed)
                    _score(world, obstacle.score)
                break
            _resolve_solid_collision(
                world, player_id, player_transform, player_hitbox, transform, hitbox
            )

    for enemy_id, (_, enemy_transform, enemy_hitbox, _) in enemies:
        if enemy_id in destroyed:
            continue
        for obstacle_id, (_, transform, hitbox, obstacle) in obstacles:
            if obstacle_id in destroyed or obstacle.lethal or not _overlaps(
                _rect(enemy_transform, enemy_hitbox), transform, hitbox,
                world_size
            ):
                continue
            _resolve_solid_collision(
                world, enemy_id, enemy_transform, enemy_hitbox, transform, hitbox
            )
        for base_id, (_, transform, hitbox, _, _) in bases:
            if base_id not in destroyed and _overlaps(
                _rect(enemy_transform, enemy_hitbox), transform, hitbox,
                world_size
            ):
                velocity = world.try_component(enemy_id, CVelocity)
                if velocity:
                    velocity.vel *= -1

    for first_id, (_, first_transform, first_hitbox) in bullets:
        if first_id in destroyed:
            continue
        for second_id, (_, second_transform, second_hitbox) in enemy_bullets:
            if second_id in destroyed:
                continue
            if _overlaps(_rect(first_transform, first_hitbox), second_transform, second_hitbox, world_size):
                world.delete_entity(first_id)
                world.delete_entity(second_id)
                destroyed.update((first_id, second_id))
                break


def _rect(transform: CTransform, hitbox: CHitBox) -> pygame.Rect:
    return hitbox.rect_at(transform.pos)


def _overlaps(
    rect: pygame.Rect,
    transform: CTransform,
    hitbox: CHitBox,
    world_size: pygame.Vector2 | None = None,
) -> bool:
    target_rect = _rect(transform, hitbox)
    if world_size is None:
        return rect.colliderect(target_rect)
    return any(
        rect.colliderect(
            target_rect.move(offset_x, offset_y)
        )
        for offset_x in (-world_size.x, 0, world_size.x)
        for offset_y in (-world_size.y, 0, world_size.y)
    )


def _score(world: esper.World, points: int) -> None:
    score = next(iter(world.get_components(CScore)), None)
    if score and points:
        score[1][0].points += points
        player = next(iter(world.get_components(CPlayer)), None)
        if player:
            player[1][0].score = score[1][0].points


def _damage(
    world: esper.World,
    entity: int,
    stats: CCombatStats,
    damage: int,
    position,
    explosion_config: dict | None,
    destroyed: set[int],
) -> bool:
    stats.health -= damage
    if stats.health <= 0:
        _destroy(world, entity, position, explosion_config, destroyed)
        if world.try_component(entity, CTagTurret):
            turret = world.try_component(entity, CTurretState)
            if turret:
                base = world.try_component(turret.base_id, CBaseState)
                if base:
                    base.turret_ids.discard(entity)
                    if not base.turret_ids:
                        base_stats = world.try_component(turret.base_id, CCombatStats)
                        if base_stats:
                            _destroy(world, turret.base_id, position, explosion_config, destroyed)
                            _score(world, base_stats.score)
        return True
    return False


def _destroy(
    world: esper.World,
    entity: int,
    position,
    explosion_config: dict | None,
    destroyed: set[int],
) -> bool:
    if entity in destroyed or not world.entity_exists(entity):
        return False
    obstacle = world.try_component(entity, CObstacleState)
    if obstacle and obstacle.lethal:
        obstacle_transform = world.try_component(entity, CTransform)
        obstacle_hitbox = world.try_component(entity, CHitBox)
        if obstacle_transform and obstacle_hitbox:
            center = pygame.Vector2(
                _rect(obstacle_transform, obstacle_hitbox).center
            )
            for player_id, (_, player_transform, player_hitbox, _) in list(
                world.get_components(
                    CTagPlayer, CTransform, CHitBox, CPlayer
                )
            ):
                if pygame.Vector2(
                    _rect(player_transform, player_hitbox).center
                ).distance_to(center) <= obstacle.blast_radius:
                    _hurt_player(
                        world,
                        player_id,
                        player_transform,
                        explosion_config,
                        center,
                        destroyed,
                    )
    base = world.try_component(entity, CBaseState)
    if base:
        if base.core_entity is not None and world.entity_exists(base.core_entity):
            world.delete_entity(base.core_entity)
            destroyed.add(base.core_entity)
        for turret_id in list(base.turret_ids):
            if world.entity_exists(turret_id):
                world.delete_entity(turret_id)
                destroyed.add(turret_id)
    _explode(world, pygame.Vector2(position), explosion_config)
    world.delete_entity(entity)
    destroyed.add(entity)
    return True


def _resolve_solid_collision(
    world: esper.World,
    entity: int,
    transform: CTransform,
    hitbox: CHitBox,
    other_transform: CTransform,
    other_hitbox: CHitBox,
) -> None:
    rect = _rect(transform, hitbox)
    other_rect = _rect(other_transform, other_hitbox)
    overlap_x = min(rect.right - other_rect.left, other_rect.right - rect.left)
    overlap_y = min(rect.bottom - other_rect.top, other_rect.bottom - rect.top)
    velocity = world.try_component(entity, CVelocity)
    if overlap_x < overlap_y:
        direction = -1 if rect.centerx < other_rect.centerx else 1
        transform.pos.x += direction * overlap_x
        if velocity:
            velocity.vel.x = -velocity.vel.x
    else:
        direction = -1 if rect.centery < other_rect.centery else 1
        transform.pos.y += direction * overlap_y
        if velocity:
            velocity.vel.y = -velocity.vel.y


def _hurt_player(
    world: esper.World,
    player_id: int,
    player_transform: CTransform,
    explosion_config: dict | None,
    position,
    destroyed: set[int] | None = None,
) -> None:
    if destroyed is not None and player_id in destroyed:
        return
    _explode(world, pygame.Vector2(position), explosion_config)
    player = world.try_component(player_id, CPlayer)
    if player:
        player.lives = max(0, player.lives - 1)
        if player.lives == 0:
            player.dead = True
        if player.spawn_position is not None:
            player_transform.pos.update(player.spawn_position)
        velocity = world.try_component(player_id, CVelocity)
        if velocity:
            velocity.vel.update(0, 0)
        for other_id, (hunter, hunter_transform, hunter_velocity) in list(
            world.get_components(CHunter, CTransform, CVelocity)
        ):
            if other_id != player_id:
                hunter_transform.pos.update(hunter.origin)
                hunter_velocity.vel.update(0, 0)
                hunter.returning = False
                hunter.paused_until_player_moves_away = True
        if destroyed is not None:
            destroyed.add(player_id)
