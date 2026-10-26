# Capítulo 0 · Preparación e interfaces (F0)

> Etiqueta: `fase-0` · Archivos: `config.py`, `controlador.py`, `eventos.py`,
> `grabar.py`, `guardado.py`, `tests/`

## 0.1 Dónde estamos

Antes de escribir una sola línea de física o de inteligencia artificial hay
un problema más básico: **seis personas van a escribir partes distintas de un
mismo programa al mismo tiempo**. Si cada uno inventa cómo se llaman las cosas,
al juntar el trabajo nada encaja.

La fase 0 resuelve eso con tres ideas:

1. **Un repositorio con reglas** (git, ramas, pruebas automáticas).
2. **Un solo lugar para los parámetros** (`config.py`).
3. **Interfaces comunes**: acuerdos sobre cómo se pasan los datos entre las partes.

## 0.2 Teoría

### Qué es una interfaz

Una interfaz es un **contrato**: "yo te entrego esto, con estos nombres y este
significado; lo que hagas por dentro es asunto tuyo". Un enchufe es una
interfaz: no importa cómo se genera la electricidad, mientras el enchufe tenga
la forma acordada.

En este proyecto hay tres:

```
             Percepcion                         eventos (eventos.py)
 partido.py ────────────► Controlador          ┌──► aptitud.py   (R2)
   (R1)     ◄──────────── (IA, rival, humano)  ├──► metricas.py  (R4)
                Accion                         └──► grabación ──► ver2d / ver3d (R3)
```

- **El controlador** (`controlador.py`): todo lo que juega (la IA, el rival
  programado, una persona con el teclado) recibe una `Percepcion` y devuelve
  una `Accion`. Gracias a eso, `partido.py` no necesita saber quién juega.
- **Los eventos** (`eventos.py`): lo que pasa en un partido ("golpe", "bote",
  "punto") con nombres fijos. La aptitud y las métricas se calculan leyendo
  eventos, sin volver a simular.
- **La grabación** (`grabar.py`): un archivo con las posiciones de todo en cada
  instante. Los visores solo leen esto.

### El marco propio (simetría)

El jugador de la izquierda tiene la red hacia +x; el de la derecha, hacia −x.
Si la red neuronal viera el mundo "tal cual", tendría que aprender a jugar dos
veces: una para cada lado. Por eso **cada jugador ve el mundo como si
estuviera a la izquierda**. Al jugador derecho se le refleja la percepción como
en un espejo:

| Cantidad | Al reflejar |
|---|---|
| posición x | `x → 1200 − x` |
| velocidad horizontal | `vx → −vx` |
| ángulo de la raqueta | `θ → π − θ` |
| todo lo vertical | no cambia |

Reflejar dos veces deja todo igual (pruébalo: `1200 − (1200 − x) = x`). Esa
propiedad es una prueba automática en `tests/test_controlador.py`.

### Reproducibilidad y semillas

Los programas usan números "al azar" que en realidad salen de una fórmula: un
**generador pseudoaleatorio**. Si le das el mismo punto de partida (la
**semilla**), produce siempre la misma secuencia. Por eso la regla del equipo es:
toda aleatoriedad usa su propio `random.Random(semilla)`, nunca el `random`
global. Así, la misma semilla da exactamente el mismo partido, el mismo
entrenamiento y el mismo resultado, y cualquiera puede repetir el experimento.

### Guardado atómico

Un entrenamiento puede durar horas. Si la computadora se apaga justo mientras
se escribe el archivo de progreso, el archivo queda a medias y se pierde todo.
`guardado.guardar_json` escribe primero en un archivo temporal y después lo
**renombra** (`os.replace`). Renombrar es *atómico*: o pasa completo o no pasa,
nunca a medias.

## 0.3 Cómo está construido

