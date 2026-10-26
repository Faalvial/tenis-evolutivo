"""
metricas.py — La batería de referencia y las métricas del experimento (sección 8 del plan).

Las métricas se calculan IGUAL para todos los tratamientos (A, B y C) y NO
dependen de la aptitud con que se entrenó: así se pueden comparar. Siempre
contra el mismo rival (el rival programado de la etapa 2) y con los mismos
saques (SEMILLA_BATERIA fija).

Métricas de un jugador (sección 8):
  1. ganados          % de puntos ganados contra el rival de referencia
  2. peloteo          golpes válidos por punto (de los dos jugadores)
  3. golpes_validos   % de sus golpes que fueron válidos
  4. profundidad      distancia media a la red de sus botes válidos
  5. ganadores        % de puntos que ganó con un golpe que el rival no devolvió
     errores          % de puntos que perdió por error propio (red, fuera, techo)
  6. anulados         % de puntos anulados (tiempo agotado)
Además, `botes` guarda la x de cada bote válido suyo, para el mapa de calor.

Clasificación de los motivos (la confirma R4, ver docs/interfaces.md):
"ganador" = el punto lo ganó él por doble_bote del rival; "error propio" =
lo perdió por bote_propio, fuera o techo.
"""

import config
import eventos
import partido
from aptitud import ERRORES, separar_puntos
from rivales import RivalProgramado

SEMILLA_BATERIA = 8082026      # saques y rival de la batería: NO cambiar a mitad del experimento
PUNTOS_BATERIA = 100


def jugar_bateria(controlador, puntos=None, semilla=SEMILLA_BATERIA):
    """El jugador (a la izquierda) juega `puntos` puntos contra el rival de referencia."""
    puntos = PUNTOS_BATERIA if puntos is None else puntos
    return partido.jugar_partido(controlador, RivalProgramado(semilla), semilla, puntos=puntos)


def calcular(eventos_partido, lado=0):
    """Las métricas de la sección 8 a partir de los eventos (todas las fracciones de 0 a 1)."""
    puntos = separar_puntos(eventos_partido)
    finales = [evs[-1] for evs in puntos]
    golpes = [ev for ev in eventos_partido if ev["tipo"] == eventos.GOLPE and ev["jugador"] == lado]
    botes_validos = [ev for ev in eventos_partido
                     if ev["tipo"] == eventos.BOTE and ev["valido"] and ev["golpeador"] == lado]
    n = len(finales)
    return {
        "ganados": sum(p["ganador"] == lado for p in finales) / n,
        "peloteo": sum(p["golpes_validos"] for p in finales) / n,
        "golpes_validos": len(botes_validos) / len(golpes) if golpes else 0.0,
        "profundidad": (sum(abs(b["x"] - config.X_RED) for b in botes_validos) / len(botes_validos)
                        if botes_validos else 0.0),
        "ganadores": sum(p["ganador"] == lado and p["motivo"] == eventos.DOBLE_BOTE
                         for p in finales) / n,
        "errores": sum(p["ganador"] == 1 - lado and p["motivo"] in ERRORES for p in finales) / n,
        "anulados": sum(p["motivo"] == eventos.ANULADO for p in finales) / n,
        "botes": [round(b["x"], 1) for b in botes_validos],
    }


def medir(controlador, puntos=None):
    """Atajo: jugar la batería y calcular sus métricas."""
    return calcular(jugar_bateria(controlador, puntos))
