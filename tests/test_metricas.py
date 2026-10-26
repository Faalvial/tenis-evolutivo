"""Pruebas de las métricas de la sección 8 (metricas.py), con eventos inventados y una batería real corta."""

import pytest

import config
import eventos
import metricas
from rivales import RivalProgramado


def punto(*intermedios, ganador, motivo, validos):
    evs = [eventos.evento(eventos.SAQUE, 0.0, hacia=0), *intermedios,
           eventos.evento(eventos.PUNTO, 1.0, ganador=ganador, motivo=motivo, golpes_validos=validos)]
    return evs


def golpe(lado=0):
    return eventos.evento(eventos.GOLPE, 0.5, jugador=lado, x=300.0, y=40.0, fuerza=0.5)


def bote(x, golpeador=0, valido=True):
    return eventos.evento(eventos.BOTE, 0.7, x=x, campo=1, golpeador=golpeador, valido=valido)


def test_metricas_de_tres_puntos():
    evs = (punto(golpe(), bote(1100.0), ganador=0, motivo="doble_bote", validos=1)    # ganador
           + punto(golpe(), ganador=1, motivo="fuera", validos=0)                     # error propio
           + punto(ganador=None, motivo="anulado", validos=0))
    m = metricas.calcular(evs)
    assert m["ganados"] == pytest.approx(1 / 3)
    assert m["peloteo"] == pytest.approx(1 / 3)
    assert m["golpes_validos"] == pytest.approx(1 / 2)
    assert m["profundidad"] == pytest.approx(1100.0 - config.X_RED)
    assert m["ganadores"] == pytest.approx(1 / 3)
    assert m["errores"] == pytest.approx(1 / 3)
    assert m["anulados"] == pytest.approx(1 / 3)
    assert m["botes"] == [1100.0]


def test_la_bateria_es_siempre_la_misma():
    a = metricas.medir(RivalProgramado(5), puntos=10)
    b = metricas.medir(RivalProgramado(5), puntos=10)
    assert a == b


def test_el_rival_programado_contra_si_mismo_gana_cerca_de_la_mitad():
    m = metricas.medir(RivalProgramado(5), puntos=60)
    assert 0.3 <= m["ganados"] <= 0.7
    assert m["peloteo"] > 2
