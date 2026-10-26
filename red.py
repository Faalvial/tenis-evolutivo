"""
red.py — La red neuronal de los jugadores y el controlador que la usa.

Es la misma red del ejercicio del capítulo 3 (ejercicios/seguir_punto.py),
más grande: 14 entradas (percepcion.py), OCULTAS neuronas ocultas y 4 salidas,
todas con tanh. El genoma es la lista de todos los pesos y sesgos, agrupados
POR NEURONA (pesos de entrada y después el sesgo): genetico.py aprovecha ese
orden para cruzar neuronas completas.

Salidas -> Accion (controlador.py):
  0  mover            -1 a 1, tal cual
  1  saltar           si es mayor que 0
  2  angulo_raqueta   -1 a 1, tal cual
  3  golpe            si supera UMBRAL_GOLPE: fuerza de 0 a 1 según cuánto lo supera

Uso desde la terminal:
    python red.py --medir      compara la velocidad de Python puro y NumPy
"""

import math

import config
import percepcion
from controlador import Accion, Controlador

N_SALIDAS = 4


def tamano_genoma(ocultas=None):
    """Pesos y sesgos de las dos capas: (14 + 1) · ocultas + (ocultas + 1) · 4."""
    ocultas = config.OCULTAS if ocultas is None else ocultas
    return ocultas * (percepcion.N_ENTRADAS + 1) + N_SALIDAS * (ocultas + 1)


def bloques_neuronas(ocultas=None):
    """
    Dónde empieza y termina cada neurona dentro del genoma: [(inicio, fin), ...].
    Una neurona = sus pesos de entrada + su sesgo. Lo usa el cruce por neurona.
    """
    ocultas = config.OCULTAS if ocultas is None else ocultas
    bloques, i = [], 0
    for n_entradas, n_neuronas in ((percepcion.N_ENTRADAS, ocultas), (ocultas, N_SALIDAS)):
        for _ in range(n_neuronas):
            bloques.append((i, i + n_entradas + 1))
            i += n_entradas + 1
    return bloques


class Red:
    """
    Una red ya "armada": separa el genoma en neuronas UNA vez, al crearla, para
    no tener que cortar la lista en cada decisión (se decide 30 veces por
    segundo de juego, miles de veces por partido).
    """

    def __init__(self, genoma, ocultas=None):
        ocultas = config.OCULTAS if ocultas is None else ocultas
        if len(genoma) != tamano_genoma(ocultas):
            raise ValueError(f"El genoma tiene {len(genoma)} números y la red necesita "
                             f"{tamano_genoma(ocultas)}")
        neuronas = [(list(genoma[a:b - 1]), genoma[b - 1]) for a, b in bloques_neuronas(ocultas)]
        self.capa_oculta = neuronas[:ocultas]
        self.capa_salida = neuronas[ocultas:]

    def propagar(self, entradas):
        """Propagación hacia adelante (capítulo 3): entradas -> ocultas -> salidas."""
        ocultas = _capa(self.capa_oculta, entradas)
        return _capa(self.capa_salida, ocultas)


def _capa(neuronas, entradas):
    salidas = []
    for pesos, sesgo in neuronas:
        suma = sesgo
        for w, x in zip(pesos, entradas):
            suma += w * x
        salidas.append(math.tanh(suma))
    return salidas


def salidas_a_accion(salidas):
    """Traduce las 4 salidas de la red (tanh, de -1 a 1) a una Accion."""
    mover, saltar, angulo, golpe = salidas
    fuerza = 0.0
    if golpe > config.UMBRAL_GOLPE:
        # De apenas encima del umbral (fuerza ~0) a 1 (fuerza 1).
        fuerza = (golpe - config.UMBRAL_GOLPE) / (1.0 - config.UMBRAL_GOLPE)
        fuerza = max(fuerza, 0.01)   # golpe = 0 significa "no golpear"
    return Accion(mover=mover, saltar=saltar > 0.0, angulo_raqueta=angulo, golpe=fuerza)


class ControladorRed(Controlador):
    """Un jugador controlado por una red neuronal. No usa azar: es determinista."""

    def __init__(self, genoma, nombre="IA"):
        self.red = Red(genoma)
        self.nombre = nombre

    def decidir(self, p):
        return salidas_a_accion(self.red.propagar(percepcion.normalizar(p)))


# --- Medición: ¿Python puro o NumPy? (sección 4 del plan) ---

def _medir():
    import random
    import time

    import numpy as np

    azar = random.Random(0)
    genoma = [azar.gauss(0, 1) for _ in range(tamano_genoma())]
    entradas = [azar.uniform(-1, 1) for _ in range(percepcion.N_ENTRADAS)]
    repeticiones = 20000

    red = Red(genoma)
    inicio = time.perf_counter()
    for _ in range(repeticiones):
        red.propagar(entradas)
    puro = (time.perf_counter() - inicio) / repeticiones

    # La misma red con matrices de NumPy: W1 (ocultas × entradas), W2 (salidas × ocultas).
    w1 = np.array([p for p, _ in red.capa_oculta])
    b1 = np.array([b for _, b in red.capa_oculta])
    w2 = np.array([p for p, _ in red.capa_salida])
    b2 = np.array([b for _, b in red.capa_salida])
    x = np.array(entradas)
    inicio = time.perf_counter()
    for _ in range(repeticiones):
        np.tanh(w2 @ np.tanh(w1 @ x + b1) + b2)
    con_numpy = (time.perf_counter() - inicio) / repeticiones

    # Con NumPy, además, hay que convertir la lista de entradas en un arreglo cada vez.
    inicio = time.perf_counter()
    for _ in range(repeticiones):
        np.tanh(w2 @ np.tanh(w1 @ np.array(entradas) + b1) + b2)
    con_numpy_y_conversion = (time.perf_counter() - inicio) / repeticiones

    print(f"Red {percepcion.N_ENTRADAS}-{config.OCULTAS}-{N_SALIDAS} ({tamano_genoma()} números), "
          f"{repeticiones} propagaciones:")
    print(f"  Python puro                     {puro * 1e6:6.1f} µs")
    print(f"  NumPy (entradas ya en arreglo)  {con_numpy * 1e6:6.1f} µs")
    print(f"  NumPy (convirtiendo entradas)   {con_numpy_y_conversion * 1e6:6.1f} µs")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Red neuronal de los jugadores.")
    parser.add_argument("--medir", action="store_true", help="comparar Python puro y NumPy")
    if parser.parse_args().medir:
        _medir()
