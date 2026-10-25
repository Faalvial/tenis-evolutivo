# CLAUDE.md — Tenis evolutivo

Proyecto para la Feria ABET 2026-II (Facultad de Ciencias, UNI): dos agentes
neuroevolutivos aprenden a jugar un tenis 2D en vista lateral, y se mide cómo
la función de aptitud (A ganar, B pelotear, C precisión) cambia las estrategias
que emergen. El plan completo está en `docs/PLAN.md`; las interfaces comunes,
en `docs/interfaces.md`.

## Comandos

```bash
.venv\Scripts\activate                 # activar el entorno (Windows)
pip install -r requirements.txt        # dependencias base
pip install -r requirements-3d.txt     # solo quien use ver3d.py (Ursina)
pytest                                 # todas las pruebas
```

## Reglas de trabajo

- Trabajar **una fase a la vez** (sección 12 del plan) y detenerse al cumplir sus criterios de aceptación para que el equipo revise.
- **Trabajo en equipo:** cada integrante trabaja en una rama de git de su rol y solo modifica sus módulos (tabla de abajo). Si hace falta cambiar una interfaz común, avisar y no hacerlo sin acuerdo del equipo. Antes de unir una rama, todas las pruebas deben pasar.
- **No todos usan Claude Code:** el código debe poder entenderlo y modificarlo a mano cualquier integrante. Nada de "magia": funciones cortas, nombres claros en español y comentarios que expliquen el porqué.
- Las carpetas de resultados, grabaciones, videos y los archivos de estado van en `.gitignore`; se comparten por la carpeta en la nube.
- **Objetivo de aprendizaje:** el equipo quiere entender cada concepto, y tiene poca experiencia con redes neuronales: explicarlas desde cero cuando aparezcan. El código va **comentado en español**, explicando el porqué y no solo el qué. Cada concepto nuevo se agrega al README con una fuente de estudio.
- Todos los parámetros van en `config.py`; nunca números mágicos en el código.
- No cambiar las aptitudes A/B/C (sección 7) ni las métricas (sección 8) sin preguntar: son el diseño experimental.
- Escribir pruebas (`pytest`) para las reglas del árbitro y para la reproducibilidad: la misma semilla debe dar el mismo resultado.
- El entrenamiento nunca dibuja; los visores solo reproducen grabaciones.
- Mantener todo reanudable y con guardado atómico (`guardado.guardar_json`).
- Medir tiempos al terminar F1 y actualizar el presupuesto de la sección 11.
- Si un criterio de aceptación no se cumple tras ajustes razonables, explicar el problema y proponer opciones en lugar de seguir adelante.

## Interfaces comunes (no cambiar sin acuerdo del equipo)

| Archivo | Qué define |
|---|---|
| `controlador.py` | `Percepcion`, `Accion`, `Controlador` y el marco propio (espejo) |
| `eventos.py` | Tipos de evento y motivos de fin de punto que produce el árbitro |
| `grabar.py` (`COLUMNAS`, formato del JSON) | Formato de las grabaciones que leen los visores |
| `config.py` | Parámetros compartidos; cambiar un valor de física afecta a todos |

Agregar un campo nuevo es compatible; renombrar, borrar o cambiar el
significado de uno no lo es. Si el formato de grabación cambia de forma
incompatible, subir `VERSION_GRABACION`.

## Dueños de los módulos (ramas)

| Rol | Rama | Módulos |
|---|---|---|
| R1 · Física y reglas | `fisica` | `mundo`, `jugador`, `arbitro`, `partido`, `rivales`, `tests/` de reglas |
| R2 · IA y entrenamiento | `ia` | `red`, `percepcion`, `genetico`, `aptitud`, `entrenar`, `experimentos` |
| R3 · Visualización y demo | `visual` | `grabar`, `ver2d`, `ver3d`, `jugar` |
| R4 · Análisis y documentos | `analisis` | `metricas`, `graficos`, documentos |
| R5 · Plan B | `plan-b` | `criaturas/` |
| R6 · Integración | — | revisión de todo; `controlador`, `eventos`, `guardado` |

`main` siempre funciona: nadie sube directo a ella; todo entra por *pull request*.

## Convenciones del código

- Cada módulo empieza con un docstring `nombre.py — qué hace y por qué`, como en el proyecto de las criaturas.
- Coordenadas en unidades de pymunk, `y` hacia arriba, cancha de `x = 0` a `ANCHO_CANCHA`. Jugador 0 = izquierda, 1 = derecha.
- Toda aleatoriedad usa un `random.Random(semilla)` propio, nunca el módulo `random` global.
