"""Pruebas de la red de los jugadores (red.py) y de la normalización (percepcion.py)."""

import pickle
import random

import pytest

import config
import partido
import percepcion
import red
from controlador import Accion, Percepcion
from jugador import Jugador
from mundo import Mundo


def genoma_al_azar(semilla=0):
    azar = random.Random(semilla)
    return [azar.gauss(0, 1) for _ in range(red.tamano_genoma())]


def test_tamano_y_bloques_del_genoma():
    # 8 ocultas × (14 + 1) + 4 salidas × (8 + 1) = 120 + 36
    assert red.tamano_genoma() == 156
    bloques = red.bloques_neuronas()
    assert len(bloques) == config.OCULTAS + red.N_SALIDAS
    assert bloques[0][0] == 0 and bloques[-1][1] == red.tamano_genoma()
    assert all(a[1] == b[0] for a, b in zip(bloques, bloques[1:]))    # sin huecos


def test_la_red_rechaza_un_genoma_del_tamano_equivocado():
    with pytest.raises(ValueError):
        red.Red([0.0] * 10)


def test_red_en_cero_da_salidas_en_cero():
    assert red.Red([0.0] * red.tamano_genoma()).propagar([0.5] * percepcion.N_ENTRADAS) == [0.0] * 4


def test_salidas_a_accion():
    a = red.salidas_a_accion([0.5, 0.2, -0.3, config.UMBRAL_GOLPE - 0.01])
    assert (a.mover, a.saltar, a.angulo_raqueta, a.golpe) == (0.5, True, -0.3, 0.0)
    assert red.salidas_a_accion([0, -0.1, 0, 1.0]).golpe == pytest.approx(1.0)
    assert red.salidas_a_accion([0, -0.1, 0, 1.0]).saltar is False
    media = (1 + config.UMBRAL_GOLPE) / 2
    assert red.salidas_a_accion([0, 0, 0, media]).golpe == pytest.approx(0.5)


def test_el_controlador_de_red_se_puede_enviar_a_otro_proceso():
    c = red.ControladorRed(genoma_al_azar())
    copia = pickle.loads(pickle.dumps(c))     # lo que hace multiprocessing
    p = Percepcion(300, 100, -200, 50, 300, 20, 0, True, -0.9, 0, 900, 20)
    assert copia.decidir(p) == c.decidir(p)
    assert isinstance(c.decidir(p), Accion)


def test_normalizar_da_14_valores_entre_menos_uno_y_uno():
    p = Percepcion(pelota_x=2000, pelota_y=900, pelota_vx=-5000, pelota_vy=300,
                   propio_x=-400, propio_y=20, propio_vy=0, en_suelo=True,
                   raqueta_angulo=-0.9, recarga=0.4, rival_x=900, rival_y=20)
    valores = percepcion.normalizar(p)
    assert len(valores) == percepcion.N_ENTRADAS
    assert all(-1.0 <= v <= 1.0 for v in valores)
    assert valores[4] == pytest.approx(-1.0)      # parado en el fondo del espacio detrás


def test_los_dos_jugadores_ven_lo_mismo_en_situaciones_espejadas():
    # El izquierdo con la pelota a 200 de él, y el derecho con la pelota a 200
    # de él (del otro lado): sus entradas normalizadas deben ser iguales.
    mundo = Mundo()
    jugadores = (Jugador(mundo, 0, 300.0), Jugador(mundo, 1, 900.0))
    mundo.colocar_pelota(500.0, 150.0, -300.0, 100.0)
    izq = percepcion.normalizar(partido.percibir(mundo, jugadores, 0))
    mundo.colocar_pelota(700.0, 150.0, 300.0, 100.0)
    der = percepcion.normalizar(partido.percibir(mundo, jugadores, 1))
    assert izq == pytest.approx(der)
