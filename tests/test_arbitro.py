"""
Pruebas de las reglas (arbitro.py), SIN física.

Cada prueba le "cuenta" al árbitro una jugada inventada y revisa a quién le
da el punto. Así se prueban las reglas una por una, sin depender de que la
física produzca justo esa jugada.

Recordatorio: lado 0 = izquierda (x < 600), lado 1 = derecha (x > 600).
"""

import config
import eventos
from arbitro import Arbitro, campo_de

X_IZQ = 300.0                       # un punto en el campo izquierdo
X_DER = 900.0                       # un punto en el campo derecho
X_FUERA_DER = config.ANCHO_CANCHA + 50.0


def punto_final(arb):
    """El último evento PUNTO del árbitro."""
    puntos = [ev for ev in arb.eventos if ev["tipo"] == eventos.PUNTO]
    assert puntos, "el punto todavía no terminó"
    return puntos[-1]


def nuevo(receptor=0):
    arb = Arbitro()
    arb.nuevo_punto(0.0, receptor)
    return arb


def test_campo_de():
    assert campo_de(100.0) == 0
    assert campo_de(1000.0) == 1
    assert campo_de(-1.0) is None
    assert campo_de(config.ANCHO_CANCHA + 1.0) is None


def test_saque_registra_evento():
    arb = nuevo(receptor=1)
    assert arb.eventos[0] == {"tipo": "saque", "t": 0.0, "hacia": 1}


def test_receptor_que_deja_botar_dos_veces_el_saque_pierde():
    arb = nuevo(receptor=0)
    arb.bote(0.5, X_IZQ)
    assert not arb.punto_terminado      # un bote del saque está bien
    arb.bote(1.0, X_IZQ - 50)
    p = punto_final(arb)
    assert (p["ganador"], p["motivo"], p["golpes_validos"]) == (1, eventos.DOBLE_BOTE, 0)


def test_golpe_valido_y_doble_bote_del_rival():
    arb = nuevo(receptor=0)
    arb.bote(0.5, X_IZQ)
    arb.golpe(0.8, 0, X_IZQ, 40.0, 0.5)
    arb.bote(1.5, X_DER)                # cruza y bota en el campo rival: válido
    bote = arb.eventos[-1]
    assert bote["valido"] is True and bote["golpeador"] == 0
    assert not arb.punto_terminado
    arb.bote(2.0, X_DER + 100)          # el rival no la devolvió
    p = punto_final(arb)
    assert (p["ganador"], p["motivo"], p["golpes_validos"]) == (0, eventos.DOBLE_BOTE, 1)


def test_segundo_bote_fuera_tras_un_bote_valido_sigue_siendo_doble_bote():
    # Si ya botó bien, que el segundo bote caiga fuera es culpa de quien no
    # la devolvió, no de quien la golpeó.
    arb = nuevo(receptor=0)
    arb.golpe(0.8, 0, X_IZQ, 40.0, 0.5)
    arb.bote(1.5, X_DER)
    arb.bote(2.0, X_FUERA_DER)
    p = punto_final(arb)
    assert (p["ganador"], p["motivo"]) == (0, eventos.DOBLE_BOTE)


def test_red_tras_golpe_pierde_quien_golpeo():
    arb = nuevo(receptor=1)
    arb.golpe(0.8, 1, X_DER, 40.0, 0.5)
    arb.red(1.0)
    p = punto_final(arb)
    assert (p["ganador"], p["motivo"]) == (0, eventos.BOTE_PROPIO)
    assert any(ev["tipo"] == eventos.RED and ev["golpeador"] == 1 for ev in arb.eventos)


def test_red_despues_de_un_bote_valido_no_termina_el_punto():
    arb = nuevo(receptor=0)
    arb.golpe(0.8, 0, X_IZQ, 40.0, 0.5)
    arb.bote(1.5, X_DER)
    arb.red(1.8)                        # la pelota volvió rodando hacia la red
    assert not arb.punto_terminado


def test_bote_en_el_propio_campo_tras_golpear():
    arb = nuevo(receptor=0)
    arb.golpe(0.8, 0, X_IZQ, 40.0, 0.2)
    arb.bote(1.2, X_IZQ + 100)
    p = punto_final(arb)
    assert (p["ganador"], p["motivo"]) == (1, eventos.BOTE_PROPIO)


def test_golpe_que_cae_fuera():
    arb = nuevo(receptor=0)
    arb.golpe(0.8, 0, X_IZQ, 40.0, 1.0)
    arb.bote(2.0, X_FUERA_DER)
    p = punto_final(arb)
    assert (p["ganador"], p["motivo"]) == (1, eventos.FUERA)


def test_golpe_que_supera_el_techo():
    arb = nuevo(receptor=1)
    arb.golpe(0.8, 1, X_DER, 40.0, 1.0)
    arb.revisar(1.0, config.TECHO - 1)
    assert not arb.punto_terminado
    arb.revisar(1.2, config.TECHO + 1)
    p = punto_final(arb)
    assert (p["ganador"], p["motivo"]) == (0, eventos.SOBRE_TECHO)


def test_volea_cuenta_como_golpe_valido_de_quien_la_mando():
    arb = nuevo(receptor=0)
    arb.golpe(0.8, 0, X_IZQ, 40.0, 0.5)
    arb.golpe(1.4, 1, X_DER, 80.0, 0.5)     # el rival la golpea en el aire
    arb.bote(2.2, X_IZQ)                    # y su golpe bota bien
    arb.bote(2.6, X_IZQ)
    p = punto_final(arb)
    assert (p["ganador"], p["golpes_validos"]) == (1, 2)


def test_varios_contactos_seguidos_son_un_solo_golpe():
    arb = nuevo(receptor=0)
    for i in range(4):   # cuatro subpasos tocando la raqueta
        arb.golpe(0.8 + i * config.DT, 0, X_IZQ, 40.0, 0.5)
    golpes = [ev for ev in arb.eventos if ev["tipo"] == eventos.GOLPE]
    assert len(golpes) == 1


def test_punto_anulado_por_tiempo():
    arb = nuevo(receptor=0)
    arb.revisar(config.TIEMPO_MAX_PUNTO - 0.1, 100.0)
    assert not arb.punto_terminado
    arb.revisar(config.TIEMPO_MAX_PUNTO, 100.0)
    p = punto_final(arb)
    assert (p["ganador"], p["motivo"]) == (None, eventos.ANULADO)


def test_despues_del_punto_se_ignoran_los_avisos():
    arb = nuevo(receptor=0)
    arb.golpe(0.8, 0, X_IZQ, 40.0, 1.0)
    arb.bote(2.0, X_FUERA_DER)
    n = len(arb.eventos)
    arb.bote(2.5, X_IZQ)
    arb.red(2.6)
    arb.golpe(2.7, 1, X_DER, 40.0, 0.5)
    assert len(arb.eventos) == n


def test_eventos_del_partido_se_acumulan_entre_puntos():
    arb = nuevo(receptor=0)
    arb.bote(0.5, X_IZQ)
    arb.bote(1.0, X_IZQ)
    arb.nuevo_punto(1.0, 1)
    arb.bote(1.5, X_DER)
    arb.bote(2.0, X_DER)
    puntos = [ev for ev in arb.eventos if ev["tipo"] == eventos.PUNTO]
    assert [p["ganador"] for p in puntos] == [1, 0]
