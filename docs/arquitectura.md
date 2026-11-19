# Contratos iniciales de arquitectura

## Flujo de ejecución

`main.py` crea `GameEngine`. El motor inicializa Pygame, la ventana y los servicios; crea un `esper.World` y ejecuta un único ciclo de eventos, actualización y renderizado. `SceneManager` entrega eventos, `delta_time` y la superficie de dibujo a la escena activa. Un cambio de escena solo llama `on_exit`/`on_enter`; no reinicia Pygame ni crea otra ventana. Los módulos de jugador, combate, mundo e interfaz agregan sistemas a este mismo ciclo; no deben crear loops de juego independientes.

## ECS y entidades

- La base depende de Esper 2.x porque utiliza `esper.World`; Esper 3.0 eliminó esa clase y migró la API a funciones de módulo. No actualizar a Esper 3 hasta migrar conjuntamente el motor y todos los sistemas.
- Las entidades son identificadores creados por `esper.World`.
- Los componentes guardan datos; no ejecutan lógica de juego.
- Los sistemas consultan componentes y modifican el mundo.
- Las fábricas de `src/create/` ensamblan entidades a partir de componentes.
- Los cambios de entidad durante la iteración deben respetar el procesamiento diferido de Esper (`world.process()`).

## Componentes compartidos

- `CTransform.pos`: `pygame.Vector2` en píxeles de mundo; `CTransform.angle`: grados.
- `CVelocity.vel`: `pygame.Vector2` en píxeles por segundo. Los sistemas integran posición con `vel * delta_time`.
- `CSurface`: sprite/fuente visual y rectángulo de recorte. No define colisiones.
- `CAnimation`: estado del sprite animado y tiempos en segundos.
- `CHitBox.size` y `CHitBox.offset`: dimensiones y desplazamiento en píxeles; su AABB se calcula desde `CTransform` y no depende del sprite.
- `CState.name`, `elapsed` y `data`: estado de gameplay, duración en segundos y datos opcionales.

Las fábricas pueden crear una hitbox con el tamaño visual como valor inicial, pero la almacenan en `CHitBox`. Cada entidad puede definir dimensiones y offset propios sin cambiar el sprite.

## Convenciones compartidas

- Posiciones: `pygame.Vector2`, en píxeles del mundo.
- Velocidades: píxeles por segundo; multiplicar por `delta_time` en segundos.
- El tamaño del área de juego es 256 × 208 píxeles. Si más adelante se elige un lienzo de 256 × 256, reservar 24 píxeles negros arriba y abajo.
- Las entidades guardan coordenadas de mundo; en la base actual el mundo coincide con la ventana. Cuando se integre la cámara, esta convertirá a coordenadas de pantalla. HUD y minimapa se dibujan en coordenadas fijas de pantalla.
- Las colisiones obligatorias usan hitboxes AABB. La hitbox debe ser componente independiente del sprite.
- Los niveles y sus parámetros se cargan desde JSON; los sistemas no deben codificar una lista de niveles dentro de la lógica.

## Integración entre responsables

- Integrante 1 mantiene los componentes y contratos compartidos, el motor, escenas, cámara y servicios.
- Integrante 2 crea entidades y sistemas de jugador sobre esos contratos.
- Integrante 3 implementa combate, enemigos, bases y obstáculos, coordinando hitboxes con el integrante 2.
- Integrante 4 implementa niveles, mundo e interfaz, coordinando la cámara con el integrante 1 y las alertas/spawns con el integrante 3.
- Antes de cambiar un componente compartido, se debe abrir un PR o avisar al equipo para actualizar sus consumidores en el mismo cambio.

## Escenas

Cada escena implementa `handle_event(event)`, `update(delta_time)` y `draw(target)`, y puede preparar/cerrar su estado en `on_enter()` y `on_exit()`. Una escena puede solicitar una transición al `SceneManager`; el manager aplica la transición al terminar el callback actual.
