"""
entrenar.py — El entrenamiento por etapas (currículo, sección 6 del plan).

  Etapa 1 · lanzapelotas      aprender a devolver (capítulo 4)
  Etapa 2 · rival programado  aprender a ganar puntos (capítulo 5)
  Etapa 3 · IA contra IA      con las aptitudes A, B o C (capítulo 6): una
                              RAMA por tratamiento, desde la población base

La MISMA población pasa de una etapa a la siguiente: lo que aprendió en la
etapa 1 es el punto de partida de la 2. Al terminar la etapa 2 se guarda la
POBLACIÓN BASE (poblacion_base.json), de la que salen los tres tratamientos.

Cada generación de una etapa:
  1. se eligen las pelotas/puntos de esta generación (los MISMOS para todos:
     equidad), a partir de (semilla, etapa, generación);
  2. se evalúa a toda la población EN PARALELO (multiprocessing);
  3. cada ETAPA_PRUEBA_CADA generaciones se prueba a los mejores con una batería
     FIJA (siempre la misma, para comparar entre generaciones) y el que mejor
     la hace es el campeón; si cumple la
     meta, se lo CONFIRMA con una segunda batería independiente (validación),
     y solo entonces la etapa termina;
  4. el algoritmo genético hace la generación siguiente;
  5. se guarda el estado (guardado atómico) y el historial.

REANUDABLE: si se corta, el mismo comando sigue desde la última generación
guardada, y el resultado es idéntico al de no cortar.

Uso:
    python entrenar.py --carpeta resultados/prueba --semilla 1               (etapas 1 y 2)
    python entrenar.py --carpeta resultados/prueba --semilla 1 --hasta-etapa 1
    python entrenar.py --carpeta resultados/prueba --grabar-campeon
"""

import argparse
import os
import random
import time
from dataclasses import dataclass
from typing import Callable

import aptitud
import config
import genetico
import grabar
import metricas
import partido
from aptitud import aptitud_etapa1, aptitud_etapa2
from guardado import cargar_json, guardar_csv, guardar_json
from red import ControladorRed
from rivales import ControladorAusente, RivalProgramado, lanzapelotas

SEMILLA_PRUEBA = 20261210      # batería fija de la prueba del campeón (no cambiarla)
SEMILLA_VALIDACION = 31415926  # segunda batería, independiente, para CONFIRMAR la meta
COLUMNAS_HISTORIAL = ["etapa", "generacion", "mejor", "promedio", "logro_mejor",
                      "prueba_campeon", "validacion", "segundos"]


# --- Evaluaciones (corren en los procesos del Pool: deben ser funciones de módulo) ---

def evaluar_etapa1(argumentos):
    """N pelotas del lanzapelotas -> (aptitud, fracción devuelta bien)."""
    genoma, semilla, pelotas = argumentos
    evs = partido.jugar_partido(ControladorRed(genoma), ControladorAusente(), semilla,
                                puntos=pelotas, saque=lanzapelotas, receptor_fijo=0)
    return aptitud_etapa1(evs)


def evaluar_etapa2(argumentos):
    """N puntos contra el rival programado (saques alternados) -> (aptitud, fracción ganada)."""
    genoma, semilla, puntos = argumentos
    evs = partido.jugar_partido(ControladorRed(genoma), RivalProgramado(semilla), semilla,
                                puntos=puntos)
    return aptitud_etapa2(evs)


@dataclass
class Etapa:
    numero: int
    nombre: str
    evaluar: Callable          # (genoma, semilla, n) -> (aptitud, logro)
    n_evaluacion: int          # pelotas o puntos por evaluación
    n_prueba: int              # pelotas o puntos de la prueba del campeón
    meta: float                # logro que tiene que alcanzar el campeón en la prueba
    max_generaciones: int
    prueba_cada: int
    logro: str                 # cómo se llama el logro (para imprimir)


def etapas():
    """Se arma en una función (no al importar) para que lea config en el momento de usarla."""
    return {
        1: Etapa(1, "lanzapelotas", evaluar_etapa1, config.LANZAMIENTOS_POR_EVALUACION,
                 config.ETAPA1_LANZAMIENTOS_PRUEBA, config.ETAPA1_META_DEVUELTAS,
                 config.ETAPA1_MAX_GENERACIONES, config.ETAPA1_PRUEBA_CADA, "devueltas"),
        2: Etapa(2, "rival programado", evaluar_etapa2, config.PUNTOS_ETAPA2,
                 config.ETAPA2_PUNTOS_PRUEBA, config.ETAPA2_META_GANADOS,
                 config.ETAPA2_MAX_GENERACIONES, config.ETAPA2_PRUEBA_CADA, "ganados"),
    }


