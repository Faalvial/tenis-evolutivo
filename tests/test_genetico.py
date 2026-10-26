"""Pruebas del algoritmo genético (genetico.py)."""

import random

import pytest

import config
import genetico
import red


def dos_padres():
    n = red.tamano_genoma()
    return [1.0] * n, [2.0] * n


def test_cruce_por_neurona_hereda_neuronas_completas():
    a, b = dos_padres()
    hijo = genetico.cruce_por_neurona(a, b, random.Random(3))
    usados = set()
    for inicio, fin in red.bloques_neuronas():
        bloque = hijo[inicio:fin]
        assert bloque == a[inicio:fin] or bloque == b[inicio:fin]   # nunca mezclado
        usados.add(bloque[0])
    assert usados == {1.0, 2.0}                                     # hay de los dos padres


def test_cruce_uniforme_mezcla_pesos_sueltos():
    a, b = dos_padres()
    hijo = genetico.cruce_uniforme(a, b, random.Random(3))
    assert set(hijo) == {1.0, 2.0} and len(hijo) == len(a)


def test_mutar_cambia_poco_y_respeta_el_limite():
    azar = random.Random(0)
    genoma = [0.0] * red.tamano_genoma()
    hijo = genetico.mutar(genoma, azar)
    diferencias = [abs(h - g) for h, g in zip(hijo, genoma)]
    assert 0.05 < sum(diferencias) / len(diferencias) < 0.3          # del orden de SIGMA
    grande = genetico.mutar([100.0] * red.tamano_genoma(), azar)
    assert all(abs(w) <= config.LIMITE_PESO for w in grande)


def test_recorte_suave():
    assert genetico.recorte_suave(0.1) == pytest.approx(0.1, abs=1e-3)   # casi no toca los chicos
    assert genetico.recorte_suave(50.0) < config.LIMITE_PESO


def test_elitismo_y_tamano_de_la_poblacion():
    azar = random.Random(1)
    poblacion = genetico.poblacion_inicial(azar, tamano=10)
    aptitudes = [float(i) for i in range(10)]
    nueva = genetico.siguiente_generacion(poblacion, aptitudes, azar)
    assert len(nueva) == 10
    assert nueva[0] == poblacion[9] and nueva[1] == poblacion[8]


def test_misma_semilla_misma_generacion():
    def una(semilla):
        azar = random.Random(semilla)
        poblacion = genetico.poblacion_inicial(azar, tamano=8)
        return genetico.siguiente_generacion(poblacion, list(range(8)), azar)
    assert una(5) == una(5)
