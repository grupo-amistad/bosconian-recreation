import esper
from src.ecs.components.c_animation import CAnimation
from src.ecs.components.c_surface import CSurface


def system_animation(world: esper.World, dt: float):
    for entity, (anim, surface) in list(world.get_components(CAnimation, CSurface)):
        if anim.finished:
            continue
        current = anim.animations[anim.current]
        anim.elapsed += dt
        step = 1.0 / current.framerate
        while anim.elapsed >= step:
            anim.elapsed -= step
            if anim.frame >= current.end:
                if anim.destroy_on_finish or not anim.loop:
                    if anim.destroy_on_finish:
                        anim.finished = True
                        world.delete_entity(entity)
                        break
                    anim.finished = True
                    break
                anim.frame = current.start
            else:
                anim.frame += 1
        if world.entity_exists(entity) and not anim.finished:
            width = surface.surf.get_width() // anim.frames
            surface.area = surface.surf.get_rect(x=anim.frame * width, width=width)
