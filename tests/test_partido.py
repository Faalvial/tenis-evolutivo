"""
Pruebas del partido completo (partido.py + rivales.py).

Incluyen dos criterios de aceptación de F1:
- dos rivales programados pelotean;
- la misma semilla da exactamente el mismo partido (reproducibilidad).
"""

import math

import pytest

import config
import eventos
import grabar
import partido
from controlador import ControladorQuieto, Percepcion, espejar_percepcion
from jugador import Jugador
from mundo import Mundo
from rivales import RivalProgramado, prediccion_golpe, rapidez_para_llegar, tiempo_hasta_altura


def puntos_de(evs):
    return [ev for ev in evs if ev["tipo"] == eventos.PUNTO]


def test_misma_semilla_mismo_partido():
    a = partido.jugar_partido(RivalProgramado(1), RivalProgramado(2), semilla=7)
    b = partido.jugar_partido(RivalProgramado(1), RivalProgramado(2), semilla=7)
    assert a == b


def test_otra_semilla_otro_partido():
    a = partido.jugar_partido(RivalProgramado(1), RivalProgramado(2), semilla=7)
    b = partido.jugar_partido(RivalProgramado(1), RivalProgramado(2), semilla=8)
    assert a != b


def test_jugadores_quietos_pierden_el_saque_que_reciben():
    # Nadie se mueve: o el saque bota dos veces en el campo del receptor, o la
    # pelota toca sin querer su raqueta quieta y después bota en su campo.
    # En los dos casos pierde el receptor.
    evs = partido.jugar_partido(ControladorQuieto(), ControladorQuieto(), semilla=3, puntos=6)
    puntos = puntos_de(evs)
    assert len(puntos) == 6
    receptores = [ev["hacia"] for ev in evs if ev["tipo"] == eventos.SAQUE]
    assert receptores == [0, 1, 0, 1, 0, 1]     # saques alternados
    for receptor, p in zip(receptores, puntos):
        assert p["motivo"] in (eventos.DOBLE_BOTE, eventos.BOTE_PROPIO)
        assert p["ganador"] == 1 - receptor


def test_dos_rivales_programados_pelotean():
    # Criterio de F1. Medimos 10 partidos (60 puntos).
    puntos = []
    for s in range(10):
        evs = partido.jugar_partido(RivalProgramado(100 + s), RivalProgramado(200 + s), semilla=s)
        puntos += puntos_de(evs)
    golpes_por_punto = sum(p["golpes_validos"] for p in puntos) / len(puntos)
    anulados = sum(p["motivo"] == eventos.ANULADO for p in puntos) / len(puntos)
    ganados = [sum(p["ganador"] == lado for p in puntos) for lado in (0, 1)]
    assert golpes_por_punto >= 2.0     # en promedio, más de dos golpes válidos por punto
    assert anulados <= 0.2             # casi todos los puntos terminan con un ganador
    assert min(ganados) >= 0.3 * sum(ganados)   # ningún lado tiene ventaja grande (simetría)


def test_el_punto_trae_la_distancia_minima_a_la_pelota():
    evs = partido.jugar_partido(RivalProgramado(1), ControladorQuieto(), semilla=5, puntos=2)
    for p in puntos_de(evs):
        assert len(p["distancia_minima"]) == 2
        assert all(d >= 0 for d in p["distancia_minima"])


def test_grabacion_tiene_cuadros_y_los_mismos_eventos(tmp_path):
    g = grabar.nueva_grabacion(["rival", "quieto"])
    evs = partido.jugar_partido(RivalProgramado(1), ControladorQuieto(), semilla=5, puntos=2,
                                grabacion=g)
    assert g["eventos"] == evs
    duracion = evs[-1]["t"]
    assert len(g["cuadros"]) == pytest.approx(duracion / config.DT, abs=2)
    ruta = tmp_path / "partido.json"
    grabar.guardar_grabacion(g, str(ruta))
    assert grabar.cargar_grabacion(str(ruta))["eventos"] == g["eventos"]


def test_percepcion_del_jugador_derecho_esta_espejada():
    mundo = Mundo()
    jugadores = (Jugador(mundo, 0, 300.0), Jugador(mundo, 1, 900.0))
    mundo.colocar_pelota(700.0, 100.0, 50.0, 10.0)
    izq = partido.percibir(mundo, jugadores, 0)
    der = partido.percibir(mundo, jugadores, 1)
    # Cada uno se ve a 300 de su fondo y ve al rival a 900.
    assert izq.propio_x == pytest.approx(300.0) and der.propio_x == pytest.approx(300.0)
    assert izq.rival_x == pytest.approx(900.0) and der.rival_x == pytest.approx(900.0)
    # La pelota está en x = 700 y se aleja del derecho... que la ve en 500, viniendo hacia él.
    assert der.pelota_x == pytest.approx(500.0) and der.pelota_vx == pytest.approx(-50.0)
    # Las dos raquetas empiezan igual en su marco propio.
    assert izq.raqueta_angulo == pytest.approx(der.raqueta_angulo)
    assert espejar_percepcion(der).pelota_x == pytest.approx(700.0)


# --- Las fórmulas del rival programado ---

def test_tiempo_hasta_altura_tiro_vertical():
    # Lanzada hacia arriba a 300 desde y = 0 con g = -900: vuelve a y = 0 en 2·300/900 s.
    assert tiempo_hasta_altura(0.0, 300.0, 0.0, -900.0) == pytest.approx(2 / 3)
    assert tiempo_hasta_altura(0.0, 100.0, 1000.0, -900.0) is None   # no llega tan alto


def test_rapidez_para_llegar_cumple_el_tiro_parabolico():
    angulo, distancia, altura = math.radians(40), 700.0, 40.0
    v = rapidez_para_llegar(distancia, altura, angulo)
    t = distancia / (v * math.cos(angulo))
    y = altura + v * math.sin(angulo) * t + 0.5 * config.GRAVEDAD * t * t
    assert y == pytest.approx(config.RADIO_PELOTA, abs=1e-6)


def test_prediccion_none_si_la_pelota_no_bota_en_mi_campo():
    p = Percepcion(pelota_x=550.0, pelota_y=300.0, pelota_vx=800.0, pelota_vy=0.0,
                   propio_x=300.0, propio_y=20.0, propio_vy=0.0, en_suelo=True,
                   raqueta_angulo=0.0, recarga=0.0, rival_x=900.0, rival_y=20.0)
    assert prediccion_golpe(p, ya_boto=False) is None
