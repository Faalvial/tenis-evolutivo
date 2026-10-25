"""Pruebas de la interfaz común del controlador (controlador.py)."""

import math

import pytest

import config
from controlador import (
    Accion,
    Controlador,
    ControladorQuieto,
    Percepcion,
    espejar_percepcion,
    reflejar_angulo,
)


def percepcion_ejemplo(**cambios):
    datos = dict(
        pelota_x=300.0, pelota_y=200.0, pelota_vx=150.0, pelota_vy=-50.0,
        propio_x=900.0, propio_y=20.0, propio_vy=0.0, en_suelo=True,
        raqueta_angulo=0.3, recarga=0.0, rival_x=250.0, rival_y=20.0,
    )
    datos.update(cambios)
    return Percepcion(**datos)


def test_accion_recorta_valores_fuera_de_rango():
    a = Accion(mover=3.0, saltar=1, angulo_raqueta=-7.0, golpe=-0.5)
    assert a.mover == 1.0
    assert a.saltar is True
    assert a.angulo_raqueta == -1.0
    assert a.golpe == 0.0


def test_accion_por_defecto_no_hace_nada():
    a = Accion()
    assert (a.mover, a.saltar, a.angulo_raqueta, a.golpe) == (0.0, False, 0.0, 0.0)


def test_espejar_refleja_x_y_velocidad_horizontal():
    p = percepcion_ejemplo()
    e = espejar_percepcion(p)
    assert e.pelota_x == config.ANCHO_CANCHA - p.pelota_x
    assert e.propio_x == config.ANCHO_CANCHA - p.propio_x
    assert e.rival_x == config.ANCHO_CANCHA - p.rival_x
    assert e.pelota_vx == -p.pelota_vx
    # Lo vertical no cambia al reflejar de izquierda a derecha.
    assert (e.pelota_y, e.pelota_vy, e.propio_y, e.propio_vy) == (
        p.pelota_y, p.pelota_vy, p.propio_y, p.propio_vy)


def test_espejar_dos_veces_deja_todo_igual():
    p = percepcion_ejemplo()
    doble = espejar_percepcion(espejar_percepcion(p))
    assert doble.en_suelo == p.en_suelo
    for campo in p.__dataclass_fields__:
        if campo != "en_suelo":
            assert getattr(doble, campo) == pytest.approx(getattr(p, campo))


def test_reflejar_angulo():
    # Una raqueta del jugador derecho apuntando a la red (hacia -x, ángulo π en
    # el mundo) se ve en su marco propio como 0: "horizontal hacia la red".
    assert reflejar_angulo(math.pi) == pytest.approx(0.0)
    # Apuntar hacia arriba es igual en los dos marcos.
    assert reflejar_angulo(math.pi / 2) == pytest.approx(math.pi / 2)
    # Arriba-hacia-la-red del derecho (135° en el mundo) = 45° en su marco.
    assert reflejar_angulo(3 * math.pi / 4) == pytest.approx(math.pi / 4)


def test_controlador_quieto_devuelve_accion_nula():
    c = ControladorQuieto()
    c.reiniciar()
    assert c.decidir(percepcion_ejemplo()) == Accion()


def test_controlador_base_obliga_a_implementar_decidir():
    with pytest.raises(NotImplementedError):
        Controlador().decidir(percepcion_ejemplo())
