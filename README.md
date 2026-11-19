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
python -m pip install --upgrade -r requirements.txt
python main.py
```

## Estado de esta base

La estructura inicial parte del videojuego de la entrega 4 del curso: conserva el ciclo principal, el mundo de Esper, componentes y sistemas ECS, fábricas de entidades, configuración JSON y servicios para cargar recursos. También conserva sus sprites, fuente y sonidos como recursos de prototipo. El juego de esa entrega es una referencia técnica; sus mecánicas todavía deben evolucionar para cumplir los requisitos de Bosconian.

La ventana base usa la resolución total de **256 × 208 píxeles**. El primer archivo de nivel está en `assets/cfg/levels/level_01.json`; los demás niveles deben seguir el contrato de [`docs/configuracion-de-niveles.md`](docs/configuracion-de-niveles.md). La jugabilidad y los assets del prototipo de la entrega anterior todavía se están reemplazando por los de Bosconian.

## Estructura

- `main.py`: punto de entrada.
- `src/engine/`: ciclo de juego, contrato de escenas y Scene Manager.
- `src/ecs/components/`: datos de las entidades.
- `src/ecs/systems/`: lógica ejecutada por el ciclo principal.
- `src/create/`: fábricas de entidades y prefabs.
- `src/services/`: acceso centralizado a configuración y recursos.
- `assets/cfg/`: configuración JSON global y de niveles.
- `assets/img/`, `fnt/`, `snd/`: recursos heredados de la entrega 4.
- `docs/`: contratos de arquitectura, reparto de trabajo y cronograma.

## Organización del equipo

La división, los contratos entre módulos y el cronograma de seis semanas están en [`docs/plan-de-trabajo.md`](docs/plan-de-trabajo.md). Todo módulo nuevo debe integrarse en el mismo Game Loop y usar los componentes y sistemas ECS compartidos.

## Flujo de Git

Revisen [`docs/arquitectura.md`](docs/arquitectura.md) antes de modificar componentes compartidos.
