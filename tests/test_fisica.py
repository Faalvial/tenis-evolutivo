"""
Pruebas de la física (mundo.py y jugador.py).

La más importante es la de "anti-atravesamiento" (criterio de F1): en un
motor de física por pasos, un objeto rápido puede estar a un lado de la
raqueta en un paso y al otro lado en el siguiente, sin que el motor note el
choque. Lanzamos 1000 pelotas contra una raqueta quieta y 1000 contra una que
está golpeando, y exigimos que TODAS se registren como contacto.
"""

import math
import random

import pytest

import config
from controlador import Accion
from jugador import Jugador, traducir_angulo, valor_para_angulo
from mundo import Mundo

LANZAMIENTOS = 1000


# --- Ayudantes ---

def jugador_en_el_aire(azar):
    """Un jugador flotando (sin gravedad), con la raqueta quieta en un ángulo al azar."""
    mundo = Mundo()
    mundo.espacio.gravity = (0.0, 0.0)
    lado = azar.choice((0, 1))
    jugador = Jugador(mundo, lado, 300.0 if lado == 0 else 900.0)
    jugador.cuerpo.position = (jugador.cuerpo.position.x, 300.0)   # lejos del suelo
    valor = azar.uniform(-1.0, 1.0)
    for _ in range(30):   # dejar que el motor lleve la raqueta al ángulo pedido
        jugador.aplicar(Accion(angulo_raqueta=valor), config.DT)
        mundo.avanzar()
    return mundo, jugador, valor


def punto_de_la_raqueta(jugador, distancia, giro_extra=0.0):
    """Punto a `distancia` del pivote, a lo largo de la raqueta (marco propio + giro)."""
    angulo = jugador.angulo_propio() + giro_extra
    pivote = jugador.pivote_mundo()
    return (pivote.x + jugador.signo * distancia * math.cos(angulo),
            pivote.y + distancia * math.sin(angulo)), angulo


def hubo_toque(mundo, jugador, accion, pasos=15):
    for _ in range(pasos):
        jugador.aplicar(accion, config.DT)
        mundo.avanzar()
        if any(c[0] == "toque" for c in mundo.contactos):
            return True
    return False


def lanzar_contra_raqueta_quieta(semilla):
    azar = random.Random(semilla)
    mundo, jugador, valor = jugador_en_el_aire(azar)
    (px, py), angulo = punto_de_la_raqueta(jugador, azar.uniform(5, config.LARGO_RAQUETA - 5))
    # Llega desde arriba de la raqueta, con hasta ±57° de inclinación y
    # entre la mitad y el total de la rapidez máxima.
    direccion = angulo + math.pi / 2 + azar.uniform(-1.0, 1.0)
    dx, dy = jugador.signo * math.cos(direccion), math.sin(direccion)
    rapidez = azar.uniform(0.5, 1.0) * config.VEL_MAX_PELOTA
    mundo.colocar_pelota(px + 60 * dx, py + 60 * dy, -rapidez * dx, -rapidez * dy)
    mundo.contactos.clear()
    return hubo_toque(mundo, jugador, Accion(angulo_raqueta=valor))


def lanzar_contra_raqueta_golpeando(semilla):
    azar = random.Random(semilla)
    mundo, jugador, valor = jugador_en_el_aire(azar)
    # La pelota baja hacia un punto que la raqueta va a barrer a mitad del golpe.
    (px, py), angulo = punto_de_la_raqueta(jugador, azar.uniform(10, config.LARGO_RAQUETA - 5),
                                           azar.uniform(0.3, 0.8))
    direccion = angulo + math.pi / 2
    dx, dy = jugador.signo * math.cos(direccion), math.sin(direccion)
    rapidez = azar.uniform(0.0, 1.0) * config.VEL_MAX_PELOTA
    t_llegada = 0.04
    mundo.colocar_pelota(px + rapidez * dx * t_llegada, py + rapidez * dy * t_llegada,
                         -rapidez * dx, -rapidez * dy)
    mundo.contactos.clear()
    return hubo_toque(mundo, jugador, Accion(angulo_raqueta=valor, golpe=1.0))


