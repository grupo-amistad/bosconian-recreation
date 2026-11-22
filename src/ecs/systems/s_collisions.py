import esper
import pygame
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_tag_explosion import CTagExplosion
from src.ecs.components.c_animation import Animation, CAnimation
from src.ecs.components.c_explosion_lifetime import CExplosionLifetime
from src.services import ServiceLocator
from src.ecs.components.c_world_entity import CWorldEntity


def _explode(world, position, config=None):
    config = config or {}
    image = config.get("image")
    animation_config = config.get("animations", {})
    frames = animation_config.get("number_frames", config.get("frames", 1))
    animation_list = animation_config.get("list", [])
    animation_data = animation_list[0] if animation_list else config.get(
        "animation", {"name": "EXPLODE", "start": 0, "end": 0, "framerate": 8}
    )
    surf = CSurface(
        image=image,
        size=pygame.Vector2(8, 8),
        color=pygame.Color("orange"),
        frames=frames,
    )
    # Never slice a sprite sheet into more frames than its width supports.
    if image:
        # Make the impact readable at the game's current display scale.
        surf.surf = pygame.transform.scale_by(surf.surf, 2)
        frames = max(1, min(frames, surf.surf.get_width()))
    if image:
        frame_width = surf.surf.get_width() // frames
        surf.area = pygame.Rect(0, 0, frame_width, surf.surf.get_height())
    entity = world.create_entity()
    world.add_component(entity, surf)
    world.add_component(entity, CWorldEntity())
    frame_width = surf.surf.get_width() // frames
    world.add_component(entity, CTransform(pygame.Vector2(position) - pygame.Vector2(frame_width, surf.surf.get_height()) / 2))
    world.add_component(entity, CTagExplosion())
    # The lifetime timer is the final cleanup guard; the animation itself stops
    # on its last frame and cannot loop forever.
    anim = CAnimation(
        frames,
        [Animation(animation_data["name"], animation_data["start"], animation_data["end"], animation_data["framerate"])],
        animation_data["name"],
        True,
        False,
    )
    world.add_component(entity, anim)
    world.add_component(entity, CExplosionLifetime(
        (animation_data["end"] - animation_data["start"] + 1) / animation_data["framerate"]
    ))
    sound_path = config.get("sound")
    if sound_path:
        ServiceLocator.sounds.load(sound_path).play()
