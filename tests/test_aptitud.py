"""Pruebas de las aptitudes (aptitud.py): etapas 1 y 2 y las A, B y C de la etapa 3, con eventos inventados."""

import pytest

import config
import eventos
from aptitud import anulados, aptitud_A, aptitud_B, aptitud_C, aptitud_etapa1, aptitud_etapa2


def lanzamiento(*intermedios, ganador=1, motivo="doble_bote", validos=0, distancia=500.0):
    evs = [eventos.evento(eventos.SAQUE, 0.0, hacia=0)]
    evs += list(intermedios)
    evs.append(eventos.evento(eventos.PUNTO, 2.0, ganador=ganador, motivo=motivo,
                              golpes_validos=validos))
    evs[-1]["distancia_minima"] = [distancia, 900.0]
    return evs


def golpe(t=1.0):
    return eventos.evento(eventos.GOLPE, t, jugador=0, x=200.0, y=40.0, fuerza=0.5)


def bote(x, t=1.5, valido=False):
    return eventos.evento(eventos.BOTE, t, x=x, campo=None, golpeador=0, valido=valido)


def test_no_tocar_ni_acercarse_vale_cero():
    assert aptitud_etapa1(lanzamiento(distancia=500.0)) == (0.0, 0.0)


def test_acercarse_sin_tocar_vale_menos_que_tocar():
    apt, _ = aptitud_etapa1(lanzamiento(distancia=0.0))
    assert apt == pytest.approx(config.PREMIO_CERCANIA)
    assert apt < config.PREMIO_TOQUE


def test_tocar_y_a_la_red():
    evs = lanzamiento(golpe(), eventos.evento(eventos.RED, 1.2, golpeador=0), motivo="bote_propio")
    assert aptitud_etapa1(evs) == (config.PREMIO_TOQUE, 0.0)


def test_tocar_y_cruzar_pero_fuera():
    evs = lanzamiento(golpe(), bote(config.ANCHO_CANCHA + 50), motivo="fuera")
    assert aptitud_etapa1(evs)[0] == config.PREMIO_TOQUE + config.PREMIO_CRUZA


def test_devolucion_valida_vale_todo():
    evs = lanzamiento(golpe(), bote(900.0, valido=True), bote(1100.0, t=1.8), ganador=0, validos=1)
    apt, devueltas = aptitud_etapa1(evs)
    assert apt == config.PREMIO_TOQUE + config.PREMIO_CRUZA + config.PREMIO_DENTRO
    assert devueltas == 1.0


def test_promedia_por_lanzamiento():
    buena = lanzamiento(golpe(), bote(900.0, valido=True), ganador=0, validos=1)
    mala = lanzamiento(distancia=500.0)
    apt, devueltas = aptitud_etapa1(buena + mala)
    assert apt == pytest.approx((config.PREMIO_TOQUE + config.PREMIO_CRUZA + config.PREMIO_DENTRO) / 2)
    assert devueltas == 0.5


def test_aptitud_etapa2_puntos_ganados_mas_devoluciones():
    # Punto 1: devuelve dos veces bien y gana. Punto 2: devuelve una vez y pierde.
    gana = lanzamiento(golpe(), bote(900.0, valido=True), golpe(2.0), bote(950.0, t=2.5, valido=True),
                       ganador=0, validos=3)
    pierde = lanzamiento(golpe(), bote(900.0, valido=True), ganador=1, validos=2)
    apt, ganados = aptitud_etapa2(gana + pierde)
    assert ganados == 0.5
    assert apt == pytest.approx((1 + config.PESO_DEVOLUCIONES * 3) / 2)


# --- Etapa 3: A, B y C (sección 7 del plan) ---

def golpe_de(lado, t=1.0):
    return eventos.evento(eventos.GOLPE, t, jugador=lado, x=300.0, y=40.0, fuerza=0.5)


def bote_de(lado, x, t=1.5):
    return eventos.evento(eventos.BOTE, t, x=x, campo=1 - lado, golpeador=lado, valido=True)


def partido_ejemplo():
    """Tres puntos, mirados desde el jugador 0."""
    profundo = config.X_RED + 0.9 * (config.ANCHO_CANCHA - config.X_RED)   # último tercio
    corto = config.X_RED + 0.3 * (config.ANCHO_CANCHA - config.X_RED)
    p1 = lanzamiento(golpe_de(0), bote_de(0, profundo), ganador=0, motivo="doble_bote", validos=1)
    p2 = lanzamiento(golpe_de(0), bote_de(0, corto), golpe_de(1), bote_de(1, 300.0),
                     golpe_de(0, 2.0), ganador=1, motivo="fuera", validos=2)
    p3 = lanzamiento(golpe_de(0), bote_de(0, corto), ganador=None, motivo="anulado", validos=6)
    return p1 + p2 + p3


def test_aptitud_A_no_cuenta_los_anulados():
    # Ganó 1, perdió 1, el tercero se anuló: (1 − 1) / 2 = 0.
    assert aptitud_A([(partido_ejemplo(), 0)]) == 0.0


def test_aptitud_A_desde_los_dos_lados():
    evs = partido_ejemplo()
    # Visto desde el jugador 1 es al revés; juntos, también 0.
    assert aptitud_A([(evs, 1)]) == 0.0
    solo_gana = lanzamiento(golpe_de(0), bote_de(0, 1100.0), ganador=0, motivo="doble_bote", validos=1)
    assert aptitud_A([(solo_gana, 0)]) == 1.0 and aptitud_A([(solo_gana, 1)]) == -1.0


def test_aptitud_B_es_la_misma_para_los_dos_y_cuenta_los_anulados():
    evs = partido_ejemplo()
    assert aptitud_B([(evs, 0)]) == aptitud_B([(evs, 1)]) == pytest.approx((1 + 2 + 6) / 3)
    assert anulados([(evs, 0)]) == pytest.approx(1 / 3)


def test_aptitud_C_profundos_menos_errores():
    # Jugador 0: 4 golpes. Profundos y válidos: 1 (punto 1). Fallidos: 1 (último golpe del punto 2).
    assert aptitud_C([(partido_ejemplo(), 0)]) == pytest.approx((1 - 1) / 4)
    # Jugador 1: no devolvió la pelota del punto 1 (1 intento fallido) y golpeó
    # una vez, corto, en el punto 2 sin error: (0 − 1) / 2.
    assert aptitud_C([(partido_ejemplo(), 1)]) == pytest.approx(-0.5)


def test_aptitud_C_no_jugar_ya_no_conviene():
    # La trampa de la corrida corta de F4: un jugador que nunca golpea pierde
    # todos los puntos por doble bote. Con el ajuste, eso vale −1 (el mínimo).
    no_juega = (lanzamiento(ganador=1, motivo="doble_bote", validos=0)
                + lanzamiento(ganador=1, motivo="doble_bote", validos=0))
    assert aptitud_C([(no_juega, 0)]) == -1.0
