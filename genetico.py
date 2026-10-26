"""
genetico.py — El algoritmo genético: selección, cruce, mutación y elitismo.

Es el del ejercicio del capítulo 3, con dos cosas nuevas (capítulo 4):

1. CRUCE: un hijo puede tener dos padres. Con el cruce POR NEURONA, el hijo
   hereda cada neurona COMPLETA (todos sus pesos de entrada y su sesgo) de uno
   de los dos padres. ¿Por qué completa? Porque los pesos de una neurona
   trabajan juntos: si la neurona 3 del padre A aprendió "¿está la pelota
   delante de mí?", mezclar la mitad de sus pesos con los de otra neurona
   que aprendió otra cosa suele dar una neurona que no sirve para nada.
   El cruce UNIFORME (cada peso de un padre al azar) se deja para comparar.

2. RECORTE SUAVE: los pesos se mantienen entre ±LIMITE_PESO con
   LIMITE · tanh(w / LIMITE), que casi no cambia los pesos chicos y frena
   suavemente a los grandes (en lugar de cortarlos en seco).

Toda la aleatoriedad usa el random.Random que se le pasa (reproducibilidad).
"""

import math

import config
import red


def poblacion_inicial(azar, tamano=None):
    tamano = config.POBLACION if tamano is None else tamano
    n = red.tamano_genoma()
    return [[azar.gauss(0.0, config.DESVIACION_INICIAL) for _ in range(n)] for _ in range(tamano)]


def recorte_suave(w):
    return config.LIMITE_PESO * math.tanh(w / config.LIMITE_PESO)


def mutar(genoma, azar):
    """A cada peso (con probabilidad PROB_MUTACION) se le suma un número gaussiano."""
    hijo = []
    for w in genoma:
        if azar.random() < config.PROB_MUTACION:
            w = recorte_suave(w + azar.gauss(0.0, config.SIGMA_MUTACION))
        hijo.append(w)
    return hijo


def cruce_por_neurona(padre_a, padre_b, azar):
    """Cada neurona completa (pesos + sesgo) viene de uno de los dos padres, al azar."""
    hijo = []
    for inicio, fin in red.bloques_neuronas():
        padre = padre_a if azar.random() < 0.5 else padre_b
        hijo.extend(padre[inicio:fin])
    return hijo


def cruce_uniforme(padre_a, padre_b, azar):
    """Cada peso por separado viene de uno de los dos padres, al azar."""
    return [a if azar.random() < 0.5 else b for a, b in zip(padre_a, padre_b)]


CRUCES = {"neurona": cruce_por_neurona, "uniforme": cruce_uniforme}


def torneo(poblacion, aptitudes, azar):
    """Se eligen TORNEO individuos al azar y gana el de mejor aptitud."""
    elegidos = azar.sample(range(len(poblacion)), config.TORNEO)
    return poblacion[max(elegidos, key=lambda i: aptitudes[i])]


def hacer_hijo(poblacion, aptitudes, azar):
    padre = torneo(poblacion, aptitudes, azar)
    if config.TIPO_CRUCE != "ninguno" and azar.random() < config.PROB_CRUCE:
        otro = torneo(poblacion, aptitudes, azar)
        padre = CRUCES[config.TIPO_CRUCE](padre, otro, azar)
    return mutar(padre, azar)


def siguiente_generacion(poblacion, aptitudes, azar):
    """Elitismo (los ELITE mejores pasan tal cual) + hijos de torneo con cruce y mutación."""
    orden = sorted(range(len(poblacion)), key=lambda i: aptitudes[i], reverse=True)
    nueva = [list(poblacion[i]) for i in orden[:config.ELITE]]
    while len(nueva) < len(poblacion):
        nueva.append(hacer_hijo(poblacion, aptitudes, azar))
    return nueva
