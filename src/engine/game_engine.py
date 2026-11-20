import asyncio
from pathlib import Path

import esper
import pygame

from src.create.prefab_creator import animations_from_config, animation_frame_count, create_player
from src.ecs.components.c_input_command import CInputCommand
from src.ecs.components.c_player import CPlayer
from src.ecs.components.c_special_ability import CSpecialAbility
from src.ecs.components.c_surface import CSurface
from src.ecs.components.c_tag_player import CTagPlayer
from src.ecs.components.c_text import CText
from src.ecs.components.c_transform import CTransform
from src.ecs.components.c_velocity import CVelocity
from src.ecs.systems.s_animation import system_animation
from src.ecs.systems.s_collisions import system_bullet_enemy_collision, system_player_enemy_collision
from src.ecs.systems.s_enemy_spawner import system_enemy_spawner
from src.ecs.systems.s_explosion_lifetime import system_explosion_lifetime
from src.ecs.systems.s_hunter import system_hunter, system_moving_animation
from src.ecs.systems.s_input import system_input
from src.ecs.systems.s_movement import system_movement
from src.ecs.systems.s_player import system_player_input
from src.ecs.systems.s_rendering import system_rendering
from src.ecs.systems.s_special_ability import system_special_ability
from src.ecs.systems.s_text import system_text_rendering
from src.ecs.systems.s_wraparound import system_wraparound
from src.engine.camera import Camera
from src.engine.gameplay_scene import GameplayScene
from src.engine.menu_scenes import ContinueScene, CreditsScene, EndScene, InstructionsScene, PauseScene, TitleScene
from src.engine.scene_manager import SceneManager
from src.services import ServiceLocator
from src.ui.minimap import MiniMap
from src.world.starfield import Starfield