# --- Pruebas ---

def test_pelota_no_atraviesa_raqueta_quieta():
    fallos = [s for s in range(LANZAMIENTOS) if not lanzar_contra_raqueta_quieta(s)]
    assert fallos == []


def test_pelota_no_atraviesa_raqueta_que_golpea():
    fallos = [s for s in range(LANZAMIENTOS) if not lanzar_contra_raqueta_golpeando(s)]
    assert fallos == []


@pytest.mark.parametrize("lado, x", [(0, 300.0), (1, 900.0)])
@pytest.mark.parametrize("mover", [-1.0, 1.0])
def test_jugador_no_sale_de_su_mitad(lado, x, mover):
    mundo = Mundo()
    jugador = Jugador(mundo, lado, x)
    x_min, x_max = jugador.limites_x()
    for paso in range(400):
        jugador.aplicar(Accion(mover=mover, saltar=paso % 30 == 0), config.DT)
        mundo.avanzar()
        assert x_min - 1e-6 <= jugador.cuerpo.position.x <= x_max + 1e-6
    # Y la raqueta nunca cruza la red (gracias a MARGEN_RED_JUGADOR).
    punta_x = jugador.pivote_mundo().x + jugador.signo * config.LARGO_RAQUETA
    assert (punta_x < config.X_RED) if lado == 0 else (punta_x > config.X_RED)


def test_solo_salta_desde_el_suelo():
    mundo = Mundo()
    jugador = Jugador(mundo, 0, 300.0)
    jugador.aplicar(Accion(saltar=True), config.DT)
    mundo.avanzar()
    assert jugador.cuerpo.velocity.y > 0
    for _ in range(5):
        mundo.avanzar()
    vy_en_el_aire = jugador.cuerpo.velocity.y
    jugador.aplicar(Accion(saltar=True), config.DT)   # en el aire: se ignora
    assert jugador.cuerpo.velocity.y == vy_en_el_aire


def test_rebote_pierde_energia_segun_la_elasticidad():
    # Soltada desde h, la pelota sube después del bote hasta ~ e² · h
    # (la rapidez se multiplica por e, y la altura va con la rapidez al cuadrado).
    mundo = Mundo()
    h = 300.0
    mundo.colocar_pelota(100.0, h + config.RADIO_PELOTA, 0.0, 0.0)
    boto = False
    altura_max = 0.0
    for _ in range(300):
        mundo.avanzar()
        boto = boto or any(c[0] == "bote" for c in mundo.contactos)
        mundo.contactos.clear()
        if boto:
            altura_max = max(altura_max, mundo.pelota.position.y - config.RADIO_PELOTA)
    assert altura_max == pytest.approx(config.ELASTICIDAD_PELOTA ** 2 * h, rel=0.05)


def jugador_listo_para_golpear(lado, fuerza=1.0, angulo_preparacion=-math.pi / 4):
    """Un jugador en medio de un golpe, con la preparación y la fuerza dadas."""
    mundo = Mundo()
    jugador = Jugador(mundo, lado, 300.0 if lado == 0 else 900.0)
    jugador.angulo_inicio_golpe = angulo_preparacion
    jugador.fuerza_golpe = fuerza
    return jugador


def punto_dulce(jugador):
    """Un punto sobre la raqueta, justo en el punto dulce."""
    (x, y), _ = punto_de_la_raqueta(jugador, config.POSICION_PUNTO_DULCE * config.LARGO_RAQUETA)
    return (x, y)


