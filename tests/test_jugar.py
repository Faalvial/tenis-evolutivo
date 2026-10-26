"""
Pruebas de jugar.py sin teclado ni ventana: una "persona" simulada aprieta
teclas y se comprueba que la partida avanza, termina y graba bien.
"""

import grabar
import jugar
from controlador import Percepcion
from rivales import RivalProgramado

P = Percepcion(300, 100, -200, 50, 300, 20, 0, True, -0.9, 0, 900, 20)


def test_teclas_a_accion():
    humano = jugar.ControladorHumano()
    humano.teclas = {"derecha", "saltar", "globo", "golpe", "fuerte"}
    a = humano.decidir(P)
    assert (a.mover, a.saltar, a.angulo_raqueta, a.golpe) == (1.0, True, 1.0, jugar.FUERZA_FUERTE)
    humano.teclas = {"izquierda", "plano", "golpe", "suave"}
    a = humano.decidir(P)
    assert (a.mover, a.angulo_raqueta, a.golpe) == (-1.0, -1.0, jugar.FUERZA_SUAVE)
    humano.teclas = set()
    assert humano.decidir(P).golpe == 0.0


def test_una_partida_completa_sin_ventana(tmp_path):
    juego = jugar.Juego(RivalProgramado(1), puntos=3, semilla=2)
    cuadros = 0
    while juego.cuadro({"derecha"} if cuadros % 120 < 60 else {"izquierda", "golpe"}):
        cuadros += 1
        assert cuadros < 60 * 200, "la partida no termina"
    puntos = [ev for ev in juego.arbitro.eventos if ev["tipo"] == "punto"]
    assert len(puntos) == 3
    ruta = tmp_path / "partida.json"
    grabar.guardar_grabacion(juego.g, str(ruta))
    assert grabar.cargar_grabacion(str(ruta))["eventos"] == juego.arbitro.eventos
