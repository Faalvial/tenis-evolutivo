"""
Pruebas del visor 2D (ver2d.py).

El visor no cambia nada del juego, pero conviene saber que sigue abriendo las
grabaciones: si alguien cambia el formato y el visor se rompe, esta prueba
avisa antes de la feria. Corre sin ventana (SDL_VIDEODRIVER=dummy).
"""

import pytest

import eventos
import grabar
import partido
import ver2d
from controlador import ControladorQuieto
from rivales import RivalProgramado


@pytest.fixture
def grabacion_corta():
    g = grabar.nueva_grabacion(["A", "B"])
    partido.jugar_partido(RivalProgramado(1), ControladorQuieto(), semilla=2, puntos=2, grabacion=g)
    return g


def test_captura_en_varios_instantes(grabacion_corta, tmp_path, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    duracion = len(grabacion_corta["cuadros"]) * grabacion_corta["dt_cuadro"]
    for t in (0.0, duracion / 2, duracion + 5):   # inicio, medio y más allá del final
        ruta = tmp_path / f"cuadro_{t:.0f}.png"
        ver2d.guardar_captura(grabacion_corta, t, str(ruta))
        assert ruta.stat().st_size > 0


def test_gestos_salen_de_los_eventos(grabacion_corta):
    punto = next(ev for ev in grabacion_corta["eventos"] if ev["tipo"] == eventos.PUNTO)
    ganador = punto["ganador"]
    justo_despues = punto["t"] + 0.1
    assert ver2d.gesto(grabacion_corta["eventos"], justo_despues, ganador) == "feliz"
    assert ver2d.gesto(grabacion_corta["eventos"], justo_despues, 1 - ganador) == "triste"
    assert ver2d.gesto(grabacion_corta["eventos"], 0.0, ganador) == "normal"


def test_la_camara_siempre_encuadra_a_los_jugadores(grabacion_corta):
    for i, (x_min, x_max) in enumerate(ver2d.encuadres(grabacion_corta)):
        cam = ver2d.Camara(x_min, x_max)
        c = grabar.cuadro_como_dict(grabacion_corta, i)
        for x in (c["izq_x"], c["der_x"]):
            px, _ = cam.punto(x, 0)
            assert 0 <= px <= ver2d.ANCHO_VENTANA
