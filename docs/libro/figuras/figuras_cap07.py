"""
figuras_cap07.py — Figuras del capítulo 7 a partir de un experimento ya corrido.

Uso (desde la raíz del repositorio):
    python docs/libro/figuras/figuras_cap07.py --carpeta resultados/ejemplo

1. Corre graficos.py sobre el experimento y copia sus gráficos a docs/libro/img
   (cap07_curvas.png, cap07_curvas_poblacion.png, cap07_cajas.png, cap07_botes.png).
2. Dibuja la "cronofotografía" (sección 9 del plan): para cada tratamiento, el
   campeón final de la primera semilla juega contra el rival de referencia y se
   dibuja la trayectoria de la pelota en un punto típico (el de golpes válidos
   más cercano al promedio de su batería).
3. Graba un partido del campeón final de cada tratamiento contra el rival de
   referencia, para verlo con ver2d.py o ver3d.py.
"""

import argparse
import os
import shutil
import statistics
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, RAIZ)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config
import grabar
import graficos
import partido
from aptitud import separar_puntos
from guardado import cargar_json
from metricas import SEMILLA_BATERIA
from red import ControladorRed
from rivales import RivalProgramado

CARPETA_IMG = os.path.join(RAIZ, "docs", "libro", "img")
TINTA, TINTA_2, GRILLA = "#0b0b0b", "#52514e", "#e4e3df"
RIVAL = "#898781"


def copiar_graficos(carpeta):
    salida, _ = graficos.generar(carpeta)
    for origen, destino in (("curvas.png", "cap07_curvas.png"), ("cajas.png", "cap07_cajas.png"),
                            ("mapa_botes.png", "cap07_botes.png"),
                            ("curvas_poblacion.png", "cap07_curvas_poblacion.png")):
        if os.path.exists(os.path.join(salida, origen)):
            shutil.copy(os.path.join(salida, origen), os.path.join(CARPETA_IMG, destino))
    return salida


def campeon_final(carpeta, semilla, tratamiento):
    estado = cargar_json(os.path.join(carpeta, f"semilla_{semilla}", f"rama_{tratamiento}", "estado.json"))
    return estado["salon"][-1], estado["generacion"]


def punto_tipico(g):
    """(t_inicio, t_fin) del punto con golpes válidos más cercano al promedio."""
    puntos = separar_puntos(g["eventos"])
    promedio = statistics.mean(p[-1]["golpes_validos"] for p in puntos)
    elegido = min(puntos, key=lambda p: (abs(p[-1]["golpes_validos"] - promedio), -p[-1]["golpes_validos"]))
    return elegido[0]["t"], elegido[-1]["t"], elegido


def cronofotografia(carpeta, semilla, ruta, puntos=20):
    tratamientos = [t for t in graficos.TRATAMIENTOS
                    if os.path.exists(os.path.join(carpeta, f"semilla_{semilla}", f"rama_{t}"))]
    fig, ejes = plt.subplots(len(tratamientos), 1, figsize=(10, 2.4 * len(tratamientos)), dpi=130,
                             sharex=True)
    for ax, t in zip(ejes, tratamientos):
        genoma, gen = campeon_final(carpeta, semilla, t)
        g = grabar.nueva_grabacion([f"{t} gen {gen}", "rival programado"], tratamiento=t, generacion=gen)
        partido.jugar_partido(ControladorRed(genoma), RivalProgramado(SEMILLA_BATERIA), SEMILLA_BATERIA,
                              puntos=puntos, grabacion=g)
        grabar.guardar_grabacion(g, os.path.join(carpeta, f"partido_campeon_{t}.json"))
        t0, t1, evs = punto_tipico(g)
        cuadros = [grabar.cuadro_como_dict(g, i) for i in range(len(g["cuadros"]))]
        cuadros = [c for c in cuadros if t0 <= c["t"] <= t1]
        golpes = [ev for ev in evs if ev["tipo"] == "golpe"]
        cortes = [t0] + [ev["t"] for ev in golpes] + [t1 + 1]
        for k in range(len(cortes) - 1):
            tramo = [c for c in cuadros if cortes[k] <= c["t"] <= cortes[k + 1]]
            color = RIVAL if k == 0 or golpes[k - 1]["jugador"] == 1 else graficos.COLORES[t]
            ax.plot([c["pelota_x"] for c in tramo], [c["pelota_y"] for c in tramo], color=color, linewidth=2)
        for ev in golpes:
            ax.plot(ev["x"], ev["y"], "o", markersize=7, markeredgecolor="white",
                    color=graficos.COLORES[t] if ev["jugador"] == 0 else RIVAL, zorder=3)
        ax.axhline(0, color=TINTA_2, linewidth=1)
        ax.plot([0, config.ANCHO_CANCHA], [0, 0], color="#008300", linewidth=4)
        ax.plot([config.X_RED, config.X_RED], [0, config.ALTO_RED], color=TINTA, linewidth=3)
        final = evs[-1]
        ax.set_title(f"{graficos.NOMBRES[t]} (izquierda) contra el rival de referencia: "
                     f"{final['golpes_validos']} golpes válidos, termina por {final['motivo']}",
                     fontsize=9, color=TINTA, loc="left")
        ax.set_ylim(-15, 420)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        ax.tick_params(colors=TINTA_2, labelsize=7)
    ejes[-1].set_xlabel("x (unidades de pymunk)", color=TINTA_2)
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--carpeta", required=True)
    parser.add_argument("--semilla", type=int, default=1)
    args = parser.parse_args()
    os.makedirs(CARPETA_IMG, exist_ok=True)
    salida = copiar_graficos(args.carpeta)
    cronofotografia(args.carpeta, args.semilla, os.path.join(CARPETA_IMG, "cap07_cronofotografia.png"))
    print(f"Gráficos en {salida} y figuras en {CARPETA_IMG}")


if __name__ == "__main__":
    main()
