# Bosconian Recreation

Recreación de **Bosconian (Sharp X68000)** para el proyecto de Introducción al Desarrollo de Videojuegos. El proyecto usa Python, Pygame y Esper, con arquitectura ECS.

## Ejecutar

Requiere Python 3.10 o posterior.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

## Estado de esta base

La estructura inicial parte del videojuego de la entrega 4 del curso: conserva el ciclo principal, el mundo de Esper, componentes y sistemas ECS, fábricas de entidades, configuración JSON y servicios para cargar recursos. También conserva sus sprites, fuente y sonidos como recursos de prototipo. El juego de esa entrega es una referencia técnica; sus mecánicas todavía deben evolucionar para cumplir los requisitos de Bosconian.

La ventana y las configuraciones iniciales aún reflejan el prototipo anterior. Ajustar la resolución a 256 × 208, definir el mundo con wraparound y crear las escenas y mecánicas de Bosconian forman parte del trabajo planificado.

## Estructura

- `main.py`: punto de entrada.
- `src/engine/`: ciclo de juego e inicialización.
- `src/ecs/components/`: datos de las entidades.
- `src/ecs/systems/`: lógica ejecutada por el ciclo principal.
- `src/create/`: fábricas de entidades y prefabs.
- `src/services/`: acceso centralizado a configuración y recursos.
- `assets/cfg/`: configuración JSON del prototipo.
- `assets/img/`, `fnt/`, `snd/`: recursos heredados de la entrega 4.
- `docs/`: contratos de arquitectura, reparto de trabajo y cronograma.

## Organización del equipo

La división, los contratos entre módulos y el cronograma de seis semanas están en [`docs/plan-de-trabajo.md`](docs/plan-de-trabajo.md). Todo módulo nuevo debe integrarse en el mismo Game Loop y usar los componentes y sistemas ECS compartidos.

## Flujo de Git

Trabajen en ramas `feature/<tema>` y abran Pull Requests hacia `develop`. Integren cambios al menos una vez por semana y mantengan `main` para entregas estables. Revisen [`docs/arquitectura.md`](docs/arquitectura.md) antes de modificar componentes compartidos.
