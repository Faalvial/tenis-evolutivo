"""
figuras_cap01.py — Genera las figuras del capítulo 1 del libro.

Uso (desde la raíz del repositorio):
    python docs/libro/figuras/figuras_cap01.py

Simula un partido entre dos rivales programados y dibuja la trayectoria de
la pelota en el punto más largo ("cronofotografía"), coloreada según quién la
golpeó por última vez.
"""

import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, RAIZ)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config
import grabar
import partido
from rivales import RivalProgramado

CARPETA_IMG = os.path.join(RAIZ, "docs", "libro", "img")
COLOR_LADO = ("#2a78d6", "#eb6834")      # izquierda azul, derecha naranja (como ver2d)
COLOR_SAQUE = "#898781"
TINTA, TINTA_2, GRILLA = "#0b0b0b", "#52514e", "#e4e3df"


def punto_mas_largo(g):
    """(t_inicio, t_fin, eventos) del punto con más golpes válidos."""
    puntos, actual = [], []
    for ev in g["eventos"]:
        actual.append(ev)
        if ev["tipo"] == "punto":
            puntos.append(actual)
            actual = []
    evs = max(puntos, key=lambda p: p[-1]["golpes_validos"])
    return evs[0]["t"], evs[-1]["t"], evs


def figura_trayectoria(g, ruta):
    t0, t1, evs = punto_mas_largo(g)
    cuadros = [grabar.cuadro_como_dict(g, i) for i in range(len(g["cuadros"]))]
    cuadros = [c for c in cuadros if t0 <= c["t"] <= t1]
    golpes = [ev for ev in evs if ev["tipo"] == "golpe"]

    fig, ax = plt.subplots(figsize=(10, 3.6), dpi=130)
    # Trayectoria por tramos: cada tramo con el color de quien golpeó.
    cortes = [t0] + [ev["t"] for ev in golpes] + [t1 + 1]
    for i in range(len(cortes) - 1):
        tramo = [c for c in cuadros if cortes[i] <= c["t"] <= cortes[i + 1]]
        color = COLOR_SAQUE if i == 0 else COLOR_LADO[golpes[i - 1]["jugador"]]
        ax.plot([c["pelota_x"] for c in tramo], [c["pelota_y"] for c in tramo],
                color=color, linewidth=2, solid_capstyle="round")
    for ev in golpes:
        ax.plot(ev["x"], ev["y"], "o", markersize=8, color=COLOR_LADO[ev["jugador"]],
                markeredgecolor="white", markeredgewidth=2, zorder=3)
    for ev in evs:
        if ev["tipo"] == "bote" and ev["valido"]:
            ax.plot(ev["x"], 0, "v", markersize=8, color=TINTA_2, zorder=3)
    # Cancha, red y techo.
    ax.axhline(0, color=TINTA_2, linewidth=1)
    ax.plot([0, config.ANCHO_CANCHA], [0, 0], color="#008300", linewidth=4, solid_capstyle="butt")
    ax.plot([config.X_RED, config.X_RED], [0, config.ALTO_RED], color=TINTA, linewidth=3)
    ax.text(config.X_RED, config.ALTO_RED + 12, "red", ha="center", color=TINTA_2, fontsize=9)
    ax.set_xlim(-config.ESPACIO_DETRAS_FONDO, config.ANCHO_CANCHA + config.ESPACIO_DETRAS_FONDO)
    ax.set_ylim(-15, max(c["pelota_y"] for c in cuadros) * 1.15)
    ax.set_xlabel("x (unidades de pymunk)", color=TINTA_2)
    ax.set_ylabel("altura y", color=TINTA_2)
    ax.set_title(f"Un punto entre dos rivales programados: {len(golpes)} golpes, "
                 f"{evs[-1]['golpes_validos']} válidos (motivo final: {evs[-1]['motivo']})",
                 color=TINTA, fontsize=11, loc="left")
    leyenda = [plt.Line2D([], [], color=COLOR_SAQUE, lw=2, label="saque"),
               plt.Line2D([], [], color=COLOR_LADO[0], lw=2, marker="o", label="golpe del jugador 0"),
               plt.Line2D([], [], color=COLOR_LADO[1], lw=2, marker="o", label="golpe del jugador 1"),
               plt.Line2D([], [], color=TINTA_2, lw=0, marker="v", label="bote válido")]
    ax.legend(handles=leyenda, loc="upper right", frameon=False, fontsize=9, ncol=4)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.spines["left"].set_color(GRILLA)
    ax.spines["bottom"].set_color(GRILLA)
    ax.tick_params(colors=TINTA_2, labelsize=8)
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def main():
    os.makedirs(CARPETA_IMG, exist_ok=True)
    g = grabar.nueva_grabacion(["rival A", "rival B"])
    partido.jugar_partido(RivalProgramado(3), RivalProgramado(1003), semilla=3, grabacion=g)
    ruta = os.path.join(CARPETA_IMG, "cap01_trayectoria.png")
    figura_trayectoria(g, ruta)
    print("Figura guardada en", ruta)


if __name__ == "__main__":
    main()
