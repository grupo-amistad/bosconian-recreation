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
- `bases`: lista de bases con `type`, `position` y `orientation`. El tipo se configura en `assets/cfg/bases.json`; cada base crea seis torretas por defecto, alterna el estado del núcleo y puede producir enemigos E desde el nivel indicado.
- `obstacles`: lista de obstáculos con `type`, `position` y, opcionalmente, `velocity`. Los tipos se configuran en `assets/cfg/obstacles.json`. `mine` es destructible, animada y letal; `rock` es indestructible y rebota frente a las bases. `rock_mobile` usa el mismo comportamiento con velocidad inicial.

## Configuración de combate

`assets/cfg/enemies.json` define I, P y E junto con los tipos de prototipo anteriores. Cada entrada puede indicar:

- `size`, `hitbox_size` y `hitbox_offset`, independientemente del sprite. Los mismos campos de hitbox aplican a los proyectiles del jugador y pueden configurarse para torretas, bases y obstáculos.
- `velocity_min` y `velocity_max` en píxeles por segundo.
- `health`, `score`, `behavior` (`patrol`, `seek_base` o `seek_player`) y `turn_rate` en grados por segundo.
- `fire_interval`, `bullet_speed` y `bullet_size` para enemigos que disparan.

Las bases (`assets/cfg/bases.json`) permiten configurar dimensiones de hitbox y colores del núcleo, radio y cantidad de torretas, orientación, velocidades de giro/disparo, tiempos de apertura/cierre, puntajes y nivel/intervalo de aparición de E. Los obstáculos admiten `destructible`, `lethal`, `blast_radius`, `health`, `score`, hitbox y animaciones. Las reglas AABB se resuelven desde un solo sistema de combate.

## Unidades y límites

Todas las posiciones y dimensiones están en píxeles del mundo. Los tiempos están en segundos. El archivo de nivel no guarda `delta_time`: lo aporta el ciclo principal. Las posiciones de aparición y el `spawn_area` deben quedar dentro del rectángulo `[0, world_size.w) × [0, world_size.h)`.

El nivel 1 es la configuración de transición desde el prototipo de la entrega 4. Sus posiciones fueron adaptadas a 256 × 208; enemigos y datos de oleadas se irán sustituyendo por las entidades de Bosconian.
