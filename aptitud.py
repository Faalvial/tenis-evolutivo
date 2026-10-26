"""
aptitud.py — Las funciones de aptitud: cuánto "vale" lo que hizo un jugador.

La aptitud es lo ÚNICO que ve el algoritmo genético: si premia algo, la
evolución lo va a buscar, y si deja un hueco, la evolución lo va a encontrar
(las "trampas" del capítulo 1). Por eso cada aptitud está escrita aquí, en un
solo lugar, y se calcula SOLO con los eventos del árbitro (eventos.py), sin
volver a simular.

Etapa 1 (lanzapelotas, sección 6 del plan), por cada pelota lanzada:
  +1 si la toca, +3 si la pasa al otro lado de la red, +5 si bota dentro del
  campo rival, y, si no la toca, un premio chico por acercarse (como máximo
  PREMIO_CERCANIA, menos que un toque: acercarse sin tocar nunca debe
  convenir más que tocar).
Etapa 2 (rival programado): puntos ganados + PESO_DEVOLUCIONES × devoluciones
  válidas, por punto jugado. El premio chico por devolver evita el problema
  del arranque: al principio nadie gana puntos, pero algunos devuelven.
Etapa 3 (IA contra IA), las tres aptitudes del experimento (sección 7 del
plan; NO se cambian sin acuerdo del equipo). Reciben una lista de partidos
[(eventos, lado), ...] porque un individuo juega varios partidos y en los dos
lados:
  A · Ganar      (ganados − perdidos) / puntos jugados.
  B · Pelotear   golpes válidos por punto (de los dos jugadores).
  C · Precisión  fracción de golpes propios válidos y profundos (último tercio
                 del campo rival) − fracción de golpes propios que terminan en error.
  Puntos anulados: no suman ni restan en A y C (A los saca del denominador).
  En B CUENTAN (un peloteo que llega al tiempo máximo es justo lo que B
  premia) y se informan aparte, para detectar la trampa de "congelar" la
  pelota (ver capítulo 6).
"""

import config
import eventos


def separar_puntos(eventos_partido):
    """Corta la lista de eventos de un partido en una lista por punto (de saque a punto)."""
    puntos, actual = [], []
    for ev in eventos_partido:
        actual.append(ev)
        if ev["tipo"] == eventos.PUNTO:
            puntos.append(actual)
            actual = []
    return puntos


def resultado_lanzamiento(evs, lado):
    """
    Qué logró el jugador `lado` con una pelota: un diccionario con
    toco, cruzo, dentro (booleanos) y la distancia mínima a la pelota.
    """
    golpes = [ev for ev in evs if ev["tipo"] == eventos.GOLPE and ev["jugador"] == lado]
    punto = evs[-1]
    toco = bool(golpes)
    # "Válida" = el árbitro contó un golpe válido suyo (botó en el campo rival,
    # o el rival la tocó en el aire de su lado).
    dentro = toco and punto["golpes_validos"] > 0
    cruzo = dentro or (toco and _cruzo_la_red(evs, lado))
    return {"toco": toco, "cruzo": cruzo, "dentro": dentro,
            "distancia": punto["distancia_minima"][lado]}


def _cruzo_la_red(evs, lado):
    """¿Después de su último golpe, la pelota botó del otro lado (aunque fuera fuera)?"""
    ultimo = max(i for i, ev in enumerate(evs) if ev["tipo"] == eventos.GOLPE and ev["jugador"] == lado)
    for ev in evs[ultimo + 1:]:
        if ev["tipo"] == eventos.BOTE:
            return ev["x"] > config.X_RED if lado == 0 else ev["x"] < config.X_RED
    return False


def puntaje_lanzamiento(r):
    """Los premios de la etapa 1 para una pelota."""
    if not r["toco"]:
        cercania = max(0.0, 1.0 - r["distancia"] / config.DISTANCIA_CERCANIA)
        return config.PREMIO_CERCANIA * cercania
    return (config.PREMIO_TOQUE
            + (config.PREMIO_CRUZA if r["cruzo"] else 0.0)
            + (config.PREMIO_DENTRO if r["dentro"] else 0.0))


