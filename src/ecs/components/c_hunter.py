import pygame


class CHunter:
    def __init__(self, origin, aggro_range, leash_range, speed, return_speed, chase_sound=None):
        self.origin = pygame.Vector2(origin)
        self.aggro_range = float(aggro_range)
        self.leash_range = float(leash_range)
        self.speed = float(speed)
        self.return_speed = float(return_speed)
        self.chase_sound = chase_sound
        self.was_chasing = False
        self.returning = False
        self.paused_until_player_moves_away = False
