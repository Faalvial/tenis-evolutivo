"""
Pruebas del entrenamiento (entrenar.py) y del lanzapelotas (rivales.py).

Se usan poblaciones y partidos chicos para que corran rápido. La prueba
clave: cortar el entrenamiento y reanudarlo da EXACTAMENTE lo mismo que no
cortarlo.
"""

import os
import random

import pytest

import config
import entrenar
import partido
from arbitro import campo_de
from guardado import cargar_json, guardar_json
from rivales import ControladorAusente, lanzapelotas


@pytest.fixture
def entrenamiento_chico(monkeypatch):
    monkeypatch.setattr(config, "POBLACION", 6)
    monkeypatch.setattr(config, "LANZAMIENTOS_POR_EVALUACION", 2)
    monkeypatch.setattr(config, "ETAPA1_LANZAMIENTOS_PRUEBA", 4)


@pytest.mark.parametrize("receptor", [0, 1])
def test_el_lanzapelotas_bota_en_el_campo_del_receptor(receptor):
    for s in range(20):
        evs = partido.jugar_partido(ControladorAusente(), ControladorAusente(), s, puntos=1,
                                    saque=lanzapelotas, receptor_fijo=receptor)
        primer_bote = next(ev for ev in evs if ev["tipo"] == "bote")
        assert campo_de(primer_bote["x"]) == receptor


def test_guarda_estado_e_historial(entrenamiento_chico, tmp_path):
    entrenar.entrenar_etapa1(str(tmp_path), semilla=1, procesos=1, generaciones=2)
    estado = cargar_json(os.path.join(tmp_path, "estado.json"))
    assert estado["generacion"] == 2 and len(estado["poblacion"]) == 6
    assert os.path.exists(os.path.join(tmp_path, "historial.csv"))
    assert estado["campeon"] is not None          # la generación 0 siempre prueba al campeón


def test_reanudar_da_lo_mismo_que_no_cortar(entrenamiento_chico, tmp_path):
    cortado, seguido = str(tmp_path / "cortado"), str(tmp_path / "seguido")
    entrenar.entrenar_etapa1(cortado, semilla=4, procesos=1, generaciones=2)
    entrenar.entrenar_etapa1(cortado, semilla=4, procesos=1, generaciones=3)   # reanuda
    entrenar.entrenar_etapa1(seguido, semilla=4, procesos=1, generaciones=3)
    a = cargar_json(os.path.join(cortado, "estado.json"))
    b = cargar_json(os.path.join(seguido, "estado.json"))
    assert a["poblacion"] == b["poblacion"]
    sin_tiempo = lambda h: [{k: v for k, v in f.items() if k != "segundos"} for f in h]
    assert sin_tiempo(a["historial"]) == sin_tiempo(b["historial"])


def test_no_mezcla_semillas(entrenamiento_chico, tmp_path):
    entrenar.entrenar_etapa1(str(tmp_path), semilla=1, procesos=1, generaciones=1)
    with pytest.raises(ValueError):
        entrenar.entrenar_etapa1(str(tmp_path), semilla=2, procesos=1, generaciones=2)


def test_grabar_al_campeon(entrenamiento_chico, tmp_path):
    entrenar.entrenar_etapa1(str(tmp_path), semilla=1, procesos=1, generaciones=1)
    ruta = entrenar.grabar_campeon(str(tmp_path), puntos=2)
    assert os.path.getsize(ruta) > 0


def test_al_terminar_la_etapa_1_sigue_con_la_2(entrenamiento_chico, monkeypatch, tmp_path):
    # Meta 0: la etapa 1 termina en la primera prueba y la población pasa a la etapa 2.
    monkeypatch.setattr(config, "ETAPA1_META_DEVUELTAS", 0.0)
    monkeypatch.setattr(config, "PUNTOS_ETAPA2", 2)
    monkeypatch.setattr(config, "ETAPA2_PUNTOS_PRUEBA", 2)
    estado = entrenar.entrenar(str(tmp_path), semilla=1, procesos=1, generaciones=2)
    assert estado["etapa"] == 2 and estado["generacion"] == 2
    assert estado["campeones"]["1"] is not None
    assert estado["resumen_etapas"]["1"]["generaciones"] == 1
    assert [h["etapa"] for h in estado["historial"]] == [1, 2, 2]


