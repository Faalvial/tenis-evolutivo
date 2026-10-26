"""
percepcion.py — Convierte una Percepcion (unidades físicas) en las entradas de la red.

La red trabaja mejor si todas sus entradas son números de tamaño parecido,
entre -1 y 1 (capítulo 3, "normalizar las entradas"): si una entrada valiera
900 y otra 0,3, los pesos tendrían que compensar esa diferencia.

La Percepcion ya llega en el MARCO PROPIO (partido.py la espeja para el
jugador derecho), así que una misma red sirve en los dos lados.

Entradas (14):
  0-3   pelota: x, y, vx, vy
  4-7   propio: x, altura, vy, en_suelo (+1 / -1)
  8-9   raqueta: ángulo, recarga
  10-11 rival: x, altura
  12-13 DERIVADAS: dónde está la pelota respecto de la raqueta (dx, dy)
Las 12 primeras son las de la Percepcion; las 2 últimas se calculan con
ellas. No agregan información nueva, pero le ahorran a la red una resta que
con pesos al azar tardaría mucho en "descubrir": "¿está la pelota delante de
mí y a qué altura?" es lo primero que necesita saber para golpear.
"""

import config
from jugador import valor_para_angulo

N_ENTRADAS = 14

# Escalas: el valor físico que se convierte en 1.
ANCHO_VISIBLE = config.X_RED + config.ESPACIO_DETRAS_FONDO   # x de -400 a 1600 -> de -1 a 1
ALTURA_SALTO = config.VEL_SALTO ** 2 / (2 * -config.GRAVEDAD)  # cuánto sube un salto (~112)
ALCANCE_RAQUETA = config.LARGO_RAQUETA + config.TAMANO_JUGADOR  # "cerca" = dentro de esto


def normalizar(p):
    """Percepcion -> lista de N_ENTRADAS números entre -1 y 1."""
    pivote_x = p.propio_x + config.TAMANO_JUGADOR / 2           # en el marco propio, la red está en +x
    pivote_y = p.propio_y + config.ALTURA_PIVOTE
    valores = [
        _x(p.pelota_x),
        2 * p.pelota_y / config.LIMITE_ALTURA_PERCEPCION - 1,
        p.pelota_vx / config.VEL_MAX_PELOTA,
        p.pelota_vy / config.VEL_MAX_PELOTA,
        _x(p.propio_x),
        2 * (p.propio_y - config.TAMANO_JUGADOR / 2) / ALTURA_SALTO - 1,
        p.propio_vy / config.VEL_SALTO,
        1.0 if p.en_suelo else -1.0,
        valor_para_angulo(p.raqueta_angulo),
        2 * p.recarga / config.RECARGA_GOLPE - 1,
        _x(p.rival_x),
        2 * (p.rival_y - config.TAMANO_JUGADOR / 2) / ALTURA_SALTO - 1,
        (p.pelota_x - pivote_x) / ALCANCE_RAQUETA,
        (p.pelota_y - pivote_y) / ALCANCE_RAQUETA,
    ]
    return [max(-1.0, min(1.0, v)) for v in valores]


def _x(x):
    """Posición horizontal: el fondo propio con su espacio detrás (-400) = -1, la red = 0."""
    return (x - config.X_RED) / ANCHO_VISIBLE
