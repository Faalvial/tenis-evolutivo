"""
medir_etapa1.py — Compara los tipos de cruce en la etapa 1 (capítulo 4).

Uso (desde la raíz del repositorio; tarda varios minutos):
    python docs/libro/figuras/medir_etapa1.py --procesos 4

Para cada tipo de cruce ("neurona", "uniforme", "ninguno") y cada semilla,
entrena la etapa 1 hasta cumplir la meta o llegar al máximo de generaciones,
y anota en qué generación terminó y cuánto devuelve el campeón en una batería
NUEVA de 200 pelotas. Guarda el resumen en resultados/medir_etapa1/resumen.json
y dibuja docs/libro/img/cap04_cruces.png.
"""

import argparse
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, RAIZ)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config
import entrenar
from guardado import cargar_json, guardar_json

CRUCES = ("neurona", "uniforme", "ninguno")
SEMILLAS = (1, 2, 3, 4, 5)
COLORES = {"neurona": "#2a78d6", "uniforme": "#eb6834", "ninguno": "#1baf7a"}
TINTA, TINTA_2, GRILLA = "#0b0b0b", "#52514e", "#e4e3df"
CARPETA = os.path.join(RAIZ, "resultados", "medir_etapa1")


def devueltas_nuevas(genoma):
    """Fracción devuelta en 5 baterías nuevas de 40 pelotas (200 en total)."""
    total = 0.0
    for k in range(5):
        _, d = entrenar.evaluar_etapa1((genoma, 777 + k, 40))
        total += d
    return total / 5


def correr(procesos):
    resumen = {}
    ruta_resumen = os.path.join(CARPETA, "resumen.json")
    if os.path.exists(ruta_resumen):
        resumen = cargar_json(ruta_resumen)
    for cruce in CRUCES:
        config.TIPO_CRUCE = cruce
        for semilla in SEMILLAS:
            clave = f"{cruce}-{semilla}"
            if clave in resumen:
                continue
            estado = entrenar.entrenar_etapa1(os.path.join(CARPETA, clave), semilla, procesos)
            fin = estado["resumen_etapas"]["1"]
            resumen[clave] = {
                "cruce": cruce, "semilla": semilla, "generaciones": fin["generaciones"],
                "logro_meta": fin["prueba_campeon"] >= config.ETAPA1_META_DEVUELTAS,
                "devueltas_nuevas": devueltas_nuevas(estado["campeones"]["1"]),
                "promedio": [h["promedio"] for h in estado["historial"] if h["etapa"] == 1],
            }
            guardar_json(ruta_resumen, resumen)
    return resumen


def tabla(resumen):
    print("| Cruce | Generaciones hasta la meta (cada semilla) | Promedio | Lograron la meta | Devuelve en pelotas nuevas |")
    print("|---|---|---|---|---|")
    for cruce in CRUCES:
        filas = [resumen[f"{cruce}-{s}"] for s in SEMILLAS]
        gens = [f["generaciones"] for f in filas]
        logradas = sum(f["logro_meta"] for f in filas)
        nuevas = sum(f["devueltas_nuevas"] for f in filas) / len(filas)
        print(f"| {cruce} | {', '.join(map(str, gens))} | {sum(gens) / len(gens):.0f} "
              f"| {logradas} de {len(filas)} | {nuevas:.0%} |")


def figura(resumen, ruta):
    fig, ax = plt.subplots(figsize=(7.5, 3.6), dpi=130)
    for cruce in CRUCES:
        for s in SEMILLAS:
            curva = resumen[f"{cruce}-{s}"]["promedio"]
            ax.plot(range(len(curva)), curva, color=COLORES[cruce], linewidth=1.6, alpha=0.75,
                    label=f"cruce {cruce}" if s == SEMILLAS[0] else None)
    ax.set_xlabel("generación", color=TINTA_2)
    ax.set_ylabel("aptitud promedio de la población", color=TINTA_2)
    ax.set_title("Etapa 1: cada línea es una semilla; terminan al cumplir la meta",
                 color=TINTA, fontsize=11, loc="left")
    ax.legend(frameon=False, fontsize=9)
    ax.grid(axis="y", color=GRILLA, linewidth=0.8)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(GRILLA)
    ax.tick_params(colors=TINTA_2, labelsize=8)
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--procesos", type=int, default=os.cpu_count() or 1)
    resumen = correr(parser.parse_args().procesos)
    tabla(resumen)
    figura(resumen, os.path.join(RAIZ, "docs", "libro", "img", "cap04_cruces.png"))


if __name__ == "__main__":
    main()