@pytest.fixture
def capas_apagadas(monkeypatch):
    monkeypatch.setattr(config, "APORTE_PELOTA_ENTRANTE", 0.0)
    monkeypatch.setattr(config, "PERDIDA_FUERA_DEL_PUNTO_DULCE", 0.0)
    monkeypatch.setattr(config, "MEZCLA_ANGULO_CONTACTO", 0.0)


def test_modelo_de_golpe_direccion_y_rapidez(capas_apagadas):
    for lado in (0, 1):
        jugador = jugador_listo_para_golpear(lado)   # raqueta a -45°: el tiro sale a +45°
        vx, vy = jugador.velocidad_salida(jugador.pivote_mundo(), (0.0, 0.0))
        assert math.hypot(vx, vy) == pytest.approx(config.VEL_SALIDA_MAX)
        assert vy == pytest.approx(abs(vx))           # 45° hacia arriba
        assert (vx > 0) == (lado == 0)                # siempre hacia la red


def test_capa_1_la_pelota_que_llega_suma_rapidez(capas_apagadas, monkeypatch):
    monkeypatch.setattr(config, "APORTE_PELOTA_ENTRANTE", 0.3)
    jugador = jugador_listo_para_golpear(0, fuerza=0.0)
    vx, vy = jugador.velocidad_salida(punto_dulce(jugador), (-300.0, -400.0))   # llega a 500
    assert math.hypot(vx, vy) == pytest.approx(config.VEL_SALIDA_MIN + 0.3 * 500.0)


def test_capa_2_punto_dulce(capas_apagadas, monkeypatch):
    monkeypatch.setattr(config, "PERDIDA_FUERA_DEL_PUNTO_DULCE", 0.3)
    jugador = jugador_listo_para_golpear(1)
    assert jugador.factor_punto_dulce(punto_dulce(jugador)) == pytest.approx(1.0)
    # En el mango (y en la punta, que está igual de lejos) se pierde el 30 %.
    assert jugador.factor_punto_dulce(jugador.pivote_mundo()) == pytest.approx(0.7)
    punta, _ = punto_de_la_raqueta(jugador, config.LARGO_RAQUETA)
    assert jugador.factor_punto_dulce(punta) == pytest.approx(0.7)
    # Y es suave: un poco fuera del punto dulce pierde poco.
    cerca, _ = punto_de_la_raqueta(jugador, config.POSICION_PUNTO_DULCE * config.LARGO_RAQUETA + 5)
    assert 0.98 < jugador.factor_punto_dulce(cerca) < 1.0


def test_capa_3_mezcla_el_angulo_al_tocar(capas_apagadas, monkeypatch):
    monkeypatch.setattr(config, "MEZCLA_ANGULO_CONTACTO", 1.0)
    jugador = jugador_listo_para_golpear(0, angulo_preparacion=-1.2)
    vx, vy = jugador.velocidad_salida(punto_dulce(jugador), (0.0, 0.0))
    # Con mezcla 1, la dirección sale del ángulo ACTUAL de la raqueta, no del de preparación.
    assert math.atan2(vy, vx) == pytest.approx(jugador.angulo_propio() + math.pi / 2)


def test_traducir_angulo_ida_y_vuelta():
    assert traducir_angulo(-1.0) == pytest.approx(config.ANGULO_RAQUETA_MIN)
    assert traducir_angulo(1.0) == pytest.approx(config.ANGULO_RAQUETA_MAX)
    for valor in (-0.7, 0.0, 0.4):
        assert valor_para_angulo(traducir_angulo(valor)) == pytest.approx(valor)


def test_raqueta_llega_al_angulo_pedido_en_los_dos_lados():
    for lado in (0, 1):
        mundo = Mundo()
        jugador = Jugador(mundo, lado, 300.0 if lado == 0 else 900.0)
        for _ in range(60):
            jugador.aplicar(Accion(angulo_raqueta=0.5), config.DT)
            mundo.avanzar()
        assert jugador.angulo_propio() == pytest.approx(traducir_angulo(0.5), abs=0.05)
