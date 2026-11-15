class CEnemySpawner:
    def __init__(
        self,
        spawn_events: list[dict],
        enemy_configs: dict,
        dynamic_config: dict | None = None,
    ) -> None:
        self.spawn_events = sorted([
            {
                "time": event["time"],
                "enemy_type": event["enemy_type"],
                "position": event["position"],
                "spawned": False,
            }
            for event in spawn_events
        ], key=lambda event: event["time"])
        self.enemy_configs = enemy_configs
        self.elapsed_time = 0.0
        self.dynamic_config = dynamic_config or {}
        self.next_wave_time = self.dynamic_config.get("start_time", 24.0)
        self.wave_number = 0
