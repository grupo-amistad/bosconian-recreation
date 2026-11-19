import asyncio
from pathlib import Path
import pygame
import esper

from src.ecs.components.c_enemy_spawner import CEnemySpawner
from src.ecs.components.c_input_command import CInputCommand
from src.ecs.components.c_player import CPlayer
from src.create.prefab_creator import create_player
from src.ecs.systems.s_boundaries import (
    system_bullet_boundary,
    system_player_boundary,
)
from src.ecs.systems.s_collisions import (
    system_bullet_enemy_collision,
    system_player_enemy_collision,
)
from src.ecs.systems.s_input import system_input
from src.ecs.systems.s_player import system_player_input
from src.ecs.systems.s_movement import system_movement
from src.ecs.systems.s_rendering import system_rendering
from src.ecs.systems.s_screen_bounce import system_screen_bounce
from src.ecs.systems.s_enemy_spawner import system_enemy_spawner
from src.create.prefab_creator import animations_from_config, animation_frame_count
from src.ecs.systems.s_animation import system_animation
from src.ecs.systems.s_hunter import system_hunter, system_moving_animation
from src.ecs.systems.s_explosion_lifetime import system_explosion_lifetime
from src.ecs.systems.s_special_ability import system_special_ability
from src.ecs.systems.s_text import system_text_rendering
from src.ecs.components.c_text import CText
from src.ecs.components.c_special_ability import CSpecialAbility
from src.services import ServiceLocator
from src.engine.gameplay_scene import GameplayScene
from src.engine.scene_manager import SceneManager