def aptitud_etapa1(eventos_partido, lado=0):
    """
    Promedio de los premios por pelota, y la fracción de pelotas devueltas
    bien (la que mide el criterio de aceptación de F2b).
    Devuelve (aptitud, fraccion_devueltas).
    """
    resultados = [resultado_lanzamiento(evs, lado) for evs in separar_puntos(eventos_partido)]
    aptitud = sum(puntaje_lanzamiento(r) for r in resultados) / len(resultados)
    devueltas = sum(r["dentro"] for r in resultados) / len(resultados)
    return aptitud, devueltas


def devoluciones_validas(evs, lado):
    """Golpes del jugador `lado` que botaron bien en el campo rival."""
    return sum(1 for ev in evs
               if ev["tipo"] == eventos.BOTE and ev["valido"] and ev["golpeador"] == lado)


def aptitud_etapa2(eventos_partido, lado=0):
    """
    (puntos ganados + PESO_DEVOLUCIONES × devoluciones válidas) / puntos jugados,
    y la fracción de puntos ganados (la que mide el criterio de F3).
    Devuelve (aptitud, fraccion_ganados).
    """
    puntos = separar_puntos(eventos_partido)
    ganados = sum(1 for evs in puntos if evs[-1]["ganador"] == lado)
    validas = sum(devoluciones_validas(evs, lado) for evs in puntos)
    aptitud = (ganados + config.PESO_DEVOLUCIONES * validas) / len(puntos)
    return aptitud, ganados / len(puntos)


# --- Etapa 3: las aptitudes del experimento ---

ERRORES = (eventos.BOTE_PROPIO, eventos.FUERA, eventos.SOBRE_TECHO)
# El "tercio profundo" del campo rival: a más de 2/3 de su largo, medido desde la red.
PROFUNDIDAD_MINIMA = (config.ANCHO_CANCHA - config.X_RED) * 2 / 3


def _puntos_con_lado(partidos):
    """[(eventos de un punto, lado del jugador), ...] de todos sus partidos."""
    return [(evs, lado) for eventos_partido, lado in partidos for evs in separar_puntos(eventos_partido)]


def aptitud_A(partidos):
    """A · Ganar: (puntos ganados − puntos perdidos) / puntos jugados (sin los anulados)."""
    jugados = [(evs[-1], lado) for evs, lado in _puntos_con_lado(partidos)
               if evs[-1]["motivo"] != eventos.ANULADO]
    if not jugados:
        return 0.0
    ganados = sum(p["ganador"] == lado for p, lado in jugados)
    return (ganados - (len(jugados) - ganados)) / len(jugados)


def aptitud_B(partidos):
    """B · Pelotear: golpes válidos por punto. No distingue quién golpeó (aptitud compartida)."""
    puntos = _puntos_con_lado(partidos)
    return sum(evs[-1]["golpes_validos"] for evs, _ in puntos) / len(puntos)


def golpes_propios(evs, lado):
    """Clasifica los golpes del jugador en un punto: (total, válidos y profundos, terminaron en error)."""
    golpes = [ev for ev in evs if ev["tipo"] == eventos.GOLPE and ev["jugador"] == lado]
    profundos = sum(1 for ev in evs if ev["tipo"] == eventos.BOTE and ev["valido"]
                    and ev["golpeador"] == lado and abs(ev["x"] - config.X_RED) >= PROFUNDIDAD_MINIMA)
    # Un golpe "termina en error" si es el último del punto y el punto lo
    # pierde él por red, fuera o techo.
    final = evs[-1]
    error = int(bool(golpes) and final["ganador"] == 1 - lado and final["motivo"] in ERRORES)
    return len(golpes), profundos, error


def aptitud_C(partidos):
    """C · Precisión: fracción de golpes válidos profundos − fracción de golpes que terminan en error."""
    total = profundos = errores = 0
    for evs, lado in _puntos_con_lado(partidos):
        g, p, e = golpes_propios(evs, lado)
        total, profundos, errores = total + g, profundos + p, errores + e
    if total == 0:
        return 0.0
    return (profundos - errores) / total


APTITUDES = {"A": aptitud_A, "B": aptitud_B, "C": aptitud_C}


def anulados(partidos):
    """Fracción de puntos anulados (se informa aparte, sobre todo para B)."""
    puntos = _puntos_con_lado(partidos)
    return sum(evs[-1]["motivo"] == eventos.ANULADO for evs, _ in puntos) / len(puntos)
