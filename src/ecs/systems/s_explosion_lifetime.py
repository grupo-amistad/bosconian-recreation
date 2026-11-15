import esper
from src.ecs.components.c_explosion_lifetime import CExplosionLifetime


def system_explosion_lifetime(world: esper.World, delta_time: float) -> None:
    for entity, (lifetime,) in list(world.get_components(CExplosionLifetime)):
        lifetime.elapsed += max(0.0, delta_time)
        if lifetime.elapsed >= lifetime.duration:
            world.delete_entity(entity)
