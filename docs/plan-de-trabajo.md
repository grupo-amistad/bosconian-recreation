# Reparto y cronograma de trabajo

Plan sugerido de seis semanas. Son semanas relativas, no fechas oficiales de entrega.

## Responsabilidades

| Integrante | Área principal | Entregables principales |
|---|---|---|
| 1 (dueño de la arquitectura) | Motor y ECS | Game Loop, componentes compartidos, escenas, Service Locator, cámara, configuración e integración |
| 2 | Jugador | Fábrica, controles Command, movimiento con aceleración, disparos, habilidad, vidas y reaparición |
| 3 | Combate | Enemigos I/P/E, IA, bases y torretas, núcleo, obstáculos, hitboxes, colisiones y explosiones |
| 4 | Mundo e interfaz | Estrellas y parallax, minimapa, HUD, alertas, puntaje, niveles, audio, menús y despliegue |

Cada persona programa su módulo y participa en la integración, revisión de PR y entregables grupales. Las bonificaciones se planifican solo después de cubrir lo obligatorio.

## Semanas

| Semana | Meta | Trabajo coordinado | Criterio de salida |
|---|---|---|---|
| 1 | Base común | 1: motor/ECS/contratos; 2: comando y movimiento inicial; 3: componentes/fábricas de combate; 4: JSON, estrellas y HUD inicial | Todo el equipo ejecuta la misma base; ventana a resolución objetivo, loop y entidad visible |
| 2 | Prototipo jugable | 1: render ECS y cámara inicial; 2: nave, aceleración y disparos; 3: enemigo y AABB; 4: estrellas y primer nivel | El jugador se mueve, dispara y destruye un enemigo |
| 3 | Combate esencial | 1: escenas/recursos/estados; 2: habilidad, vidas y reaparición; 3: bases, torres, núcleo, I/P/E y obstáculos; 4: HUD, puntaje y alertas | Un nivel permite destruir bases y sobrevivir al combate |
| 4 | Mundo e interfaz | 1: cámara y wraparound; 2: ajuste del jugador; 3: balance de IA y colisiones; 4: minimapa, parallax y audio | Un nivel representa el ciclo central de Bosconian con mundo e interfaz funcionales |
| 5 | Juego completo | 1: escenas, pausa y transiciones; 2: controles y balance; 3: diez configuraciones y dificultad; 4: menús, instrucciones y créditos | Se puede jugar desde el título hasta victoria o derrota en los diez niveles |
| 6 | Entrega | Correcciones, integración, publicación, documentación, post-mortem y presentación | Versión publicada, README, tag final, post-mortems individuales y video |

## Ritmo de seguimiento

- Inicio de semana: 30 minutos para acordar objetivo y contratos.
- Mitad de semana: 30 minutos para revisar bloqueos y dependencias.
- Cierre semanal: 60 minutos para integrar, revisar y demostrar el criterio de salida.
- Mantener ramas `feature/*`, PR hacia `develop` e integración semanal. No trabajar directamente sobre `main`.

## Bonificaciones

Una vez asegurados los requisitos obligatorios, opciones razonables son gamepad (2), intro animada o récord (4), enemigo espía o formaciones (3), modo atractor (1 + 4). Jefe y editor de niveles tienen mayor costo y conviene dejarlos al final.
