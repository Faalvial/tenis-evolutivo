# Tenis evolutivo

Dos agentes controlados por redes neuronales aprenden a jugar un tenis 2D
(vista lateral) mediante un algoritmo genético. El experimento compara qué
estrategias emergen según la función de aptitud: **A** ganar, **B** pelotear,
**C** precisión. Proyecto para la Feria ABET 2026-II, Facultad de Ciencias, UNI.

- Plan completo: [`docs/PLAN.md`](docs/PLAN.md)
- Interfaces comunes (controlador, eventos, grabación): [`docs/interfaces.md`](docs/interfaces.md)
- Reglas para trabajar con Claude Code (y sin él): [`CLAUDE.md`](CLAUDE.md)
- **El libro del proyecto** (cómo y por qué se construyó cada fase): [`docs/libro/`](docs/libro/README.md)

## Preparar el entorno (una sola vez)

Requiere Python 3.11 o superior (probado con 3.12) y git.

```bash
git clone <URL del repositorio>
cd <carpeta del repositorio>
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest
```

En macOS o Linux, el entorno se activa con `source .venv/bin/activate`.
Quien trabaje en el visor 3D (R3) instala además `pip install -r requirements-3d.txt`.

Criterio de F0: `pytest` corre sin errores en la máquina de cada integrante.

## Cómo trabajamos con git

1. `main` siempre funciona: nadie sube cambios directamente a ella.
2. Cada uno trabaja en la rama de su rol: `git switch -c fisica` (o `ia`, `visual`, `analisis`, `plan-b`).
3. Cambios pequeños y frecuentes: `git add`, `git commit`, `git push -u origin <rama>`.
4. Para unir a `main`: abrir un *pull request* en GitHub. Antes, `pytest` debe pasar; el integrador (R6) lo revisa.
5. Al menos una vez por semana, traer lo nuevo de `main` a tu rama: `git pull origin main`.
6. Los resultados pesados (`resultados/`, grabaciones, videos) **no** se suben: van a la carpeta compartida en la nube.

## Estado

| Fase | Estado |
|---|---|
| F0 Preparación | Repositorio, entorno y pruebas listos; interfaces decididas en F1, **falta la revisión del equipo** |
| F1 Física y reglas | Lista: dos rivales programados pelotean, 52 pruebas pasan ([capítulo 1](docs/libro/cap01_fisica_y_reglas.md)) |
| V1 Grabaciones + 2D | Lista: `python partido.py --grabar ...` y `python ver2d.py ...` ([capítulo 2](docs/libro/cap02_grabaciones_y_visor.md)) |

Para probarlo:

```bash
python partido.py                                  # un partido entre dos rivales programados
python partido.py --grabar grabaciones/demo.json   # ...grabado
python ver2d.py grabaciones/demo.json              # verlo
python partido.py --medir 20                       # medir el tiempo de un partido
```

## Archivos

| Archivo | Qué hace |
|---|---|
| `config.py` | Todos los parámetros (física, reglas, red, AG, grabaciones) |
| `controlador.py` | Interfaz común: `Percepcion`, `Accion`, `Controlador`, espejo |
| `eventos.py` | Vocabulario de eventos del partido (golpe, bote, punto...) |
| `grabar.py` | Formato de grabación de partidos para los visores |
| `guardado.py` | Guardado atómico de JSON |
| `mundo.py` | Física (pymunk): suelo, red, pelota; anota los contactos |
| `jugador.py` | Cubo + raqueta con motor; aplica acciones; modelo de golpe |
| `arbitro.py` | Reglas del tenis, sin física; produce los eventos |
| `partido.py` | Simula partidos entre dos controladores |
| `rivales.py` | Rival programado (tiro parabólico + errores al azar) |
| `ver2d.py` | Visor 2D de grabaciones (pygame) |
| `tests/` | Pruebas automáticas (`pytest`) |

## Guía de estudio

Cada concepto nuevo que aparezca en el código se agrega aquí con una fuente.

### Python y herramientas

- **Entornos virtuales (`venv`)**: cada proyecto tiene sus propias librerías, sin mezclarse con las de otros proyectos. https://docs.python.org/es/3/library/venv.html
- **Pruebas automáticas con pytest**: funciones que comprueban que el código hace lo que debe; se corren todas con `pytest`. https://docs.pytest.org/en/stable/getting-started.html
- **Git y ramas**: libro *Pro Git* en español, capítulos 2 y 3. https://git-scm.com/book/es/v2
- **Dataclasses**: clases para agrupar datos (así están hechas `Percepcion` y `Accion`). https://docs.python.org/es/3/library/dataclasses.html

### Física (capítulo 1)

- **Motor de física y pasos de tiempo**: el tiempo avanza a saltos de 1/60 s y en cada uno se aplica Newton. *The Nature of Code*, cap. 1 y 2. https://natureofcode.com/forces/
- **Pymunk** (cuerpos, formas, uniones, motores, filtros de colisión). https://www.pymunk.org/en/latest/overview.html
- **Tiro parabólico**: las ecuaciones que usa el rival programado para predecir la pelota. Serway, *Física*, cap. 4.
- **Coeficiente de restitución (elasticidad)**: qué fracción de la velocidad conserva un rebote. https://es.wikipedia.org/wiki/Coeficiente_de_restituci%C3%B3n
- **Atravesamiento (*tunneling*)**: por qué un objeto rápido puede saltarse un choque y cómo se evita. https://en.wikipedia.org/wiki/Collision_detection
- **Control proporcional**: girar más rápido cuanto más lejos del objetivo (el "P" de un PID). https://es.wikipedia.org/wiki/Controlador_PID
- **Máquina de estados**: cómo el árbitro recuerda lo que pasó antes. https://es.wikipedia.org/wiki/M%C3%A1quina_de_estados

### Conceptos del proyecto

Las fuentes de la sección 17 del plan, que se irán moviendo aquí a medida
que cada concepto aparezca en el código: algoritmos genéticos, redes
neuronales, neuroevolución, coevolución y salón de la fama, trampas de la
evolución, Pymunk, Ursina y `multiprocessing`.
