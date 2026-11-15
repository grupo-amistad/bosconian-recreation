# Contratos iniciales de arquitectura

## Flujo de ejecución

`main.py` crea `GameEngine`. El motor inicializa Pygame y los servicios, crea un `esper.World` y ejecuta el ciclo de eventos, actualización y renderizado. Los módulos de jugador, combate, mundo e interfaz agregan sistemas a este mismo ciclo; no deben crear loops de juego independientes.

## ECS y entidades

- Las entidades son identificadores creados por `esper.World`.
- Los componentes guardan datos; no ejecutan lógica de juego.
- Los sistemas consultan componentes y modifican el mundo.
- Las fábricas de `src/create/` ensamblan entidades a partir de componentes.
- Los cambios de entidad durante la iteración deben respetar el procesamiento diferido de Esper (`world.process()`).

## Convenciones compartidas

- Posiciones: `pygame.Vector2`, en píxeles del mundo.
- Velocidades: píxeles por segundo; multiplicar por `delta_time` en segundos.
- El tamaño final del área de juego debe ser 256 × 208 píxeles. Si se usa un lienzo de 256 × 256, reservar 24 píxeles negros arriba y abajo.
- Las entidades del mundo usan coordenadas de cámara; HUD y minimapa se dibujan en coordenadas de pantalla.
- Las colisiones obligatorias usan hitboxes AABB. La hitbox debe ser componente independiente del sprite.
- Los niveles y sus parámetros se cargan desde JSON; los sistemas no deben codificar una lista de niveles dentro de la lógica.

## Integración entre responsables

- Integrante 1 mantiene los componentes y contratos compartidos, el motor, escenas, cámara y servicios.
- Integrante 2 crea entidades y sistemas de jugador sobre esos contratos.
- Integrante 3 implementa combate, enemigos, bases y obstáculos, coordinando hitboxes con el integrante 2.
- Integrante 4 implementa niveles, mundo e interfaz, coordinando la cámara con el integrante 1 y las alertas/spawns con el integrante 3.
- Antes de cambiar un componente compartido, se debe abrir un PR o avisar al equipo para actualizar sus consumidores en el mismo cambio.
