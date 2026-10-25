# Tenis evolutivo

Dos agentes controlados por redes neuronales aprenden a jugar un tenis 2D
(vista lateral) mediante un algoritmo genético. El experimento compara qué
estrategias emergen según la función de aptitud: **A** ganar, **B** pelotear,
**C** precisión. Proyecto para la Feria ABET 2026-II, Facultad de Ciencias, UNI.

- Plan completo: [`docs/PLAN.md`](docs/PLAN.md)
- Interfaces comunes (controlador, eventos, grabación): [`docs/interfaces.md`](docs/interfaces.md)
- Reglas para trabajar con Claude Code (y sin él): [`CLAUDE.md`](CLAUDE.md)

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
| F0 Preparación | Repositorio, entorno y pruebas listos; interfaces **propuestas, falta acordarlas** |

## Archivos

| Archivo | Qué hace |
|---|---|
| `config.py` | Todos los parámetros (física, reglas, red, AG, grabaciones) |
| `controlador.py` | Interfaz común: `Percepcion`, `Accion`, `Controlador`, espejo |
| `eventos.py` | Vocabulario de eventos del partido (golpe, bote, punto...) |
| `grabar.py` | Formato de grabación de partidos para los visores |
| `guardado.py` | Guardado atómico de JSON |
| `tests/` | Pruebas automáticas (`pytest`) |

## Guía de estudio

Cada concepto nuevo que aparezca en el código se agrega aquí con una fuente.

### Python y herramientas

- **Entornos virtuales (`venv`)**: cada proyecto tiene sus propias librerías, sin mezclarse con las de otros proyectos. https://docs.python.org/es/3/library/venv.html
- **Pruebas automáticas con pytest**: funciones que comprueban que el código hace lo que debe; se corren todas con `pytest`. https://docs.pytest.org/en/stable/getting-started.html
- **Git y ramas**: libro *Pro Git* en español, capítulos 2 y 3. https://git-scm.com/book/es/v2
- **Dataclasses**: clases para agrupar datos (así están hechas `Percepcion` y `Accion`). https://docs.python.org/es/3/library/dataclasses.html

### Conceptos del proyecto

Las fuentes de la sección 17 del plan, que se irán moviendo aquí a medida
que cada concepto aparezca en el código: algoritmos genéticos, redes
neuronales, neuroevolución, coevolución y salón de la fama, trampas de la
evolución, Pymunk, Ursina y `multiprocessing`.
