import asyncio
from pathlib import Path

import esper
import pygame

from src.create.prefab_creator import (
    animations_from_config,
    animation_frame_count,
    create_base,
    create_obstacle,
    create_player,
)

from src.ecs.components.c_alert import CAlert
from src.ecs.systems.s_alert import system_alert
from src.ecs.systems.s_score import system_score
from src.ui.alert_system import AlertController
from src.ui.hud import HUD
from src.ui.score import ScoreManager
from src.ecs.components.c_input_command import CInputCommand
from src.ecs.components.c_player import CPlayer
from src.ecs.components.c_combat import CScore
from src.ecs.components.c_special_ability import CSpecialAbility
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.components.c_text import CText
from src.ecs.systems.s_animation import system_animation
from src.ecs.systems.s_bullet_lifetime import system_bullet_lifetime
from src.ecs.systems.s_combat import (
    system_base_behavior,
    system_combat_collisions,
    system_enemy_behavior,
    system_obstacle_motion,
)
from src.ecs.systems.s_enemy_spawner import system_enemy_spawner
from src.ecs.systems.s_explosion_lifetime import system_explosion_lifetime
from src.ecs.systems.s_hunter import system_hunter, system_moving_animation
from src.ecs.systems.s_input import system_input
from src.ecs.systems.s_movement import system_movement
from src.ecs.systems.s_player import system_player_input
from src.ecs.systems.s_rendering import system_rendering
from src.ecs.systems.s_special_ability import system_special_ability
from src.ecs.systems.s_wraparound import system_wraparound
from src.engine.camera import Camera
from src.engine.gameplay_scene import GameplayScene
from src.engine.menu_scenes import ContinueScene, CreditsScene, EndScene, InstructionsScene, PauseScene, TitleScene
from src.engine.scene_manager import SceneManager
from src.services import ServiceLocator
from src.ui.minimap import MiniMap
from src.world.starfield import Starfield
from src.ecs.components.c_enemy_spawner import CEnemySpawner
from src.ecs.systems.s_player_life import system_player_life
from src.ecs.systems.s_player_movement import system_player_movement
from src.ecs.systems.s_player_shooting import (
    system_player_bullet_bounds,
    system_player_shooting,
    system_player_special,
)
from src.ecs.systems.s_sprite_rotation import system_sprite_rotation
from src.player.player_commands import create_player_input_bindings, system_player_commands
from src.player.player_config import PlayerConfig
from src.player.player_factory import create_player_entity