def test_al_terminar_la_etapa_2_guarda_la_poblacion_base(entrenamiento_chico, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "ETAPA1_META_DEVUELTAS", 0.0)
    monkeypatch.setattr(config, "ETAPA2_META_GANADOS", 0.0)
    monkeypatch.setattr(config, "PUNTOS_ETAPA2", 2)
    monkeypatch.setattr(config, "ETAPA2_PUNTOS_PRUEBA", 2)
    estado = entrenar.entrenar(str(tmp_path), semilla=1, procesos=1)
    assert estado["etapa"] == 3
    base = cargar_json(os.path.join(tmp_path, "poblacion_base.json"))
    assert len(base["poblacion"]) == config.POBLACION
    ruta = entrenar.grabar_campeon(str(tmp_path), puntos=2)
    assert ruta.endswith("campeon_etapa2.json")


def test_la_meta_se_confirma_con_la_validacion(entrenamiento_chico, monkeypatch, tmp_path):
    # Si la validación nunca alcanza, la etapa no termina aunque la prueba sí.
    monkeypatch.setattr(config, "ETAPA1_META_DEVUELTAS", 0.0)
    reales = entrenar.probar_campeon

    def validacion_imposible(etapa, genoma, semilla=entrenar.SEMILLA_PRUEBA):
        return -1.0 if semilla == entrenar.SEMILLA_VALIDACION else reales(etapa, genoma, semilla)

    monkeypatch.setattr(entrenar, "probar_campeon", validacion_imposible)
    estado = entrenar.entrenar_etapa1(str(tmp_path), semilla=1, procesos=1, generaciones=2)
    assert not estado["terminada"] and estado["historial"][0]["validacion"] == -1.0


# --- Etapa 3 ---

@pytest.fixture
def etapa3_chica(entrenamiento_chico, monkeypatch, tmp_path):
    import genetico
    import metricas
    monkeypatch.setattr(config, "PUNTOS_POR_PARTIDO", 2)
    monkeypatch.setattr(config, "RIVALES_POBLACION", 1)
    monkeypatch.setattr(config, "RIVALES_SALON", 1)
    monkeypatch.setattr(config, "METRICAS_CADA", 2)
    monkeypatch.setattr(metricas, "PUNTOS_BATERIA", 4)
    base = {"semilla": 1, "poblacion": genetico.poblacion_inicial(random.Random(0), tamano=6)}
    ruta = os.path.join(tmp_path, "poblacion_base.json")
    guardar_json(ruta, base)
    return ruta


@pytest.mark.parametrize("tratamiento", ["A", "B", "C"])
def test_una_rama_de_la_etapa_3(etapa3_chica, tmp_path, tratamiento):
    estado = entrenar.entrenar_etapa3(str(tmp_path / tratamiento), etapa3_chica, tratamiento,
                                      procesos=1, generaciones=3)
    assert estado["generacion"] == 3
    assert len(estado["salon"]) == 3                       # un campeón por generación
    assert [m["generacion"] for m in estado["metricas"]] == [0, 2]


def test_las_ramas_parten_de_la_misma_poblacion_base(etapa3_chica, tmp_path):
    a = entrenar.entrenar_etapa3(str(tmp_path / "A"), etapa3_chica, "A", procesos=1, generaciones=0)
    b = entrenar.entrenar_etapa3(str(tmp_path / "B"), etapa3_chica, "B", procesos=1, generaciones=0)
    assert a["poblacion"] == b["poblacion"]


def test_reanudar_una_rama_da_lo_mismo(etapa3_chica, tmp_path):
    cortada, seguida = str(tmp_path / "cortada"), str(tmp_path / "seguida")
    entrenar.entrenar_etapa3(cortada, etapa3_chica, "C", procesos=1, generaciones=1)
    entrenar.entrenar_etapa3(cortada, etapa3_chica, "C", procesos=1, generaciones=2)
    entrenar.entrenar_etapa3(seguida, etapa3_chica, "C", procesos=1, generaciones=2)
    a = cargar_json(os.path.join(cortada, "estado.json"))
    b = cargar_json(os.path.join(seguida, "estado.json"))
    assert a["poblacion"] == b["poblacion"] and a["salon"] == b["salon"]
