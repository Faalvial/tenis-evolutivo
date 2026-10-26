"""Pruebas de graficos.py con un resumen inventado (no hace falta correr el experimento)."""

import os
import random

import pytest

import graficos
from guardado import cargar_json, guardar_json


def metricas_falsas(gen, nivel, azar):
    return {"generacion": gen, "ganados": nivel, "peloteo": 2 + nivel, "golpes_validos": 0.5,
            "profundidad": 300 + 100 * nivel, "ganadores": 0.1, "errores": 0.2, "anulados": 0.0,
            "botes": [600 + azar.uniform(50, 600) for _ in range(20)]}


@pytest.fixture
def experimento_falso(tmp_path):
    azar = random.Random(0)
    resumen = []
    for t, nivel in (("A", 0.6), ("B", 0.3), ("C", 0.45)):
        for semilla in range(5):
            ruido = azar.uniform(-0.03, 0.03)
            resumen.append({"semilla": semilla, "tratamiento": t, "generaciones": 20, "historial": [],
                            "metricas": [metricas_falsas(g, nivel * g / 19 + ruido, azar) for g in (0, 10, 19)]})
    guardar_json(os.path.join(tmp_path, "resumen.json"), resumen)
    return str(tmp_path)


def test_genera_graficos_y_tabla(experimento_falso):
    salida, texto = graficos.generar(experimento_falso)
    for nombre in ("curvas.png", "cajas.png", "mapa_botes.png", "tabla.md", "tabla.csv"):
        assert os.path.getsize(os.path.join(salida, nombre)) > 0
    assert "A · ganar" in texto and "p A–B" in texto


def test_mann_whitney_detecta_una_diferencia_clara(experimento_falso):
    grupos = graficos.por_tratamiento(cargar_json(os.path.join(experimento_falso, "resumen.json")))
    p = graficos.comparar(grupos, "ganados")
    assert p[("A", "B")] < 0.05          # 0,6 contra 0,3: diferencia clara con 5 semillas
