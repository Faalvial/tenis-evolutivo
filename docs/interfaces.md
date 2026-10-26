# Interfaces comunes

> **Estado: DECIDIDA en F1 (26 oct 2026), pendiente de revisión del equipo.**
> Se tomó la propuesta de F0 con tres aclaraciones (al final de este archivo);
> el porqué de cada una está en `docs/libro/cap00_preparacion.md`. Cuando el
> equipo la revise, cambiar esta línea a "Acordada el <fecha>". Desde entonces,
> cualquier cambio incompatible se discute antes con el equipo.

Son tres piezas que conectan el trabajo de varios roles. Si se acuerdan
ahora, cada uno puede avanzar en paralelo sin esperar al resto:

```
             Percepcion                         eventos (eventos.py)
 partido.py ────────────► Controlador          ┌──► aptitud.py   (R2)
   (R1)     ◄──────────── (IA, rival, humano)  ├──► metricas.py  (R4)
                Accion                         └──► grabación ──► ver2d / ver3d (R3)
```

## 1. El controlador (`controlador.py`)

Todo lo que juega (la IA, el rival programado, el humano) hereda de
`Controlador` e implementa un método:

```python
class MiControlador(Controlador):
    nombre = "rival programado"

    def reiniciar(self):              # opcional: al empezar cada punto
        ...

    def decidir(self, percepcion: Percepcion) -> Accion:
        ...
```

### Marco propio (espejo)

Cada controlador ve el mundo **como si jugara a la izquierda**, con la red
hacia +x. El jugador derecho recibe la percepción reflejada
(`espejar_percepcion`) y su acción se convierte de vuelta en `jugador.py`.

| | Al reflejar (jugador derecho) |
|---|---|
| Posiciones x (pelota, propio, rival) | `x → ANCHO_CANCHA − x` |
| Velocidad horizontal de la pelota | `vx → −vx` |
| Ángulo de la raqueta | `θ → π − θ` (`reflejar_angulo`) |
| `y`, `vy`, `en_suelo`, `recarga` | no cambian |
| `Accion.mover` | `jugador.py` invierte el signo |
| `Accion.angulo_raqueta` | `jugador.py` lo traduce al rango de config y aplica `reflejar_angulo` |

### `Percepcion` (12 valores, unidades físicas, sin normalizar)

| Campo | Significado |
|---|---|
| `pelota_x`, `pelota_y`, `pelota_vx`, `pelota_vy` | posición y velocidad de la pelota |
| `propio_x`, `propio_y`, `propio_vy` | posición y velocidad vertical del jugador |
| `en_suelo` | `True` si puede saltar |
| `raqueta_angulo` | radianes; 0 = horizontal hacia la red, positivo = arriba |
| `recarga` | segundos que faltan para poder golpear (0 = listo) |
| `rival_x`, `rival_y` | posición del rival |

Normalizar a [−1, 1] para la red es trabajo de `percepcion.py` (R2): el rival
programado prefiere los valores físicos, y así `partido.py` no depende de la red.

### `Accion` (siempre en el marco propio)

| Campo | Rango | Significado |
|---|---|---|
| `mover` | −1 a 1 | 1 = hacia la red a velocidad máxima |
| `saltar` | bool | se ignora si no está en el suelo |
| `angulo_raqueta` | −1 a 1 | se traduce a `ANGULO_RAQUETA_MIN..MAX` |
| `golpe` | 0 a 1 | 0 = no golpear; si no, fuerza del golpe |

`Accion` recorta sus valores al crearse, para que ningún controlador pueda
romper la física. **El umbral del golpe lo decide cada controlador**: la IA
convierte su salida tanh (por ejemplo, `golpe = 0` si la salida es menor que el
umbral); el humano manda `golpe = 1` al apretar la tecla.

### Reglas del contrato

1. `decidir()` se llama cada `PASOS_POR_DECISION` pasos; la acción se mantiene entre llamadas.
2. Si un controlador usa azar, recibe su propio `random.Random(semilla)` y nunca usa `random` global (reproducibilidad).
3. La IA y el rival programado deben poder enviarse a otros procesos (`multiprocessing`): sin ventanas, teclado ni archivos abiertos.
4. `ControladorQuieto` (no hace nada) sirve para pruebas y para que R1 avance en F1 sin esperar a la IA.

## 2. Los eventos (`eventos.py`)

El árbitro produce una lista de eventos por partido. Son diccionarios con
`tipo` y `t` (segundos desde el inicio del partido), en coordenadas del mundo.
Se crean con `eventos.evento(tipo, t, **campos)`, que rechaza tipos o motivos
mal escritos.

| Tipo | Campos |
|---|---|
| `saque` | `hacia` (lado que recibe) |
| `golpe` | `jugador`, `x`, `y` (de la pelota), `fuerza` — un **contacto** pelota-raqueta |
| `bote` | `x`, `campo` (lado donde botó), `golpeador` (lado o `None` si viene del saque), `valido` |
| `red` | `golpeador` |
| `punto` | `ganador` (lado o `None`), `motivo`, `golpes_validos`, `distancia_minima` |

