# Interfaces comunes — propuesta F0

> **Estado: PROPUESTA, pendiente de acuerdo del equipo.** Cuando todos la
> acepten, cambiar esta línea a "Acordada el <fecha>". Desde entonces, cualquier
> cambio incompatible se discute antes con el equipo.

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
| `golpe` | `jugador`, `x`, `y`, `fuerza` |
| `bote` | `x`, `campo` (lado donde botó), `golpeador` (lado o `None` si viene del saque), `valido` |
| `red` | `golpeador` |
| `punto` | `ganador` (lado o `None`), `motivo`, `golpes_validos` |

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

## 4. Sugerencia para `partido.py` (la define R1 en F1)

Para que R2, R3 y R4 puedan escribir código contra ella desde ya:

```python
def jugar_partido(ctrl_izq, ctrl_der, semilla, puntos=config.PUNTOS_POR_PARTIDO,
                  grabacion=None) -> list[dict]:
    """Simula un partido y devuelve la lista de eventos. Si se pasa una
    grabación (grabar.nueva_grabacion), además la va llenando cuadro a cuadro."""
```

## Puntos para decidir en la reunión

- [ ] ¿Las 12 entradas alcanzan, o se agrega algo (por ejemplo, la velocidad horizontal propia)?
- [ ] ¿`golpe` como fuerza 0..1 con umbral en cada controlador, o umbral común en `jugador.py`?
- [ ] ¿60 cuadros por segundo o 30 (`PASOS_POR_CUADRO = 2`, archivos de la mitad de tamaño)?
- [ ] ¿La firma sugerida de `jugar_partido` le sirve a R1?
