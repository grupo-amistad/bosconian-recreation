import pygame
from src.engine.scene import Scene
from src.services import ServiceLocator


class TextScene(Scene):
    title = ""
    lines: tuple[str, ...] = ()

    def __init__(self, engine, return_scene=None) -> None:
        self.engine = engine
        self.return_scene = return_scene or engine.title_scene

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.engine.scene_manager.request_change(self.return_scene)

    def update(self, delta_time):
        pass

    def draw(self, target):
        target.fill((0, 0, 0))
        self.engine.starfield.draw(target)
        self.engine.draw_lines(target, (self.title, *self.lines, "", "ESC / ENTER: volver"), 75)


class InstructionsScene(TextScene):
    title = "INSTRUCCIONES"
    lines = ("FLECHAS: MOVER", "Z / ESPACIO: DISPARAR", "X: ESPECIAL", "P: PAUSA")


class CreditsScene(TextScene):
    title = "CREDITOS"
    lines = ("BOSCONIAN RECREATION", "PROYECTO DE VIDEOJUEGOS", "EQUIPO DE 4 INTEGRANTES")


class TitleScene(Scene):
    def __init__(self, engine):
        self.engine = engine
        base = ServiceLocator.images.load("assets/img/Boskonian spacecraft.png")
        mine = ServiceLocator.images.load("assets/img/space mine.png")
        self.base_sprite = pygame.transform.scale(base, (72, 80))
        self.mine_sprite = pygame.transform.scale(mine, (20, 20))

    def on_enter(self):
        self.engine.play_music("assets/mus/starshooterv2.1.ogg")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.engine.new_game()
            elif event.key == pygame.K_i:
                self.engine.scene_manager.request_change(InstructionsScene(self.engine, self))
            elif event.key == pygame.K_c:
                self.engine.scene_manager.request_change(CreditsScene(self.engine, self))
            elif event.key == pygame.K_ESCAPE:
                self.engine.is_running = False

    def update(self, delta_time):
        self.engine.starfield.update(delta_time)

    def draw(self, target):
        target.fill((0, 0, 0))
        self.engine.starfield.draw(target)
        target.blit(self.base_sprite, ((target.get_width() - self.base_sprite.get_width()) // 2, 10))
        target.blit(self.mine_sprite, (28, 55))
        target.blit(self.mine_sprite, (target.get_width() - 48, 55))
        self.engine.draw_lines(target, ("BOSCONIAN", "ENTER: JUGAR", "I: INSTRUCCIONES", "C: CREDITOS", "ESC: SALIR"), 105)


class PauseScene(Scene):
    def __init__(self, engine, gameplay):
        self.engine, self.gameplay = engine, gameplay

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_p, pygame.K_RETURN):
            self.engine.resume_music()
            self.engine.scene_manager.request_change(self.gameplay)
        elif event.key == pygame.K_i:
            self.engine.scene_manager.request_change(InstructionsScene(self.engine, self))
        elif event.key == pygame.K_c:
            self.engine.scene_manager.request_change(CreditsScene(self.engine, self))
        elif event.key == pygame.K_ESCAPE:
            self.engine.stop_music()
            self.engine.scene_manager.request_change(self.engine.title_scene)

    def update(self, delta_time):
        pass

    def draw(self, target):
        target.fill((0, 0, 0))
        self.engine.starfield.draw(target)
        self.engine.draw_lines(target, ("PAUSA", "P / ENTER: CONTINUAR", "I: INSTRUCCIONES", "C: CREDITOS", "ESC: MENU"), 82)


class ContinueScene(Scene):
    def __init__(self, engine):
        self.engine = engine
        self.remaining = 5.0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_c, pygame.K_RETURN, pygame.K_SPACE):
            self.engine.continues_used += 1
            self.engine.score = 0
            self.engine.start_game(lives=4, keep_score=False)

    def update(self, delta_time):
        self.remaining -= delta_time
        if self.remaining <= 0:
            self.engine.scene_manager.request_change(EndScene(self.engine, False))

    def draw(self, target):
        target.fill((0, 0, 0))
        self.engine.starfield.draw(target)
        self.engine.draw_lines(target, ("GAME OVER", f"Vidas perdidas: {self.engine.lives_lost}",
            f"Continuaciones: {self.engine.continues_used}", "C: CONTINUAR", f"{self.remaining:.1f}s"), 78)


class EndScene(Scene):
    def __init__(self, engine, victory):
        self.engine, self.victory = engine, victory

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.engine.scene_manager.request_change(self.engine.title_scene)

    def update(self, delta_time):
        self.engine.starfield.update(delta_time)

    def draw(self, target):
        target.fill((0, 0, 0))
        self.engine.starfield.draw(target)
        title = "VICTORIA" if self.victory else "DERROTA"
        self.engine.draw_lines(target, (title, f"Puntaje: {self.engine.score}",
            f"Vidas perdidas: {self.engine.lives_lost}", f"Continuaciones: {self.engine.continues_used}", "ENTER: MENU"), 78)
