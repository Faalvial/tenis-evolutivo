"""Pruebas del formato de grabación (grabar.py) y del vocabulario de eventos."""

import json

import pytest

import config
import eventos
from grabar import (
    COLUMNAS,
    agregar_cuadro,
    agregar_evento,
    cargar_grabacion,
    cuadro_como_dict,
    guardar_grabacion,
    nueva_grabacion,
)


def grabacion_ejemplo():
    g = nueva_grabacion(["quieto", "quieto"], tratamiento="A", generacion=0)
    agregar_cuadro(g, 0.0, (600.0, 60.0),
                   (300.0, 20.0, 330.0, 25.0, 0.2),
                   (900.0, 20.0, 870.0, 25.0, 2.9))
    agregar_cuadro(g, 1 / 60, (603.12345, 58.98765),
                   (300.0, 20.0, 330.0, 25.0, 0.21234567),
                   (900.0, 20.0, 870.0, 25.0, 2.9))
    agregar_evento(g, eventos.evento(eventos.SAQUE, 0.0, hacia=0))
    return g


def test_cada_cuadro_tiene_una_columna_por_nombre():
    g = grabacion_ejemplo()
    assert all(len(c) == len(COLUMNAS) for c in g["cuadros"])


def test_cuadro_se_redondea():
    d = cuadro_como_dict(grabacion_ejemplo(), 1)
    assert d["pelota_x"] == round(603.12345, config.DECIMALES_GRABACION)
    assert d["izq_raqueta_angulo"] == round(0.21234567, config.DECIMALES_ANGULO)


def test_guardar_y_cargar_da_lo_mismo(tmp_path):
    g = grabacion_ejemplo()
    ruta = tmp_path / "sub" / "partido.json"
    guardar_grabacion(g, str(ruta))
    assert cargar_grabacion(str(ruta)) == g
    # El guardado atómico no deja el temporal tirado.
    assert not (tmp_path / "sub" / "partido.json.tmp").exists()


def test_cargar_rechaza_otra_version(tmp_path):
    g = grabacion_ejemplo()
    g["version"] = config.VERSION_GRABACION + 1
    ruta = tmp_path / "vieja.json"
    ruta.write_text(json.dumps(g), encoding="utf-8")
    with pytest.raises(ValueError, match="versión"):
        cargar_grabacion(str(ruta))


def test_cargar_rechaza_archivo_que_no_es_grabacion(tmp_path):
    ruta = tmp_path / "otro.json"
    ruta.write_text(json.dumps({"hola": 1}), encoding="utf-8")
    with pytest.raises(ValueError):
        cargar_grabacion(str(ruta))


def test_evento_rechaza_tipos_y_motivos_desconocidos():
    with pytest.raises(ValueError):
        eventos.evento("rebote", 1.0)
    with pytest.raises(ValueError):
        eventos.evento(eventos.PUNTO, 1.0, ganador=0, motivo="porque si")
    ev = eventos.evento(eventos.PUNTO, 1.0, ganador=1, motivo=eventos.FUERA, golpes_validos=3)
    assert ev == {"tipo": "punto", "t": 1.0, "ganador": 1, "motivo": "fuera", "golpes_validos": 3}
