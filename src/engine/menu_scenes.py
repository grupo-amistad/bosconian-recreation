import pygame
from src.engine.scene import Scene
from src.services import ServiceLocator


def _play_menu_sfx(engine, key: str = "menu_select") -> None:
    if not pygame.get_init() or not pygame.mixer.get_init():
        return
    try:
        path = engine.audio_config.get("sfx", {}).get(key)
        if path:
            ServiceLocator.sounds.load(path).play()
    except Exception:
        pass


def _load_interface_cfg() -> dict:
    try:
        return ServiceLocator.configs.load("assets/cfg/interface.json")
    except Exception:
        return {}


class TextScene(Scene):
    title = ""
    lines: tuple[str, ...] = ()
    music_key = None
    screen_cfg_key: str | None = None

    def __init__(self, engine, return_scene=None) -> None:
        self.engine = engine
        self.return_scene = return_scene or engine.title_scene
        cfg = _load_interface_cfg().get("menus", {}).get(self.screen_cfg_key or "", {})
        if cfg:
            self.title = cfg.get("header", self.title)
            raw_lines = [line for line in cfg.get("lines", []) if line.strip()]
            if raw_lines:
                self.lines = tuple(raw_lines)
            self.back_prompt = cfg.get("back_prompt", "ESC / ENTER: VOLVER")
        else:
            self.back_prompt = "ESC / ENTER: VOLVER"

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            _play_menu_sfx(self.engine, "menu_select")
            self.engine.scene_manager.request_change(self.return_scene)

    def on_enter(self):
        if self.music_key and isinstance(self.return_scene, TitleScene):
            path = self.engine.audio_config.get("music", {}).get(self.music_key)
            self.engine.play_music(path)

    def update(self, delta_time):
        self.engine.starfield.update(delta_time)

    def draw(self, target):
        target.fill((0, 0, 0))
        self.engine.starfield.draw(target)
        font = ServiceLocator.fonts.load("assets/fnt/PressStart2P.ttf", 8)
        y = 14
        header_surf = font.render(self.title, False, (255, 235, 0))
        target.blit(header_surf, ((target.get_width() - header_surf.get_width()) // 2, y))
        y += 20
        for line in self.lines:
            surf = font.render(line, False, (235, 235, 255))
            target.blit(surf, ((target.get_width() - surf.get_width()) // 2, y))
            y += 14
        back_surf = font.render(self.back_prompt, False, (140, 220, 140))
        target.blit(back_surf, ((target.get_width() - back_surf.get_width()) // 2, target.get_height() - 18))


class InstructionsScene(TextScene):
    title = "INSTRUCCIONES"
    lines = (
        "FLECHAS: MOVER NAVE",
        "Z / CLICK: DISPARAR",
        "X / SPACE: ESPECIAL",
        "P: PAUSAR PARTIDA",
        "DESTRUYE TODAS LAS BASES",
    )
    music_key = "instructions"
    screen_cfg_key = "instructions_screen"


class CreditsScene(TextScene):
    title = "CREDITOS"
    lines = (
        "BOSCONIAN RECREATION",
        "PROYECTO FINAL",
        "EQUIPO DE 4 INTEGRANTES",
        "BASADO EN BOSCONIAN (NAMCO)",
    )
    music_key = "credits"
    screen_cfg_key = "credits_screen"


class TitleScene(Scene):
    def __init__(self, engine):
        self.engine = engine
        base = ServiceLocator.images.load("assets/img/Boskonian spacecraft.png")
        mine = ServiceLocator.images.load("assets/img/space mine.png")
        logo = ServiceLocator.images.load("assets/img/titulo.png")
        self.base_sprite = pygame.transform.scale(base, (56, 62))
        self.mine_sprite = pygame.transform.scale(mine, (16, 16))
        self.logo_sprite = pygame.transform.scale(logo, (160, 64))
        self.options = [
            ("play", "JUGAR"),
            ("instructions", "INSTRUCCIONES"),
            ("credits", "CREDITOS"),
            ("quit", "SALIR"),
        ]
        self.selected_idx = 0

    def on_enter(self):
        self.engine.play_music(
            self.engine.audio_config.get("music", {}).get("menu")
        )

    def _activate_option(self, opt_id: str) -> None:
        _play_menu_sfx(self.engine, "menu_select")
        if opt_id == "play":
            self.engine.new_game()
        elif opt_id == "instructions":
            self.engine.scene_manager.request_change(InstructionsScene(self.engine, self))
        elif opt_id == "credits":
            self.engine.scene_manager.request_change(CreditsScene(self.engine, self))
        elif opt_id == "quit":
            self.engine.is_running = False

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_UP:
            self.selected_idx = (self.selected_idx - 1) % len(self.options)
            _play_menu_sfx(self.engine, "menu_select")
        elif event.key == pygame.K_DOWN:
            self.selected_idx = (self.selected_idx + 1) % len(self.options)
            _play_menu_sfx(self.engine, "menu_select")
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._activate_option(self.options[self.selected_idx][0])
        elif event.key == pygame.K_i:
            self._activate_option("instructions")
        elif event.key == pygame.K_c:
            self._activate_option("credits")
        elif event.key == pygame.K_ESCAPE:
            self.engine.is_running = False

    def update(self, delta_time):
        self.engine.starfield.update(delta_time)

    def draw(self, target):
        target.fill((0, 0, 0))
        self.engine.starfield.draw(target)
        target.blit(self.logo_sprite, ((target.get_width() - self.logo_sprite.get_width()) // 2, 3))
        target.blit(self.base_sprite, ((target.get_width() - self.base_sprite.get_width()) // 2, 67))
        target.blit(self.mine_sprite, (27, 88))
        target.blit(self.mine_sprite, (target.get_width() - 43, 88))

        font = ServiceLocator.fonts.load("assets/fnt/PressStart2P.ttf", 8)
        y = 136
        for idx, (_, label) in enumerate(self.options):
            is_sel = idx == self.selected_idx
            text = f"> {label}" if is_sel else f"  {label}"
            color = (255, 235, 0) if is_sel else (235, 235, 255)
            surf = font.render(text, False, color)
            target.blit(surf, ((target.get_width() - surf.get_width()) // 2, y))
            y += 16


class PauseScene(Scene):
    def __init__(self, engine, gameplay):
        self.engine, self.gameplay = engine, gameplay

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_p, pygame.K_RETURN):
            _play_menu_sfx(self.engine, "menu_select")
            self.engine.resume_music()
            self.engine.scene_manager.request_change(self.gameplay)
        elif event.key == pygame.K_i:
            _play_menu_sfx(self.engine, "menu_select")
            self.engine.scene_manager.request_change(InstructionsScene(self.engine, self))
        elif event.key == pygame.K_c:
            _play_menu_sfx(self.engine, "menu_select")
            self.engine.scene_manager.request_change(CreditsScene(self.engine, self))
        elif event.key == pygame.K_ESCAPE:
            _play_menu_sfx(self.engine, "menu_select")
            self.engine.stop_music()
            self.engine.scene_manager.request_change(self.engine.title_scene)

    def update(self, delta_time):
        self.engine.starfield.update(delta_time)

    def draw(self, target):
        target.fill((0, 0, 0))
        self.engine.starfield.draw(target)
        font = ServiceLocator.fonts.load("assets/fnt/PressStart2P.ttf", 8)
        lines = ("PAUSA", "P/ENTER: SEGUIR", "I: INSTRUCCIONES", "C: CREDITOS", "ESC: MENU")
        y = 58
        for idx, line in enumerate(lines):
            col = (255, 220, 80) if idx == 0 else (235, 235, 255)
            surf = font.render(line, False, col)
            target.blit(surf, ((target.get_width() - surf.get_width()) // 2, y))
            y += 18


class ContinueScene(Scene):
    def __init__(self, engine):
        self.engine = engine
        self.remaining = 5.0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_c, pygame.K_RETURN, pygame.K_SPACE):
            _play_menu_sfx(self.engine, "menu_select")
            self.engine.continues_used += 1
            self.engine.score = 0
            if hasattr(self.engine, "score_manager"):
                self.engine.score_manager.reset_for_new_game()
            self.engine.start_game(lives=4, keep_score=False)

    def update(self, delta_time):
        self.engine.starfield.update(delta_time)
        self.remaining -= delta_time
        if self.remaining <= 0:
            self.engine.scene_manager.request_change(EndScene(self.engine, False))

    def draw(self, target):
        target.fill((0, 0, 0))
        self.engine.starfield.draw(target)
        font = ServiceLocator.fonts.load("assets/fnt/PressStart2P.ttf", 8)
        lines = (
            "CONTINUAR?",
            f"VIDAS PERDIDAS: {self.engine.lives_lost}",
            f"CONTINUES: {self.engine.continues_used}",
            "C / ENTER: SI",
            f"TIEMPO: {max(0.0, self.remaining):.1f}S",
        )
        y = 56
        for idx, line in enumerate(lines):
            col = (255, 80, 80) if idx == 0 else (235, 235, 255)
            surf = font.render(line, False, col)
            target.blit(surf, ((target.get_width() - surf.get_width()) // 2, y))
            y += 18


class EndScene(Scene):
    def __init__(self, engine, victory):
        self.engine, self.victory = engine, victory

    def on_enter(self):
        key = "victory" if self.victory else "defeat"
        path = self.engine.audio_config.get("music", {}).get(key)
        self.engine.play_music(path)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                _play_menu_sfx(self.engine, "menu_select")
                self.engine.scene_manager.request_change(self.engine.title_scene)
            elif event.key == pygame.K_r:
                _play_menu_sfx(self.engine, "menu_select")
                self.engine.new_game()

    def update(self, delta_time):
        self.engine.starfield.update(delta_time)

    def draw(self, target):
        target.fill((0, 0, 0))
        self.engine.starfield.draw(target)
        font = ServiceLocator.fonts.load("assets/fnt/PressStart2P.ttf", 8)
        title = "VICTORIA!" if self.victory else "GAME OVER"
        hi_score = (
            self.engine.score_manager.high_score
            if hasattr(self.engine, "score_manager")
            else self.engine.score
        )
        lines = (
            title,
            f"PUNTAJE: {self.engine.score}",
            f"HI-SCORE: {hi_score}",
            f"VIDAS PERDIDAS: {self.engine.lives_lost}",
            "ENTER: MENU | R: REINTENTAR",
        )
        y = 52
        for idx, line in enumerate(lines):
            col = (0, 255, 120) if (idx == 0 and self.victory) else ((255, 60, 60) if idx == 0 else (235, 235, 255))
            surf = font.render(line, False, col)
            target.blit(surf, ((target.get_width() - surf.get_width()) // 2, y))
            y += 18