Motivos de fin de punto: `doble_bote`, `bote_propio` (incluye la red),
`fuera`, `techo`, `anulado` (tiempo agotado).

Con esto se calculan las aptitudes y las métricas sin volver a simular. Por
ejemplo: duración del peloteo = `golpes_validos` del evento `punto`;
profundidad = `|x − X_RED|` de los `bote` con `valido = True`; punto ganador
vs. error propio = `doble_bote` frente a `bote_propio`, `fuera` o `techo`
(esta clasificación la confirma R4 en `metricas.py`).

## 3. La grabación (`grabar.py`)

Un archivo JSON por partido. Los visores **solo** leen esto: nunca importan
la física.

```json
{
  "formato": "tenis_evolutivo/grabacion",
  "version": 1,
  "meta": {"jugadores": ["IA gen 120", "rival programado"], "fecha": "2026-11-10T21:03:00",
           "tratamiento": "A", "generacion": 120, "semilla": 3},
  "cancha": {"ancho": 1200, "x_red": 600, "alto_red": 60, "techo": 600, "radio_pelota": 8,
             "tamano_jugador": 40, "largo_raqueta": 50, "grosor_raqueta": 8},
  "dt_cuadro": 0.016667,
  "columnas": ["t", "pelota_x", "pelota_y",
               "izq_x", "izq_y", "izq_raqueta_x", "izq_raqueta_y", "izq_raqueta_angulo",
               "der_x", "der_y", "der_raqueta_x", "der_raqueta_y", "der_raqueta_angulo"],
  "cuadros": [[0.0, 600.0, 60.0, 300.0, 20.0, 330.0, 25.0, 0.2, 900.0, 20.0, 870.0, 25.0, 2.942]],
  "eventos": [{"tipo": "saque", "t": 0.0, "hacia": 0}]
}
```

Decisiones y por qué:

- **Cuadros como listas de números, no diccionarios:** un partido tiene miles de cuadros; repetir los nombres en cada uno haría el archivo varias veces más grande. Los nombres van una sola vez en `columnas` (y `cuadro_como_dict` los recupera).
- **Coordenadas del mundo**, no del marco propio: el visor dibuja lo que pasó, sin espejos.
- **Raqueta como centro + ángulo:** el visor la dibuja sin saber cómo está unida al cubo, así R1 puede cambiar el pivote sin romper los visores.
- **Las medidas de la cancha se copian al archivo:** si `config.py` cambia, las grabaciones viejas se siguen viendo bien.
- **60 cuadros por segundo** (`PASOS_POR_CUADRO = 1`) para que la cámara lenta del 3D se vea fluida; posiciones redondeadas a 1 decimal y ángulos a 3. Un partido de 6 puntos pesa del orden de unos cientos de KB.
- **`version`:** `cargar_grabacion` rechaza versiones que no conoce, en lugar de dibujar basura.

## 4. `partido.py` (definida en F1)

```python
def jugar_partido(ctrl_izq, ctrl_der, semilla, puntos=config.PUNTOS_POR_PARTIDO,
                  grabacion=None, saque=None, receptor_fijo=None) -> list[dict]:
    """Simula un partido y devuelve la lista de eventos. Si se pasa una
    grabación (grabar.nueva_grabacion), además la va llenando cuadro a cuadro.
    saque(azar, receptor) -> (x, y, vx, vy) reemplaza el saque neutro
    (lo usa el lanzapelotas de la etapa 1). receptor_fijo (0 o 1) hace que
    todas las pelotas vayan al mismo jugador (agregado en F2b, compatible)."""
```

## Decisiones tomadas en F1 (las tres aclaraciones)

1. **`golpe` = contacto.** El evento `golpe` se produce cuando la pelota toca
   la raqueta, no cuando el jugador hace el swing. Un swing al aire no deja
   rastro; un toque sin swing (raqueta quieta) sí, con `fuerza = 0`.
2. **`distancia_minima` en el evento `punto`.** Lista `[izq, der]` con la menor
   distancia entre la pelota y cada raqueta durante el punto. La etapa 1
   premia "acercarse a la pelota cuando no la toca" y no hay otra forma de
   saberlo sin volver a simular. Es un campo nuevo: compatible.
3. **El lanzapelotas usa el evento `saque`.** Cada lanzamiento de la etapa 1
   es un `saque` normal (con `hacia`); `jugar_partido` recibe la función
   `saque` para cambiar cómo se lanza la pelota. No hace falta un tipo nuevo.

Respuestas a los puntos que quedaron abiertos en F0:

- Las 12 entradas se mantienen por ahora; se revisará en F2b si a la red le falta información.
- El umbral del golpe lo decide cada controlador (como estaba propuesto).
- 60 cuadros por segundo: una grabación de 6 puntos pesa unos 300 KB, aceptable.
- La firma de `jugar_partido` es la de arriba.
