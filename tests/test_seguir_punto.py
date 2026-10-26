"""
Pruebas del ejercicio F2a (ejercicios/seguir_punto.py).

Sirven también como ejemplos: cada prueba comprueba una idea del capítulo 3
(qué calcula una neurona, qué significan los pesos, que la evolución mejora).
"""

import math
import random

import pytest

from ejercicios import seguir_punto as sp


def test_una_neurona_hace_suma_ponderada_mas_sesgo_y_tanh():
    # pesos (0,5 y −1), entradas (1 y 2), sesgo 0,25:
    # 0,5·1 + (−1)·2 + 0,25 = −1,25  →  tanh(−1,25) ≈ −0,848
    assert sp.neurona([0.5, -1.0], 0.25, [1.0, 2.0]) == pytest.approx(math.tanh(-1.25))
    assert sp.neurona([0.5, -1.0], 0.25, [1.0, 2.0]) == pytest.approx(-0.848, abs=1e-3)


def test_tamano_del_genoma():
    # 4 ocultas × (4 pesos + 1 sesgo) + 2 salidas × (4 pesos + 1 sesgo) = 20 + 10
    assert sp.tamano_genoma() == 30
    assert len(sp.red_a_mano()) == 30


def test_una_red_con_todo_en_cero_no_hace_nada():
    assert sp.propagar([0.0] * sp.tamano_genoma(), [0.3, -0.2, 0.5, 0.1]) == [0.0, 0.0]


def test_la_red_a_mano_acelera_hacia_el_objetivo_y_frena():
    red = sp.red_a_mano()
    ax, ay = sp.propagar(red, [0.5, 0.0, 0.0, 0.0])    # objetivo a la derecha, quieto
    assert ax > 0 and ay == pytest.approx(0.0)
    ax, ay = sp.propagar(red, [0.0, 0.0, 0.5, 0.0])    # ya en el objetivo pero moviéndose a la derecha
    assert ax < 0                                       # frena


def test_la_red_a_mano_persigue_mejor_que_una_al_azar():
    al_azar = sp.genoma_al_azar(random.Random(0))
    assert sp.comparar(sp.red_a_mano()) < 0.5 * sp.comparar(al_azar)


def test_la_evolucion_mejora():
    # Criterio de F2a: "el ejercicio aprende". En 15 generaciones el campeón
    # debe perseguir al menos el doble de bien que el de la generación 0.
    _, campeones = sp.evolucionar(semilla=1, generaciones=15)
    assert sp.comparar(campeones[-1]) < 0.5 * sp.comparar(campeones[0])


def test_misma_semilla_misma_evolucion():
    a, _ = sp.evolucionar(semilla=3, generaciones=3)
    b, _ = sp.evolucionar(semilla=3, generaciones=3)
    assert a == b


def test_el_elitismo_conserva_a_los_mejores():
    azar = random.Random(0)
    poblacion = [sp.genoma_al_azar(azar) for _ in range(sp.POBLACION)]
    aptitudes = list(range(sp.POBLACION))               # el último es el mejor
    nueva = sp.siguiente_generacion(poblacion, aptitudes, azar)
    assert nueva[0] == poblacion[-1] and nueva[1] == poblacion[-2]
    assert len(nueva) == sp.POBLACION