class GameEngine:
    """Owns Pygame and the single loop shared by every scene."""

    def __init__(self) -> None:
        ServiceLocator.initialize(Path(__file__).resolve().parents[2])
        self.window_cfg = ServiceLocator.configs.load("assets/cfg/window.json")
        pygame.init()
        self.audio_config = ServiceLocator.configs.load("assets/cfg/audio.json")
        ServiceLocator.sounds.set_volume(
            self.audio_config.get("volumes", {}).get("sfx", 0.7)
        )
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(
                self.audio_config.get("volumes", {}).get("music", 0.5)
            )
        pygame.display.set_caption(self.window_cfg["title"])
        size = (self.window_cfg["size"]["w"], self.window_cfg["size"]["h"])
        self.playfield_width = max(1, size[0] - 80)
        self.screen = pygame.display.set_mode(size)
        self.clock = pygame.time.Clock()
        self.framerate = self.window_cfg["framerate"]
        self.delta_time = 0.0
        self.is_running = False
        self.bg_color = pygame.Color(*[self.window_cfg["bg_color"][key] for key in ("r", "g", "b")])
        self.ecs_world = esper.World()
        self.events = []
        self.scene_manager = SceneManager()
        self.starfield = Starfield((self.playfield_width, size[1]))
        self.minimap = MiniMap()
        self.hud_font = None
        self.title_scene = TitleScene(self)
        self.level = 1
        self.score = 0
        self.lives_lost = 0
        self.continues_used = 0
        self.explosion_config = {}
        self.ui_entities = {}
        self.camera = None
        self.world_size = pygame.Vector2(size)
        self.player_entity = None
        self._last_lives = 4
        save_path = Path(__file__).resolve().parents[2] / "save" / "highscore.json"
        self.score_manager = ScoreManager(save_path=save_path)
        self.alert_controller = AlertController()
        self.hud = HUD(panel_width=80)

    def draw_lines(self, target, lines, y):
        font = ServiceLocator.fonts.load("fnt/PressStart2P.ttf", 7)
        for line in lines:
            surface = font.render(line, False, (235, 235, 255))
            target.blit(surface, ((target.get_width() - surface.get_width()) // 2, y))
            y += 16

    async def run(self) -> None:
        self.scene_manager.start(self.title_scene)
        self.is_running = True
        while self.is_running:
            self.delta_time = self.clock.tick(self.framerate) / 1000.0
            self.events = pygame.event.get()
            for event in self.events:
                if event.type == pygame.QUIT:
                    self.is_running = False
                else:
                    self.scene_manager.handle_event(event)
            self.scene_manager.update(self.delta_time)
            self.scene_manager.draw(self.screen)
            pygame.display.flip()
            await asyncio.sleep(0)
        self.scene_manager.close()
        pygame.quit()

    def _load_config_file(self, path: str) -> dict:
        return ServiceLocator.configs.load(path)

    def start_game(self, lives=4, keep_score=True):
        self.stop_music()
        self.ecs_world = esper.World()
        level_path = f"assets/cfg/levels/level_{self.level:02d}.json"
        level_cfg = self._load_config_file(level_path)
        enemies_cfg = self._load_config_file("assets/cfg/enemies.json")
        player_cfg = self._load_config_file("assets/cfg/player.json")
        bullet_cfg = self._load_config_file("assets/cfg/bullet.json")
        self.explosion_config = self._load_config_file("assets/cfg/explosion.json")
        base_configs = self._load_config_file("assets/cfg/bases.json")
        obstacle_configs = self._load_config_file("assets/cfg/obstacles.json")
        dimensions = level_cfg.get("world_size", self.window_cfg["size"])
        self.world_size = pygame.Vector2(dimensions["w"], dimensions["h"])
        viewport = pygame.Vector2(self.playfield_width, self.screen.get_height())
        self.camera = Camera(self.world_size, viewport)
        spawn = level_cfg["player_spawn"]
        spawn_pos = pygame.Vector2(spawn["position"]["x"], spawn["position"]["y"])
        player_config = PlayerConfig.from_dicts(player_cfg, bullet_cfg, spawn)
        self.player_entity = create_player_entity(
            self.ecs_world,
            player_config,
            spawn_pos,
            lives=lives,
            score=self.score if keep_score else 0,
        )
        self._last_lives = lives
        create_player_input_bindings(self.ecs_world, player_config.controls)
        spawner = self.ecs_world.create_entity()
        self.ecs_world.add_component(spawner, CEnemySpawner(
            level_cfg.get("enemy_spawn_events", []), enemies_cfg, level_cfg.get("dynamic_spawning")))
        
        alert_ent = self.ecs_world.create_entity()
        c_alert = CAlert(red_threshold=float(level_cfg.get("alert_red_time", 90.0)))
        self.alert_controller.reset(c_alert, red_threshold=c_alert.red_threshold)
        self.ecs_world.add_component(alert_ent, c_alert)

        for base_entry in level_cfg.get("bases", []):
            base_type = base_entry.get("type", "default")
            if base_type not in base_configs:
                raise ValueError(f"Unknown base type: {base_type}")
            config = {**base_configs[base_type], **base_entry}
            position = config.get("position", {})
            create_base(
                self.ecs_world,
                config,
                pygame.Vector2(position["x"], position["y"]),
                level_cfg.get("level", self.level),
                enemies_cfg,
            )
        for obstacle_entry in level_cfg.get("obstacles", []):
            obstacle_type = obstacle_entry.get("type")
            if obstacle_type not in obstacle_configs:
                raise ValueError(f"Unknown obstacle type: {obstacle_type}")
            config = {**obstacle_configs[obstacle_type], **obstacle_entry}
            position = config.get("position", {})
            create_obstacle(
                self.ecs_world,
                config,
                pygame.Vector2(position["x"], position["y"]),
            )
        interface = self._load_config_file("assets/cfg/interface.json")
        self.hud_font = ServiceLocator.fonts.load(interface["font"], 5)
        self.play_music(
            level_cfg.get(
                "music",
                self.audio_config.get("music", {}).get("default_level"),
            )
        )
        self.scene_manager.request_change(GameplayScene(self))

    def new_game(self):
        self.level = 1
        self.score = 0
        self.lives_lost = 0
        self.continues_used = 0
        self.start_game(lives=4, keep_score=False)
        self.score_manager.reset_for_new_game()
        lives = self.score_manager.initial_lives

    def complete_level(self):
        if self.level >= 10:
            self.stop_music()
            self.scene_manager.request_change(EndScene(self, True))
            return
        self.level += 1
        self.start_game(lives=self.current_player().lives if self.current_player() else 4)

    def current_player(self):
        if self.player_entity is None or not self.ecs_world.entity_exists(self.player_entity):
            return None
        return self.ecs_world.try_component(self.player_entity, CPlayer)

    def _update(self):
        system_input(self.ecs_world, self.events)
        system_player_commands(self.ecs_world)
        player = self.current_player()
        if player is None:
            return
        system_player_life(self.ecs_world, self.delta_time, self.explosion_config)
        system_player_movement(self.ecs_world, self.delta_time)
        system_player_shooting(self.ecs_world, self.delta_time)
        system_player_special(self.ecs_world, self.delta_time)
        system_enemy_spawner(self.ecs_world, self.delta_time)
        system_base_behavior(
            self.ecs_world, self.delta_time, self.world_size
        )
        system_enemy_behavior(
            self.ecs_world, self.delta_time, self.world_size
        )
        system_movement(self.ecs_world, self.delta_time)
        system_wraparound(self.ecs_world, self.world_size)
        system_hunter(self.ecs_world, self.delta_time, self.world_size)
        system_obstacle_motion(self.ecs_world, self.delta_time)
        system_moving_animation(self.ecs_world)
        system_sprite_rotation(self.ecs_world)
        system_player_bullet_bounds(self.ecs_world, self.camera)
        system_animation(self.ecs_world, self.delta_time)
        system_explosion_lifetime(self.ecs_world, self.delta_time)
        system_combat_collisions(
            self.ecs_world, self.explosion_config, self.world_size
        )
        system_bullet_lifetime(self.ecs_world, self.delta_time)
        self.ecs_world.process()
        player = self.current_player()
        if player:
            self.lives_lost += max(0, self._last_lives - player.lives)
            self._last_lives = player.lives
            self.score = player.score
            score_state = self.ecs_world.try_component(
                self.player_entity, CScore
            )
            if score_state:
                score_state.points = player.score
            self.camera.follow(self.player_position())
            self.starfield.update(self.delta_time, self.camera.delta)
            if player.dead:
                self.stop_music()
                self.scene_manager.request_change(ContinueScene(self))
            
        system_score(self.ecs_world, self.score_manager)
        system_alert(self.ecs_world, self.delta_time, self.alert_controller)

    def player_position(self):
        transform = self.ecs_world.try_component(self.player_entity, CTransform)
        player = self.ecs_world.try_component(self.player_entity, CPlayer)
        if transform is None:
            return pygame.Vector2()
        return transform.pos + (player.size / 2 if player else pygame.Vector2())

    def _draw(self, target=None):
        target = target or self.screen
        target.fill(self.bg_color)
        self.starfield.draw(target)
        system_rendering(self.ecs_world, target, self.camera)
        self.hud.draw(target,
            self.ecs_world,
            self.world_size,
            self.player_position(),
            self.level,
            self.score_manager,
            self.alert_controller,
            self.player_entity)

    def _draw_hud(self, target):
        panel_x = self.playfield_width
        panel_width = target.get_width() - panel_x
        pygame.draw.rect(target, (0, 0, 0), (panel_x, 0, panel_width, target.get_height()))
        pygame.draw.line(target, (35, 35, 35), (panel_x, 0), (panel_x, target.get_height()))
        font = self.hud_font or ServiceLocator.fonts.load("fnt/PressStart2P.ttf", 5)

        def label(text, x, y, color):
            target.blit(font.render(text, False, color), (x, y))

        coral = (230, 105, 94)
        white = (245, 245, 245)
        label("HI-SCORE", panel_x + 5, 5, coral)
        label("10000", panel_x + 30, 14, white)
        label("SCORE", panel_x + 5, 25, coral)
        current_score = font.render(str(self.score), False, white)
        target.blit(current_score, (target.get_width() - current_score.get_width() - 5, 34))
        pygame.draw.rect(target, (48, 180, 72), (panel_x + 4, 46, panel_width - 8, 15))
        alert = font.render("GREEN", False, (0, 0, 0))
        target.blit(alert, (panel_x + (panel_width - alert.get_width()) // 2, 50))
        player_pos = self.player_position()
        self.minimap.draw(target, self.ecs_world, self.world_size, player_pos)
        player = self.current_player()
        lives = max(0, min(4, player.lives if player else 0))
        for index in range(lives):
            ship = pygame.Surface((10, 12), pygame.SRCALPHA)
            pygame.draw.polygon(ship, white, [(5, 0), (9, 11), (5, 8), (1, 11)])
            target.blit(ship, (panel_x + 8 + index * 15, 163))
        label("ROUND", panel_x + 5, 187, white)
        label(f"{self.level:>2}", target.get_width() - 20, 187, white)

    def pause(self, gameplay_scene):
        self.pause_music()
        self.scene_manager.request_change(PauseScene(self, gameplay_scene))

    def play_music(self, path):
        if path and pygame.mixer.get_init():
            try:
                pygame.mixer.music.load(ServiceLocator.sounds._resolve(path))
                pygame.mixer.music.set_volume(
                    self.audio_config.get("volumes", {}).get("music", 0.5)
                )
                pygame.mixer.music.play(-1)
            except (pygame.error, OSError):
                pass

    @staticmethod
    def pause_music():
        if pygame.mixer.get_init():
            pygame.mixer.pause()
            pygame.mixer.music.pause()

    @staticmethod
    def resume_music():
        if pygame.mixer.get_init():
            pygame.mixer.unpause()
            pygame.mixer.music.unpause()

    @staticmethod
    def stop_music():
        if pygame.mixer.get_init():
            pygame.mixer.stop()
            pygame.mixer.music.stop()

    def _clean(self):
        self.scene_manager.close()
        pygame.quit()
