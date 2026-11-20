import esper

from src.ecs.components.c_bullet_lifetime import CBulletLifetime


def system_bullet_lifetime(world: esper.World, delta_time: float) -> None:
    for entity, (lifetime,) in list(world.get_components(CBulletLifetime)):
        lifetime.elapsed += delta_time
        if lifetime.elapsed >= lifetime.lifetime and world.entity_exists(entity):
            world.delete_entity(entity)
