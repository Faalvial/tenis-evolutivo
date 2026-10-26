"""
figuras_cap03.py — Genera las figuras del capítulo 3 del libro (red neuronal).

Uso (desde la raíz del repositorio):
    python docs/libro/figuras/figuras_cap03.py

1. cap03_red_a_mano.png: la red escrita a mano, con el grosor de cada flecha
   proporcional al peso (azul = positivo, naranja = negativo).
2. cap03_aprendizaje.png: aptitud del mejor y del promedio por generación.
3. cap03_recorridos.png: cómo persigue el objetivo el campeón de la
   generación 0, el campeón final y la red escrita a mano.
"""

import os
import random
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, RAIZ)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ejercicios import seguir_punto as sp

CARPETA_IMG = os.path.join(RAIZ, "docs", "libro", "img")
POSITIVO, NEGATIVO = "#2a78d6", "#eb6834"
GRIS, TINTA, TINTA_2, GRILLA = "#898781", "#0b0b0b", "#52514e", "#e4e3df"
NOMBRES_ENTRADAS = ["dx", "dy", "vx", "vy"]
NOMBRES_SALIDAS = ["acel. x", "acel. y"]
SEMILLA = 1


def _ejes_limpios(ax):
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(GRILLA)
    ax.tick_params(colors=TINTA_2, labelsize=8)


def figura_red(genoma, ruta, titulo):
    """Dibuja la red: círculos = neuronas, flechas = pesos."""
    capas = [sp.ENTRADAS, sp.OCULTAS, sp.SALIDAS]
    posiciones = []
    for c, n in enumerate(capas):
        posiciones.append([(c, (n - 1) / 2 - k) for k in range(n)])
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=130)
    i = 0
    for c in (1, 2):                                   # cada capa lee la anterior
        for destino in posiciones[c]:
            for origen in posiciones[c - 1]:
                w = genoma[i]
                i += 1
                if abs(w) > 0.05:
                    ax.plot([origen[0], destino[0]], [origen[1], destino[1]],
                            color=POSITIVO if w > 0 else NEGATIVO, linewidth=1.2 * abs(w),
                            alpha=0.85, zorder=1, solid_capstyle="round")
            i += 1                                     # el sesgo no se dibuja como flecha
    for c, capa_pos in enumerate(posiciones):
        for k, (x, y) in enumerate(capa_pos):
            ax.scatter([x], [y], s=900, color="white", edgecolor=TINTA_2, linewidth=1.5, zorder=2)
            if c == 0:
                ax.text(x - 0.12, y, NOMBRES_ENTRADAS[k], ha="right", va="center", color=TINTA, fontsize=10)
            elif c == 2:
                ax.text(x + 0.12, y, NOMBRES_SALIDAS[k], ha="left", va="center", color=TINTA, fontsize=10)
    for c, nombre in enumerate(("entradas", "capa oculta (tanh)", "salidas (tanh)")):
        ax.text(c, 2.45, nombre, ha="center", color=TINTA_2, fontsize=9)
    leyenda = [plt.Line2D([], [], color=POSITIVO, lw=3, label="peso positivo"),
               plt.Line2D([], [], color=NEGATIVO, lw=3, label="peso negativo")]
    ax.legend(handles=leyenda, loc="lower center", frameon=False, ncol=2, fontsize=9,
              bbox_to_anchor=(0.5, -0.08))
    ax.set_title(titulo, color=TINTA, fontsize=11, loc="left")
    ax.set_xlim(-0.8, 2.8)
    ax.set_ylim(-2.4, 2.7)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def figura_aprendizaje(historial, ruta):
    gens = range(len(historial))
    fig, ax = plt.subplots(figsize=(7, 3.4), dpi=130)
    ax.plot(gens, [-m for m, _ in historial], color=POSITIVO, linewidth=2, label="mejor de la generación")
    ax.plot(gens, [-p for _, p in historial], color=GRIS, linewidth=2, label="promedio de la población")
    ax.set_yscale("log")
    ax.set_xlabel("generación", color=TINTA_2)
    ax.set_ylabel("distancia promedio al objetivo\n(escala logarítmica; menos = mejor)", color=TINTA_2)
    ax.set_title("La evolución encuentra pesos que persiguen cada vez mejor",
                 color=TINTA, fontsize=11, loc="left")
    ax.legend(frameon=False, fontsize=9)
    ax.grid(axis="y", color=GRILLA, linewidth=0.8)
    _ejes_limpios(ax)
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def figura_recorridos(campeones, ruta):
    mov = sp.movimiento_objetivo(random.Random(2026))
    casos = [("campeón de la generación 0", campeones[0]),
             ("campeón final", campeones[-1]),
             ("red escrita a mano", sp.red_a_mano())]
    fig, ejes = plt.subplots(1, 3, figsize=(10, 3.6), dpi=130)
    for ax, (nombre, genoma) in zip(ejes, casos):
        distancia, recorrido = sp.simular(genoma, mov, guardar_recorrido=True)
        ax.plot([o[0] for _, o in recorrido], [o[1] for _, o in recorrido],
                color=GRIS, linewidth=1.5, linestyle="--", label="objetivo")
        ax.plot([b[0] for b, _ in recorrido], [b[1] for b, _ in recorrido],
                color=POSITIVO, linewidth=2, label="bicho")
        ax.scatter([0], [0], color=TINTA, s=18, zorder=3)
        ax.set_title(f"{nombre}\ndistancia promedio {distancia:.2f}", color=TINTA, fontsize=10)
        ax.set_xlim(-6, 6)
        ax.set_ylim(-6, 6)
        ax.set_aspect("equal")
        _ejes_limpios(ax)
    ejes[0].legend(frameon=False, fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def main():
    os.makedirs(CARPETA_IMG, exist_ok=True)
    historial, campeones = sp.evolucionar(SEMILLA)
    figura_red(sp.red_a_mano(), os.path.join(CARPETA_IMG, "cap03_red_a_mano.png"),
               "La red escrita a mano (los sesgos son 0)")
    figura_red(campeones[-1], os.path.join(CARPETA_IMG, "cap03_red_evolucionada.png"),
               "La red que encontró la evolución (semilla 1, generación 39)")
    figura_aprendizaje(historial, os.path.join(CARPETA_IMG, "cap03_aprendizaje.png"))
    figura_recorridos(campeones, os.path.join(CARPETA_IMG, "cap03_recorridos.png"))
    print("Figuras guardadas en", CARPETA_IMG)


if __name__ == "__main__":
    main()