class GameEngine:
    """Owns Pygame and the single loop shared by every scene."""

    def __init__(self) -> None:
        ServiceLocator.initialize(Path(__file__).resolve().parents[2])
        self.window_cfg = ServiceLocator.configs.load("assets/cfg/window.json")
        pygame.init()
        pygame.display.set_caption(self.window_cfg["title"])
        size = (self.window_cfg["size"]["w"], self.window_cfg["size"]["h"])
        self.screen = pygame.display.set_mode(size)
        self.clock = pygame.time.Clock()
        self.framerate = self.window_cfg["framerate"]
        self.delta_time = 0.0
        self.is_running = False
        self.bg_color = pygame.Color(*[self.window_cfg["bg_color"][key] for key in ("r", "g", "b")])
        self.ecs_world = esper.World()
        self.events = []
        self.scene_manager = SceneManager()
        self.starfield = Starfield(size)
        self.minimap = MiniMap()
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
        dimensions = level_cfg.get("world_size", self.window_cfg["size"])
        self.world_size = pygame.Vector2(dimensions["w"], dimensions["h"])
        viewport = pygame.Vector2(self.screen.get_size())
        self.camera = Camera(self.world_size, viewport)
        spawn = level_cfg["player_spawn"]
        spawn_pos = pygame.Vector2(spawn["position"]["x"], spawn["position"]["y"])
        size_data = player_cfg.get("size", {"x": 32, "y": 32})
        color_data = player_cfg.get("color", {"r": 255, "g": 255, "b": 255})
        self.player_entity = create_player(
            self.ecs_world, pygame.Vector2(size_data["x"], size_data["y"]), spawn_pos,
            pygame.Vector2(), pygame.Color(*[color_data[k] for k in ("r", "g", "b")]),
            image=player_cfg.get("image"), animations=animations_from_config(player_cfg),
            frames=animation_frame_count(player_cfg),
        )
        player = CPlayer(player_cfg["input_velocity"], bullet_cfg, spawn["max_bullets"], spawn_pos)
        player.lives = lives
        self._last_lives = lives
        player.score = self.score if keep_score else 0
        player.move_sound = ServiceLocator.sounds.load(player_cfg.get("sound_move", "snd/laser.ogg"))
        self.ecs_world.add_component(self.player_entity, player)
        self.ecs_world.add_component(self.player_entity, CSpecialAbility())

        for action, key in (("PLAYER_LEFT", pygame.K_LEFT), ("PLAYER_RIGHT", pygame.K_RIGHT),
                            ("PLAYER_UP", pygame.K_UP), ("PLAYER_DOWN", pygame.K_DOWN),
                            ("PLAYER_SPECIAL", pygame.K_SPACE)):
            entity = self.ecs_world.create_entity()
            self.ecs_world.add_component(entity, CInputCommand(action, "keyboard", key))
        fire = self.ecs_world.create_entity()
        self.ecs_world.add_component(fire, CInputCommand("PLAYER_FIRE", "mouse", pygame.BUTTON_LEFT))
        spawner = self.ecs_world.create_entity()
        from src.ecs.components.c_enemy_spawner import CEnemySpawner
        self.ecs_world.add_component(spawner, CEnemySpawner(
            level_cfg.get("enemy_spawn_events", []), enemies_cfg, level_cfg.get("dynamic_spawning")))

        self.ui_entities = {}
        interface = self._load_config_file("assets/cfg/interface.json")
        font = ServiceLocator.fonts.load(interface["font"], interface["size"])
        for name, pos in (("hud", (5, 5)), ("special", (5, 17))):
            entity = self.ecs_world.create_entity()
            self.ecs_world.add_component(entity, CText("", font, pygame.Color("white"), pygame.Vector2(pos)))
            self.ui_entities[name] = entity
        self.play_music("assets/mus/confrontation.ogg")
        self.scene_manager.request_change(GameplayScene(self))

    def new_game(self):
        self.level = 1
        self.score = 0
        self.lives_lost = 0
        self.continues_used = 0
        self.start_game(lives=4, keep_score=False)

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
        system_special_ability(self.ecs_world, self.delta_time, self.world_size)
        player = self.current_player()
        if player is None:
            return
        system_player_input(self.ecs_world, self.delta_time, self.camera, self.world_size)
        system_enemy_spawner(self.ecs_world, self.delta_time)
        system_movement(self.ecs_world, self.delta_time)
        system_wraparound(self.ecs_world, self.world_size)
        system_hunter(self.ecs_world, self.delta_time, self.world_size)
        system_moving_animation(self.ecs_world)
        system_animation(self.ecs_world, self.delta_time)
        system_explosion_lifetime(self.ecs_world, self.delta_time)
        system_bullet_enemy_collision(self.ecs_world, self.explosion_config, self.world_size)
        system_player_enemy_collision(self.ecs_world, self.explosion_config, world_size=self.world_size)
        self.ecs_world.process()
        player = self.current_player()
        if player:
            self.lives_lost += max(0, self._last_lives - player.lives)
            self._last_lives = player.lives
            self.score = player.score
            self.camera.follow(self.player_position())
            self.starfield.update(self.delta_time, self.camera.delta)
            self.ecs_world.component_for_entity(self.ui_entities["hud"], CText).set_text(
                f"P{self.score:06d}  VIDAS {player.lives}  NIVEL {self.level}")
            ability = self.ecs_world.try_component(self.player_entity, CSpecialAbility)
            status = "LISTA" if ability and ability.cooldown_remaining <= 0 else "RECARGA"
            self.ecs_world.component_for_entity(self.ui_entities["special"], CText).set_text(f"ESPECIAL {status}")
            if player.dead:
                self.stop_music()
                self.scene_manager.request_change(ContinueScene(self))

    def player_position(self):
        transform = self.ecs_world.try_component(self.player_entity, CTransform)
        surface = self.ecs_world.try_component(self.player_entity, CSurface)
        if transform is None:
            return pygame.Vector2()
        return transform.pos + (pygame.Vector2(surface.size) / 2 if surface else pygame.Vector2())

    def _draw(self, target=None):
        target = target or self.screen
        target.fill(self.bg_color)
        self.starfield.draw(target)
        system_rendering(self.ecs_world, target, self.camera)
        system_text_rendering(self.ecs_world, target)
        player_pos = self.player_position()
        self.minimap.draw(target, self.ecs_world, self.world_size, player_pos)

    def pause(self, gameplay_scene):
        self.pause_music()
        self.scene_manager.request_change(PauseScene(self, gameplay_scene))

    def play_music(self, path):
        if pygame.mixer.get_init():
            try:
                pygame.mixer.music.load(ServiceLocator.sounds._resolve(path))
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
