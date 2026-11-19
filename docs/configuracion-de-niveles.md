# Configuración de niveles

Los niveles se guardan como JSON independientes en `assets/cfg/levels/level_01.json` a `level_10.json`. `GameEngine` carga un archivo por ruta y los sistemas reciben los datos al crear las entidades; la lógica de cada sistema no debe codificar listas de rondas.

## Contrato

- `level`: número de ronda, de 1 a 10.
- `world_size`: ancho y alto del mundo en píxeles. La base usa `w: 256`, `h: 208`.
- `player_spawn.position`: coordenadas iniciales `x`, `y` en píxeles de mundo.
- `player_spawn.max_bullets`: límite de proyectiles normales.
- `player_spawn.special_ability`: si la habilidad especial está disponible en esta ronda.
- `enemy_spawn_events`: lista de apariciones programadas. Cada entrada tiene `time` en segundos, `enemy_type` (clave de `assets/cfg/enemies.json`) y `position` (`x`, `y`). El sistema añade internamente el estado `spawned`.
- `dynamic_spawning`: configuración opcional de oleadas (`start_time`, `interval`, `initial_count`, `increase_every`, `increase_amount`, `enemy_types` y `spawn_area`). El área define `min_x`, `max_x`, `min_y`, `max_y` en píxeles.
- `bases` y `obstacles`: arreglos reservados para las entidades de nivel que integrará el sistema de combate; cada tipo documentará su propio objeto cuando se implemente.

## Unidades y límites

Todas las posiciones y dimensiones están en píxeles del mundo. Los tiempos están en segundos. El archivo de nivel no guarda `delta_time`: lo aporta el ciclo principal. Las posiciones de aparición y el `spawn_area` deben quedar dentro del rectángulo `[0, world_size.w) × [0, world_size.h)`.

El nivel 1 es la configuración de transición desde el prototipo de la entrega 4. Sus posiciones fueron adaptadas a 256 × 208; enemigos y datos de oleadas se irán sustituyendo por las entidades de Bosconian.