def azar_de_generacion(semilla, etapa, generacion):
    """Un generador propio por generación: con una semilla de texto, Python siempre da lo mismo."""
    return random.Random(f"{semilla}-etapa{etapa}-gen{generacion}")


def probar_campeon(etapa, genoma, semilla=SEMILLA_PRUEBA):
    _, logro = etapa.evaluar((genoma, semilla, etapa.n_prueba))
    return logro


def elegir_campeon(etapa, poblacion, aptitudes, mapear):
    """
    Prueba a los CANDIDATOS_PRUEBA mejores de la generación con la batería
    fija y devuelve (genoma, logro) del que mejor lo hace. Se prueban en
    paralelo, como la población.
    """
    orden = sorted(range(len(poblacion)), key=lambda i: aptitudes[i], reverse=True)
    candidatos = [poblacion[i] for i in orden[:config.CANDIDATOS_PRUEBA]]
    logros = [logro for _, logro in mapear(etapa.evaluar, [(g, SEMILLA_PRUEBA, etapa.n_prueba)
                                                          for g in candidatos])]
    mejor = max(range(len(candidatos)), key=lambda k: logros[k])
    return candidatos[mejor], logros[mejor]


# --- El estado del entrenamiento (lo que se guarda en disco) ---

def estado_nuevo(semilla):
    azar = azar_de_generacion(semilla, 1, "inicial")
    return {"semilla": semilla, "etapa": 1, "generacion": 0,
            "poblacion": genetico.poblacion_inicial(azar),
            "campeon": None, "prueba_campeon": 0.0, "terminada": False,
            "campeones": {}, "resumen_etapas": {}, "historial": []}


def cargar_o_crear(carpeta, semilla):
    ruta = os.path.join(carpeta, "estado.json")
    if os.path.exists(ruta):
        estado = _actualizar_formato(cargar_json(ruta))
        if estado["semilla"] != semilla:
            raise ValueError(f"{ruta} es de la semilla {estado['semilla']}, no de la {semilla}")
        print(f"Reanudando: etapa {estado['etapa']}, generación {estado['generacion']}.")
        return estado
    os.makedirs(carpeta, exist_ok=True)
    return estado_nuevo(semilla)


def _actualizar_formato(estado):
    """
    Los estados guardados en F2b (solo etapa 1) llamaban "devueltas_mejor" a
    la columna que ahora se llama "logro_mejor" (en la etapa 2 el logro son
    los puntos ganados). Así se pueden reanudar sin perderlos.
    """
    for fila in estado["historial"]:
        if "devueltas_mejor" in fila:
            fila["logro_mejor"] = fila.pop("devueltas_mejor")
        fila.setdefault("validacion", "")
    estado.setdefault("campeones", {})
    estado.setdefault("resumen_etapas", {})
    return estado


def guardar(carpeta, estado):
    guardar_json(os.path.join(carpeta, "estado.json"), estado)
    filas = [[h[c] for c in COLUMNAS_HISTORIAL] for h in estado["historial"]]
    guardar_csv(os.path.join(carpeta, "historial.csv"), COLUMNAS_HISTORIAL, filas)


def pasar_a_la_siguiente_etapa(carpeta, estado):
    """Guarda al campeón de la etapa que terminó y deja la población lista para la siguiente."""
    # setdefault: los estados guardados antes de F3 no tenían estas claves.
    estado.setdefault("campeones", {})[str(estado["etapa"])] = estado["campeon"]
    estado.setdefault("resumen_etapas", {})[str(estado["etapa"])] = {
        "generaciones": estado["generacion"], "prueba_campeon": estado["prueba_campeon"],
        "validacion_campeon": estado.get("validacion_campeon")}
    if estado["etapa"] == 2:
        # La población base: el punto de partida común de los tratamientos A, B y C.
        guardar_json(os.path.join(carpeta, "poblacion_base.json"),
                     {"semilla": estado["semilla"], "poblacion": estado["poblacion"],
                      "campeon_etapa2": estado["campeon"]})
    estado.update(etapa=estado["etapa"] + 1, generacion=0, campeon=None,
                  prueba_campeon=0.0, validacion_campeon=None, terminada=False)


# --- Una generación ---

