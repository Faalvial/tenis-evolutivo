"""
experimentos.py — El experimento completo: semillas × tratamientos (sección 9 del plan).

Para cada semilla:
  1. el currículo (etapas 1 y 2) se entrena UNA sola vez -> población base;
  2. desde esa MISMA población base salen tres ramas de la etapa 3, una por
     tratamiento (A ganar, B pelotear, C precisión).
Así los tres tratamientos parten de jugadores idénticos y solo difieren en la
aptitud: es el control experimental clave (la "bifurcación", sección 6).

Todo es reanudable: si se corta, el mismo comando sigue donde quedó (cada
pieza guarda su propio estado). Distintas computadoras pueden correr
distintas semillas y después juntar las carpetas.

Estructura de carpetas:
    resultados/experimento/
        semilla_1/curriculo/        estado.json, historial.csv, poblacion_base.json
        semilla_1/rama_A/           estado.json (con el salón y las métricas), historial.csv
        semilla_1/rama_B/ ...
        resumen.json                métricas finales de cada rama (para graficos.py)

Uso:
    python experimentos.py --carpeta resultados/experimento --semillas 1 2 3 4 5
    python experimentos.py --carpeta resultados/corto --semillas 1 --generaciones 20   (prueba corta)
"""

import argparse
import os

import config
import entrenar
from guardado import cargar_json, guardar_json

TRATAMIENTOS = ("A", "B", "C")


def carpeta_semilla(carpeta, semilla):
    return os.path.join(carpeta, f"semilla_{semilla}")


def correr_semilla(carpeta, semilla, tratamientos, procesos, generaciones=None):
    base = carpeta_semilla(carpeta, semilla)
    curriculo = os.path.join(base, "curriculo")
    ruta_base = os.path.join(curriculo, "poblacion_base.json")
    if not os.path.exists(ruta_base):
        print(f"\n=== Semilla {semilla}: currículo (etapas 1 y 2) ===")
        entrenar.entrenar(curriculo, semilla, procesos, hasta_etapa=2)
    for tratamiento in tratamientos:
        print(f"\n=== Semilla {semilla}: rama {tratamiento} ===")
        entrenar.entrenar_etapa3(os.path.join(base, f"rama_{tratamiento}"), ruta_base,
                                 tratamiento, procesos, generaciones)


def resumir(carpeta):
    """Junta las métricas de todas las ramas terminadas en resumen.json."""
    resumen = []
    for nombre in sorted(os.listdir(carpeta)):
        if not nombre.startswith("semilla_"):
            continue
        for tratamiento in TRATAMIENTOS:
            ruta = os.path.join(carpeta, nombre, f"rama_{tratamiento}", "estado.json")
            if not os.path.exists(ruta):
                continue
            estado = cargar_json(ruta)
            resumen.append({"semilla": estado["semilla"], "tratamiento": tratamiento,
                            "generaciones": estado["generacion"], "metricas": estado["metricas"],
                            "metricas_poblacion": estado.get("metricas_poblacion", []),
                            "historial": estado["historial"]})
    guardar_json(os.path.join(carpeta, "resumen.json"), resumen)
    return resumen


def _principal():
    parser = argparse.ArgumentParser(description="Experimento: semillas × tratamientos.")
    parser.add_argument("--carpeta", required=True)
    parser.add_argument("--semillas", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    parser.add_argument("--tratamientos", nargs="+", default=list(TRATAMIENTOS), choices=TRATAMIENTOS)
    parser.add_argument("--procesos", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--generaciones", type=int, default=config.ETAPA3_GENERACIONES,
                        help="generaciones de la etapa 3 por rama")
    args = parser.parse_args()
    for semilla in args.semillas:
        correr_semilla(args.carpeta, semilla, args.tratamientos, args.procesos, args.generaciones)
    resumen = resumir(args.carpeta)
    print(f"\nResumen de {len(resumen)} ramas en {os.path.join(args.carpeta, 'resumen.json')}")


if __name__ == "__main__":
    _principal()
