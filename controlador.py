"""
controlador.py — INTERFAZ COMÚN entre quien juega y la simulación.

Decidida en F1 (ver docs/libro/cap00_preparacion.md). No se cambia sin avisar
a todos (ver CLAUDE.md y docs/interfaces.md).

Idea central: partido.py no sabe quién juega. La IA, el rival programado y el
humano son "controladores": reciben una Percepcion y devuelven una Accion.

Marco propio (simetría, sección 3.6 del plan): todo controlador ve el mundo
como si jugara en el lado IZQUIERDO, con la red hacia la derecha (+x). Así una
misma red neuronal sirve en cualquier lado. partido.py refleja la percepción
del jugador derecho con espejar_percepcion(), y jugador.py convierte la acción
de vuelta al mundo.
"""

import math
from dataclasses import dataclass, replace

import config

IZQUIERDA = 0
DERECHA = 1


@dataclass(frozen=True)
class Percepcion:
    """
    Lo que un jugador "ve" en un instante, en unidades físicas SIN normalizar.

    Normalizar a [-1, 1] es tarea de percepcion.py (R2), porque solo la red
    neuronal lo necesita; el rival programado prefiere los valores físicos.
    """

    pelota_x: float
    pelota_y: float
    pelota_vx: float
    pelota_vy: float
    propio_x: float
    propio_y: float
    propio_vy: float
    en_suelo: bool
    raqueta_angulo: float   # radianes; 0 = horizontal hacia la red, positivo = arriba
    recarga: float          # segundos que faltan para poder golpear (0 = listo)
    rival_x: float
    rival_y: float


@dataclass
class Accion:
    """
    Lo que un jugador quiere hacer. Valores siempre en el marco propio.

    - mover: -1 (alejarse de la red) a 1 (acercarse); se multiplica por la velocidad máxima.
    - saltar: True para saltar (jugador.py lo ignora si no está en el suelo).
    - angulo_raqueta: -1 a 1, se traduce al rango ANGULO_RAQUETA_MIN..MAX de config.
    - golpe: 0 = no golpear; de 0 a 1 = golpear con esa fuerza. Cada controlador
      decide su propio umbral (la IA, por ejemplo, convierte su salida tanh).
    """

    mover: float = 0.0
    saltar: bool = False
    angulo_raqueta: float = 0.0
    golpe: float = 0.0

    def __post_init__(self):
        # Se recorta en UN solo lugar para que ningún controlador (ni un bug)
        # pueda pedirle a la física valores fuera de rango.
        self.mover = _limitar(self.mover, -1.0, 1.0)
        self.saltar = bool(self.saltar)
        self.angulo_raqueta = _limitar(self.angulo_raqueta, -1.0, 1.0)
        self.golpe = _limitar(self.golpe, 0.0, 1.0)


class Controlador:
    """
    Clase base. Cada tipo de jugador hereda de ella y redefine decidir().

    Reglas del contrato:
    - partido.py llama a decidir() cada PASOS_POR_DECISION pasos de física; la
      acción se mantiene igual en los pasos intermedios.
    - reiniciar() se llama al empezar cada punto (útil si el controlador
      guarda memoria, como un rival que "planea" su golpe).
    - Si el controlador usa azar, recibe su propio random.Random(semilla) al
      crearse y NUNCA usa el módulo random global: así la misma semilla da
      siempre el mismo partido, incluso evaluando en paralelo.
    - Debe poder copiarse entre procesos (multiprocessing): nada de ventanas,
      archivos abiertos ni teclado dentro de la IA o del rival programado.
    """

    nombre = "controlador"   # aparece en las grabaciones y en el marcador

    def reiniciar(self):
        pass

    def decidir(self, percepcion: Percepcion) -> Accion:
        raise NotImplementedError("Cada controlador debe implementar decidir()")


class ControladorQuieto(Controlador):
    """No hace nada. Sirve para pruebas y para avanzar en F1 sin esperar a la IA."""

    nombre = "quieto"

    def decidir(self, percepcion):
        return Accion()


def espejar_percepcion(p: Percepcion) -> Percepcion:
    """
    Refleja la percepción del jugador DERECHO para que la vea como si estuviera
    a la izquierda: las x se reflejan respecto del centro y las velocidades
    horizontales cambian de signo. Lo vertical no cambia.

    Recibe la raqueta en ángulo del MUNDO (medido desde +x, antihorario) y la
    devuelve en el marco propio.
    """
    return replace(
        p,
        pelota_x=config.ANCHO_CANCHA - p.pelota_x,
        pelota_vx=-p.pelota_vx,
        propio_x=config.ANCHO_CANCHA - p.propio_x,
        rival_x=config.ANCHO_CANCHA - p.rival_x,
        raqueta_angulo=reflejar_angulo(p.raqueta_angulo),
    )


def reflejar_angulo(angulo):
    """
    Refleja un ángulo respecto del eje vertical: θ -> π - θ, dejado en (-π, π].

    Sirve en los dos sentidos (mundo -> propio y propio -> mundo), porque
    reflejar dos veces deja todo como estaba. jugador.py la usa para aplicar
    el ángulo de la raqueta del jugador derecho.
    """
    reflejado = math.pi - angulo
    return math.atan2(math.sin(reflejado), math.cos(reflejado))


def _limitar(valor, minimo, maximo):
    return max(minimo, min(maximo, float(valor)))