def una_generacion(estado, etapa, mapear):
    """Evalúa la población, registra el historial y prepara la generación siguiente."""
    inicio = time.perf_counter()
    gen = estado["generacion"]
    azar = azar_de_generacion(estado["semilla"], etapa.numero, gen)
    semilla_partidos = azar.randrange(2 ** 31)          # los mismos para todos
    trabajos = [(g, semilla_partidos, etapa.n_evaluacion) for g in estado["poblacion"]]
    resultados = mapear(etapa.evaluar, trabajos)
    aptitudes = [a for a, _ in resultados]
    mejor = max(range(len(aptitudes)), key=lambda i: aptitudes[i])
    fila = {"etapa": etapa.numero, "generacion": gen, "mejor": round(aptitudes[mejor], 4),
            "promedio": round(sum(aptitudes) / len(aptitudes), 4),
            "logro_mejor": round(resultados[mejor][1], 4), "prueba_campeon": "",
            "validacion": "", "segundos": 0}
    if gen % etapa.prueba_cada == 0 or gen == etapa.max_generaciones - 1:
        candidato, prueba = elegir_campeon(etapa, estado["poblacion"], aptitudes, mapear)
        fila["prueba_campeon"] = round(prueba, 4)
        if estado["campeon"] is None or prueba >= estado["prueba_campeon"]:
            estado["campeon"], estado["prueba_campeon"] = candidato, prueba
        if prueba >= etapa.meta:
            # MALDICIÓN DEL GANADOR: como elegimos al campeón con la batería
            # de prueba, su resultado en ella está inflado por la suerte. Antes
            # de dar la etapa por terminada, se lo confirma con una batería
            # que no se usó para elegirlo.
            validacion = probar_campeon(etapa, candidato, SEMILLA_VALIDACION)
            fila["validacion"] = round(validacion, 4)
            if validacion >= etapa.meta:
                estado["campeon"], estado["prueba_campeon"] = candidato, prueba
                estado["validacion_campeon"] = validacion
                estado["terminada"] = True
    estado["poblacion"] = genetico.siguiente_generacion(estado["poblacion"], aptitudes, azar)
    estado["generacion"] = gen + 1
    if estado["generacion"] >= etapa.max_generaciones:
        estado["terminada"] = True
    fila["segundos"] = round(time.perf_counter() - inicio, 2)
    estado["historial"].append(fila)
    return fila


def _imprimir(fila, etapa):
    prueba = f"{fila['prueba_campeon']:.0%}" if fila["prueba_campeon"] != "" else ""
    validacion = f"{fila['validacion']:.0%}" if fila["validacion"] != "" else ""
    print(f"{fila['generacion']:3d}  {fila['mejor']:7.3f}  {fila['promedio']:8.3f}  "
          f"{fila['logro_mejor']:12.0%}  {prueba:>14}  {validacion:>10}  {fila['segundos']:8.1f}")


# --- El currículo ---

def entrenar(carpeta, semilla, procesos, generaciones=None, hasta_etapa=2):
    """
    Entrena etapa por etapa hasta terminar `hasta_etapa`. Si se da
    `generaciones`, para cuando la etapa actual llega a esa generación (para
    pruebas y corridas cortas; al volver a correr, sigue).
    """
    estado = cargar_o_crear(carpeta, semilla)
    mapear, pool = _preparar_paralelo(procesos)
    try:
        while estado["etapa"] <= hasta_etapa:
            etapa = etapas()[estado["etapa"]]
            limite = etapa.max_generaciones if generaciones is None else generaciones
            print(f"\nEtapa {etapa.numero} ({etapa.nombre})")
            print(f"gen    mejor  promedio  {etapa.logro + '(mejor)':>12}  prueba campeón  validación  segundos")
            while not estado["terminada"] and estado["generacion"] < limite:
                _imprimir(una_generacion(estado, etapa, mapear), etapa)
                guardar(carpeta, estado)
            if not estado["terminada"]:
                break                                   # se pidió parar antes
            validacion = estado.get("validacion_campeon")
            texto = f" y {validacion:.0%} en la validación" if validacion is not None else ""
            print(f"Etapa {etapa.numero} terminada en la generación {estado['generacion']}: "
                  f"el campeón logra {estado['prueba_campeon']:.0%} ({etapa.logro}) en la prueba{texto}.")
            pasar_a_la_siguiente_etapa(carpeta, estado)
            guardar(carpeta, estado)
    finally:
        if pool is not None:
            pool.close()
            pool.join()
    return estado


def entrenar_etapa1(carpeta, semilla, procesos, generaciones=None):
    """Solo la etapa 1 (la usan las pruebas y el capítulo 4)."""
    return entrenar(carpeta, semilla, procesos, generaciones, hasta_etapa=1)


