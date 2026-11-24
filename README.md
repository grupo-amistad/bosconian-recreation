# Bosconian Recreation (Sharp X68000)

Recreación jugable de **Bosconian (versión Sharp X68000, 1988)** desarrollada en Python con **Pygame (`pygame-ce`)** y **Esper** bajo una arquitectura **ECS (Entity-Component-System)** para el curso de *Introducción al Desarrollo de Videojuegos*.

## Características implementadas

- **Arquitectura ECS (Esper) + Patrones de Diseño:** Game Loop único con `delta_time`, `Scene / SceneManager`, `Command` para controles, `State` para estados de vida del jugador y sistema de alertas (`GREEN`, `YELLOW`, `RED`), y `Service Locator` para gestión centralizada de configuraciones JSON, sprites, fuentes y audio `.ogg`.
- **10 Rondas Configurables:** Progresión de 10 niveles (`assets/cfg/levels/level_01.json` a `level_10.json`) con bases enemigas horizontales y verticales, 6 torretas por base, núcleos normales y animados (generadores de enemigos Tipo E), enemigos Tipo I, P y E, cazadores (*Hunter*), minas animadas letales y rocas.
- **Interfaz y Mundo (256 × 208 px):** Cámara con seguimiento y `wraparound` horizontal/vertical (`1024 × 1024`), campo de estrellas con parpadeo y paralaje multicapa, panel HUD fijo con `HI-SCORE` persistente, `1UP`, vidas restantes, indicador de disparo especial, minimapa en tiempo real y alertas por tiempo.

## Controles

| Acción | Teclas |
| :--- | :--- |
| Mover nave (8 direcciones con aceleración) | `Flechas` o `W A S D` |
| Disparo normal (frente y atrás) | `Z` o `Espacio` |
| Disparo especial (3 al frente + 1 atrás, según nivel) | `X` |
| Pausar / Reanudar partida | `P` |
| Navegar menús | `Flechas` + `Enter` (`I`: Instrucciones, `C`: Créditos) |

### Teclas rápidas de prueba / evaluación (durante la partida)

Para facilitar la verificación de todos los niveles y mecánicas durante la evaluación:
- **`F1`:** Avanzar inmediatamente a la siguiente ronda (o a la pantalla de Victoria en la ronda 10).
- **`F2`:** Habilitar y recargar usos del disparo especial en el nivel actual.
- **`F3`:** Alternar manualmente el estado de alerta (`GREEN` → `YELLOW` → `RED`).
- **`F4`:** Sumar `+10,000` puntos (permite verificar actualización de `HI-SCORE` y obtención de vida extra `1UP`).

## Ejecución local

Requiere Python 3.10 o superior:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

python -m pip install -r requirements.txt
python main.py
```

## Estructura del proyecto

- `main.py`: punto de entrada asíncrono (compatible con escritorio y exportación web `pygbag`).
- `src/engine/`: motor principal (`GameEngine`), escenas (`TitleScene`, `GameplayScene`, `PauseScene`, `ContinueScene`, `EndScene`), `SceneManager` y `Camera`.
- `src/ecs/components/` y `src/ecs/systems/`: componentes de datos y sistemas ECS.
- `src/player/`: configuración, comandos y fábrica de la nave del jugador.
- `src/create/`: fábricas de entidades, bases, enemigos y obstáculos.
- `src/ui/` y `src/world/`: `HUD`, `MiniMap`, `ScoreManager`, `AlertController` y `Starfield`.
- `src/services/`: `ServiceLocator` para caché y carga de recursos.
- `assets/`: configuraciones JSON (`cfg/`), sprites (`img/`), fuente pixel (`fnt/`), efectos (`sfx/`) y música (`mus/`).
- `docs/`: documentación técnica, diagrama de arquitectura y post-mortem grupal.

## Equipo de desarrollo

- **Manuel Santiago Prieto Hernández** — Arquitectura, motor y ECS
- **Daniela Munar Gonzalez** — Jugador, controles y mecánicas
- **Camilo Puerto Peña** — Enemigos, bases, obstáculos y combate
- **Camilo Inoue Rudas** — Mundo, interfaz, niveles, audio y despliegue