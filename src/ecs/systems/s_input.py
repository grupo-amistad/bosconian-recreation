import pygame
import esper

from src.ecs.components.c_input_command import CInputCommand


def system_input(world: esper.World, events: list[pygame.event.Event]) -> None:
    commands = [
        command
        for _, (command,) in world.get_components(CInputCommand)
    ]

    for command in commands:
        command.pressed = False

    for event in events:
        for command in commands:
            if command.input_type == "keyboard":
                if event.type == pygame.KEYDOWN and event.key == command.key:
                    command.active = True
                    command.pressed = True
                elif event.type == pygame.KEYUP and event.key == command.key:
                    command.active = False
            elif (
                command.input_type == "mouse"
                and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == command.key
            ):
                command.pressed = True