def _preparar_paralelo(procesos):
    """Con 1 proceso se evalúa en serie (más fácil de depurar); con más, con un Pool."""
    if procesos <= 1:
        return (lambda f, trabajos: [f(t) for t in trabajos]), None
    import multiprocessing
    pool = multiprocessing.Pool(procesos)
    return pool.map, pool


# --- Etapa 3: IA contra IA (coevolución, capítulo 6) ---
#
# Ya no hay un rival fijo: cada individuo juega contra otros individuos.
# Problema: si solo jugara contra la población actual, la evolución podría
# "olvidar" cómo ganarle a estrategias viejas y dar vueltas en círculo
# (A le gana a B, B a C, C a A...). El SALÓN DE LA FAMA guarda al campeón de
# cada generación, y cada individuo juega también contra campeones viejos
# elegidos al azar: así no conviene olvidar.

def evaluar_etapa3(argumentos):
    """
    Un individuo juega sus partidos contra varios rivales, en los dos lados.
    Devuelve (aptitud según el tratamiento, fracción de anulados, fracción ganada).
    """
    genoma, rivales, semillas, lados, tratamiento = argumentos
    yo = ControladorRed(genoma)
    partidos = []
    for rival, semilla, lado in zip(rivales, semillas, lados):
        otro = ControladorRed(rival)
        izquierda, derecha = (yo, otro) if lado == 0 else (otro, yo)
        partidos.append((partido.jugar_partido(izquierda, derecha, semilla), lado))
    ganada = (aptitud.aptitud_A(partidos) + 1) / 2      # A va de -1 a 1; esto, de 0 a 1
    return aptitud.APTITUDES[tratamiento](partidos), aptitud.anulados(partidos), ganada


def elegir_rivales(i, poblacion, salon, azar):
    """RIVALES_POBLACION de la población actual (sin él mismo) + RIVALES_SALON del salón."""
    otros = [j for j in range(len(poblacion)) if j != i]
    rivales = [poblacion[j] for j in azar.sample(otros, config.RIVALES_POBLACION)]
    fuente = salon if salon else poblacion            # en la generación 0 el salón está vacío
    rivales += [azar.choice(fuente) for _ in range(config.RIVALES_SALON)]
    return rivales


def estado_rama_nuevo(poblacion_base, tratamiento, semilla):
    return {"semilla": semilla, "tratamiento": tratamiento, "generacion": 0,
            "poblacion": [list(g) for g in poblacion_base["poblacion"]],
            "salon": [], "historial": [], "metricas": []}


def una_generacion_etapa3(estado, mapear, ultima=None):
    """`ultima`: la última generación de esta corrida (también se miden sus métricas)."""
    inicio = time.perf_counter()
    gen, tratamiento = estado["generacion"], estado["tratamiento"]
    azar = azar_de_generacion(estado["semilla"], f"3{tratamiento}", gen)
    n_partidos = config.RIVALES_POBLACION + config.RIVALES_SALON
    semillas = [azar.randrange(2 ** 31) for _ in range(n_partidos)]   # los mismos saques para todos
    lados = [k % 2 for k in range(n_partidos)]                          # mitad en cada lado
    trabajos = [(g, elegir_rivales(i, estado["poblacion"], estado["salon"], azar), semillas, lados,
                 tratamiento) for i, g in enumerate(estado["poblacion"])]
    resultados = mapear(evaluar_etapa3, trabajos)
    aptitudes = [r[0] for r in resultados]
    mejor = max(range(len(aptitudes)), key=lambda i: aptitudes[i])
    campeon = estado["poblacion"][mejor]
    estado["salon"].append(list(campeon))
    ultima = config.ETAPA3_GENERACIONES - 1 if ultima is None else ultima
    if gen % config.METRICAS_CADA == 0 or gen == ultima:
        estado["metricas"].append({"generacion": gen, **metricas.medir(ControladorRed(campeon))})
    fila = {"generacion": gen, "mejor": round(aptitudes[mejor], 4),
            "promedio": round(sum(aptitudes) / len(aptitudes), 4),
            "anulados": round(sum(r[1] for r in resultados) / len(resultados), 4),
            "ganada_mejor": round(resultados[mejor][2], 4), "segundos": 0}
    estado["poblacion"] = genetico.siguiente_generacion(estado["poblacion"], aptitudes, azar)
    estado["generacion"] = gen + 1
    fila["segundos"] = round(time.perf_counter() - inicio, 2)
    estado["historial"].append(fila)
    return fila


