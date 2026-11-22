from abc import ABC, abstractmethod

import esper
import pygame

from src.ecs.components.c_input_command import CInputCommand
from src.ecs.components.c_player_intent import CPlayerIntent


class PlayerCommand(ABC):
    @abstractmethod
    def execute(self, intent: CPlayerIntent, active: bool, pressed: bool) -> None:
        """Apply the input state of one binding to the player's intent."""


class MoveCommand(PlayerCommand):
    def __init__(self, x: int, y: int) -> None:
        self.direction = pygame.Vector2(x, y)

    def execute(self, intent: CPlayerIntent, active: bool, pressed: bool) -> None:
        if active:
            intent.move += self.direction


class FireCommand(PlayerCommand):
    def execute(self, intent: CPlayerIntent, active: bool, pressed: bool) -> None:
        intent.fire = intent.fire or pressed
        intent.fire_held = intent.fire_held or active


class SpecialCommand(PlayerCommand):
    def execute(self, intent: CPlayerIntent, active: bool, pressed: bool) -> None:
        intent.special = intent.special or pressed


PLAYER_COMMANDS: dict[str, PlayerCommand] = {
    "PLAYER_LEFT": MoveCommand(-1, 0),
    "PLAYER_RIGHT": MoveCommand(1, 0),
    "PLAYER_UP": MoveCommand(0, -1),
    "PLAYER_DOWN": MoveCommand(0, 1),
    "PLAYER_FIRE": FireCommand(),
    "PLAYER_SPECIAL": SpecialCommand(),
}

DEFAULT_CONTROLS: dict[str, list[str]] = {
    "PLAYER_LEFT": ["left", "a"],
    "PLAYER_RIGHT": ["right", "d"],
    "PLAYER_UP": ["up", "w"],
    "PLAYER_DOWN": ["down", "s"],
    "PLAYER_FIRE": ["z", "space"],
    "PLAYER_SPECIAL": ["x"],
}


def key_from_name(name: str) -> int:

    try:
        return pygame.key.key_code(name)
    except (ValueError, AttributeError):
        constant = getattr(pygame, f"K_{name}", None)
        if constant is None:
            raise ValueError(f"Unknown key name in player controls: {name!r}") from None
        return constant


def create_player_input_bindings(
    world: esper.World, controls: dict[str, list[str]] | None = None
) -> list[int]:
    entities = []
    for action, keys in (controls or DEFAULT_CONTROLS).items():
        if action not in PLAYER_COMMANDS:
            raise ValueError(f"Unknown player action in controls: {action!r}")
        for key_name in ([keys] if isinstance(keys, str) else keys):
            entity = world.create_entity()
            world.add_component(
                entity, CInputCommand(action, "keyboard", key_from_name(key_name))
            )
            entities.append(entity)
    return entities


def release_input_commands(world: esper.World) -> None:

    for _, (command,) in world.get_components(CInputCommand):
        command.active = False
        command.pressed = False


def system_player_commands(world: esper.World) -> None:
    intents = [intent for _, (intent,) in world.get_components(CPlayerIntent)]
    for intent in intents:
        intent.move.update(0, 0)
        intent.fire = False
        intent.fire_held = False
        intent.special = False

    for _, (input_command,) in world.get_components(CInputCommand):
        command = PLAYER_COMMANDS.get(input_command.action)
        if command is None:
            continue
        for intent in intents:
            command.execute(intent, input_command.active, input_command.pressed)

    for intent in intents:
        intent.move.x = max(-1.0, min(1.0, intent.move.x))
        intent.move.y = max(-1.0, min(1.0, intent.move.y))