class GameEngine:
    def __init__(self) -> None:
        ServiceLocator.initialize(Path(__file__).resolve().parents[2])
        self._load_config_files()

        pygame.init()
        pygame.display.set_caption(self.window_cfg["title"])
        self.screen = pygame.display.set_mode(
            (self.window_cfg["size"]["w"], self.window_cfg["size"]["h"]), 
            0)

        self.clock = pygame.time.Clock()
        self.is_running = False
        self.framerate = self.window_cfg["framerate"]
        self.delta_time = 0
        self.bg_color = pygame.Color(self.window_cfg["bg_color"]["r"],
                                     self.window_cfg["bg_color"]["g"],
                                     self.window_cfg["bg_color"]["b"])
        self.ecs_world = esper.World()
        self.events: list[pygame.event.Event] = []
        self.paused = False
        self.ui_entities: dict[str, int] = {}
        self.scene_manager = SceneManager()

        # Original framerate = 0
        # Original bg_color (0, 200, 128)

    def _load_config_files(self):
        self.window_cfg = ServiceLocator.configs.load("assets/cfg/window.json")

    def _load_config_file(self, path: str) -> dict:
        return ServiceLocator.configs.load(path)

    async def run(self) -> None:
        self._create()
        self.scene_manager.start(GameplayScene(self))
        self.is_running = True
        while self.is_running:
            self._calculate_time()
            self._process_events()
            self.scene_manager.update(self.delta_time)
            self.scene_manager.draw(self.screen)
            pygame.display.flip()
            await asyncio.sleep(0)
        self._clean()

    def _create(self):
        level_config = self._load_config_file("assets/cfg/levels/level_01.json")
        enemies_config = self._load_config_file("assets/cfg/enemies.json")
        player_config = self._load_config_file("assets/cfg/player.json")
        bullet_config = self._load_config_file("assets/cfg/bullet.json")
        self.explosion_config = self._load_config_file("assets/cfg/explosion.json")

        player_spawn = level_config["player_spawn"]
        player_image = player_config.get("image")
        player_entity = create_player(
            self.ecs_world,
            pygame.Vector2(player_config.get("size", {}).get("x", 32), player_config.get("size", {}).get("y", 32)),
            pygame.Vector2(
                player_spawn["position"]["x"],
                player_spawn["position"]["y"],
            ),
            pygame.Vector2(0, 0),
            pygame.Color(*[player_config.get("color", {"r":255,"g":255,"b":255})[k] for k in ("r","g","b")]),
            image=player_image,
            animations=animations_from_config(player_config),
            frames=animation_frame_count(player_config),
        )
        self.ecs_world.add_component(
            player_entity,
            CPlayer(
                player_config["input_velocity"],
                bullet_config,
                player_spawn["max_bullets"],
                pygame.Vector2(player_spawn["position"]["x"], player_spawn["position"]["y"]),
            ),
        )
        player = self.ecs_world.component_for_entity(player_entity, CPlayer)
        player.move_sound = ServiceLocator.sounds.load(player_config.get("sound_move", "snd/laser.ogg"))
        self.ecs_world.add_component(player_entity, CSpecialAbility())

        input_commands = (
            ("PLAYER_LEFT", pygame.K_LEFT),
            ("PLAYER_RIGHT", pygame.K_RIGHT),
            ("PLAYER_UP", pygame.K_UP),
            ("PLAYER_DOWN", pygame.K_DOWN),
        )
        for action, key in input_commands:
            entity = self.ecs_world.create_entity()
            self.ecs_world.add_component(
                entity,
                CInputCommand(action, "keyboard", key),
            )
        fire_entity = self.ecs_world.create_entity()
        self.ecs_world.add_component(
            fire_entity,
            CInputCommand("PLAYER_FIRE", "mouse", pygame.BUTTON_LEFT),
        )
        special_entity = self.ecs_world.create_entity()
        self.ecs_world.add_component(special_entity, CInputCommand("PLAYER_SPECIAL", "keyboard", pygame.K_SPACE))
        pause_entity = self.ecs_world.create_entity()
        self.ecs_world.add_component(pause_entity, CInputCommand("TOGGLE_PAUSE", "keyboard", pygame.K_p))

        spawner_entity = self.ecs_world.create_entity()
        self.ecs_world.add_component(
            spawner_entity,
            CEnemySpawner(
                level_config.get("enemy_spawn_events", []),
                enemies_config,
                level_config.get("dynamic_spawning"),
            ),
        )
        interface = self._load_config_file("assets/cfg/interface.json")
        font = ServiceLocator.fonts.load(interface["font"], interface["size"])
        for key, text, pos, color in (
            ("title", interface["title"], interface["title_position"], interface["title_color"]),
            ("instructions", interface["instructions"], interface["instructions_position"], interface["instructions_color"]),
            ("pause", interface["pause_text"], interface["pause_position"], interface["pause_color"]),
            ("special_label", interface["special_label"], interface["special_position"], interface["special_color"]),
            ("special", "", interface["special_status_position"], interface["special_status_color"]),
        ):
            entity = self.ecs_world.create_entity()
            self.ecs_world.add_component(entity, CText(
                text, font, pygame.Color(*color), pygame.Vector2(*pos)
            ))
            self.ui_entities[key] = entity

    def _calculate_time(self):
        self.clock.tick(self.framerate)
        self.delta_time = self.clock.get_time() / 1000.0
    
    def _process_events(self):
        self.events = pygame.event.get()
        for event in self.events:
            if event.type == pygame.QUIT:
                self.is_running = False
            else:
                self.scene_manager.handle_event(event)

    def _update(self):
        system_input(self.ecs_world, self.events)
        system_special_ability(self.ecs_world, self.delta_time)
        ability = next(iter(self.ecs_world.get_components(CSpecialAbility)), None)
        if ability:
            _, (state,) = ability
            remaining = max(state.cooldown_remaining, 0)
            status = "ACTIVA" if state.active_for > 0 else (
                "100%" if remaining == 0 else f"{remaining:.1f}s"
            )
            self.ecs_world.component_for_entity(self.ui_entities["special"], CText).set_text(status)
        self.ecs_world.component_for_entity(self.ui_entities["pause"], CText).set_text(
            "PAUSADO - presiona P para reanudar" if self.paused else ""
        )
        if self.paused:
            return
        system_player_input(self.ecs_world, self.delta_time)
        system_enemy_spawner(self.ecs_world, self.delta_time)
        system_movement(self.ecs_world, self.delta_time)
        system_hunter(self.ecs_world, self.delta_time)
        system_moving_animation(self.ecs_world)
        system_animation(self.ecs_world, self.delta_time)
        system_explosion_lifetime(self.ecs_world, self.delta_time)
        system_player_boundary(self.ecs_world, self.screen)
        system_bullet_boundary(self.ecs_world, self.screen)
        system_screen_bounce(self.ecs_world, self.screen)
        system_bullet_enemy_collision(self.ecs_world, self.explosion_config)
        system_player_enemy_collision(self.ecs_world, self.explosion_config, self.screen.get_size())
        # Esper queues delete_entity() calls until process() is invoked.
        # Purge them before rendering so destroyed enemies/effects vanish.
        self.ecs_world.process()

    def _draw(self, target=None):
        target = target or self.screen
        target.fill(self.bg_color)
        pygame.draw.rect(target, pygame.Color(180, 180, 180), target.get_rect(), 1)
        system_rendering(self.ecs_world, target)
        system_text_rendering(self.ecs_world, target)

    def _clean(self):
        self.scene_manager.close()
        pygame.quit()

    