COLUMNAS_ETAPA3 = ["generacion", "mejor", "promedio", "anulados", "ganada_mejor", "segundos"]


def guardar_rama(carpeta, estado):
    guardar_json(os.path.join(carpeta, "estado.json"), estado)
    filas = [[h[c] for c in COLUMNAS_ETAPA3] for h in estado["historial"]]
    guardar_csv(os.path.join(carpeta, "historial.csv"), COLUMNAS_ETAPA3, filas)


def entrenar_etapa3(carpeta, ruta_base, tratamiento, procesos, generaciones=None):
    """
    Una RAMA de la etapa 3: parte de la población base y evoluciona con la
    aptitud del tratamiento (A, B o C). Reanudable como las otras etapas.
    """
    ruta = os.path.join(carpeta, "estado.json")
    if os.path.exists(ruta):
        estado = cargar_json(ruta)
        print(f"Reanudando rama {tratamiento}: generación {estado['generacion']}.")
    else:
        os.makedirs(carpeta, exist_ok=True)
        base = cargar_json(ruta_base)
        estado = estado_rama_nuevo(base, tratamiento, base["semilla"])
    limite = config.ETAPA3_GENERACIONES if generaciones is None else generaciones
    mapear, pool = _preparar_paralelo(procesos)
    try:
        print(f"\nEtapa 3, tratamiento {tratamiento}")
        print("gen    mejor  promedio  anulados  ganada(mejor)  segundos")
        while estado["generacion"] < limite:
            fila = una_generacion_etapa3(estado, mapear, ultima=limite - 1)
            guardar_rama(carpeta, estado)
            print(f"{fila['generacion']:3d}  {fila['mejor']:7.3f}  {fila['promedio']:8.3f}  "
                  f"{fila['anulados']:8.0%}  {fila['ganada_mejor']:13.0%}  {fila['segundos']:8.1f}")
    finally:
        if pool is not None:
            pool.close()
            pool.join()
    return estado


# --- Grabar al campeón para verlo en ver2d.py ---

def campeon_mas_reciente(estado):
    """(etapa, genoma) del campeón más avanzado que haya."""
    if estado["campeon"] is not None:
        return estado["etapa"], estado["campeon"]
    if estado.get("campeones"):
        etapa = max(estado["campeones"], key=int)
        return int(etapa), estado["campeones"][etapa]
    raise ValueError("Todavía no hay campeón: entrena al menos una generación.")


def grabar_campeon(carpeta, puntos=8):
    estado = cargar_json(os.path.join(carpeta, "estado.json"))
    numero, genoma = campeon_mas_reciente(estado)
    nombre_ia = f"IA etapa {numero}"
    if numero == 1:
        g = grabar.nueva_grabacion([nombre_ia, "lanzapelotas"], etapa=1, semilla=estado["semilla"])
        partido.jugar_partido(ControladorRed(genoma), ControladorAusente(), SEMILLA_PRUEBA,
                              puntos=puntos, saque=lanzapelotas, receptor_fijo=0, grabacion=g)
    else:
        g = grabar.nueva_grabacion([nombre_ia, "rival programado"], etapa=numero,
                                   semilla=estado["semilla"])
        partido.jugar_partido(ControladorRed(genoma), RivalProgramado(SEMILLA_PRUEBA),
                              SEMILLA_PRUEBA, puntos=puntos, grabacion=g)
    ruta = os.path.join(carpeta, f"campeon_etapa{numero}.json")
    grabar.guardar_grabacion(g, ruta)
    return ruta


def _principal():
    parser = argparse.ArgumentParser(description="Entrenamiento por etapas.")
    parser.add_argument("--carpeta", required=True, help="dónde guardar el estado (ej. resultados/prueba)")
    parser.add_argument("--semilla", type=int, default=1)
    parser.add_argument("--procesos", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--generaciones", type=int, help="parar al llegar a esta generación")
    parser.add_argument("--hasta-etapa", type=int, default=2, help="última etapa a entrenar")
    parser.add_argument("--grabar-campeon", action="store_true", help="grabar al campeón y salir")
    args = parser.parse_args()
    if args.grabar_campeon:
        ruta = grabar_campeon(args.carpeta)
        print(f"Grabación en {ruta}  (verla con: python ver2d.py {ruta})")
        return
    entrenar(args.carpeta, args.semilla, args.procesos, args.generaciones, args.hasta_etapa)


if __name__ == "__main__":
    _principal()