| Archivo | Qué define |
|---|---|
| `config.py` | Todos los parámetros. Regla: ningún número "mágico" en el código. |
| `controlador.py` | `Percepcion` (12 valores), `Accion` (4 valores, se recortan solos), `Controlador`, `ControladorQuieto`, `espejar_percepcion` |
| `eventos.py` | Tipos de evento (`saque`, `golpe`, `bote`, `red`, `punto`) y motivos de fin de punto |
| `grabar.py` | Formato JSON de las grabaciones: columnas por cuadro, medidas de la cancha copiadas, versión |
| `guardado.py` | `guardar_json` atómico y `cargar_json` |
| `pyproject.toml` | Configura pytest para que las pruebas encuentren los módulos |

## 0.4 Diario de decisiones

En F0 las interfaces quedaron como **propuesta**. Al empezar F1, antes de
programar la física, se decidieron tres puntos que la propuesta dejaba ambiguos
(detalle en `docs/interfaces.md`):

1. **"Golpe" es un contacto, no un swing.** La etapa 1 del entrenamiento premia
   "+1 por toque". Si `golpe` significara "hizo el movimiento", un jugador que
   agita la raqueta al aire sumaría puntos sin tocar nunca la pelota: una
   trampa servida. Por eso el evento se produce cuando la pelota toca la raqueta.
2. **La distancia mínima a la pelota viaja en el evento `punto`.** La etapa 1
   también premia "acercarse a la pelota cuando no la toca". Esa distancia no
   se puede reconstruir con los eventos, así que `partido.py` la mide y la
   agrega como campo nuevo (`distancia_minima`). Agregar un campo es
   compatible: nadie que lea los eventos se rompe.
3. **El lanzapelotas usa `saque`.** En la etapa 1 una máquina lanza pelotas.
   En vez de inventar un tipo de evento nuevo, cada lanzamiento es un `saque`, y
   `jugar_partido` acepta una función que decide cómo se lanza.

La regla general que aplicamos: **agregar es barato; renombrar o cambiar el
significado es caro**, porque rompe el código de otros.

## 0.5 Pruébalo tú

```bash
git checkout fase-0
pytest -v                      # 13 pruebas: controlador y grabación
python -c "from controlador import *; print(espejar_percepcion(Percepcion(300,200,150,-50,900,20,0,True,0.3,0,250,20)))"
git checkout -
```

Experimento: en `controlador.py`, dentro de `espejar_percepcion`, cambia
`config.ANCHO_CANCHA - p.pelota_x` por `config.ANCHO_CANCHA + p.pelota_x` y corre
`pytest`. Mira qué pruebas fallan y por qué: ¿cuál de las dos propiedades del
espejo se rompió? Después deshaz el cambio con `git checkout controlador.py`.

## 0.6 Criterios de aceptación

| Criterio | Estado |
|---|---|
| El repositorio existe y se clona | listo |
| `pip install -r requirements.txt` instala todo (Python 3.11+) | comprobado con Python 3.13 |
| `pytest` corre en la máquina de cada integrante | **cada integrante debe comprobarlo** |
| Interfaces acordadas | decididas en F1; falta la revisión del equipo |

## 0.7 Puente al capítulo 1

Ya sabemos **cómo** se van a hablar las partes, pero todavía no hay nada que
hable. Lo primero que necesita todo lo demás es un mundo donde la pelota caiga
y rebote, unos jugadores que se muevan y un árbitro que cuente los puntos. Sin
eso no hay nada que aprender (R2), nada que dibujar (R3) y nada que medir (R4).
Por eso la física y las reglas son la fase 1 y la ruta crítica del plan.

## 0.8 Para estudiar más

- Git y ramas: *Pro Git*, capítulos 2 y 3 — https://git-scm.com/book/es/v2
- Pruebas con pytest — https://docs.pytest.org/en/stable/getting-started.html
- Dataclasses (`Percepcion`, `Accion`) — https://docs.python.org/es/3/library/dataclasses.html
- Números pseudoaleatorios y semillas — https://docs.python.org/es/3/library/random.html
