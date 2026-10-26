"""
graficos.py — Gráficos, tabla y estadística del experimento (sección 9 del plan).

Lee resultados/<experimento>/resumen.json (lo arma experimentos.py) y genera,
en resultados/<experimento>/graficos/:
  curvas.png        cada métrica por generación: promedio ± desviación estándar entre semillas
  cajas.png         diagramas de caja de las métricas finales, por tratamiento
  mapa_botes.png    dónde botan los tiros válidos de cada tratamiento (mapa de calor)
  tabla.md/.csv     promedio ± desviación estándar y valores p de Mann-Whitney
  curvas_poblacion.png, tabla_poblacion.md/.csv
                    lo mismo con el promedio de los 10 mejores de la población
                    (medida complementaria, más estable que un solo campeón)

Estadística: la prueba U de Mann-Whitney compara dos grupos (por ejemplo, las
5 semillas de A contra las 5 de B) sin suponer que los datos siguen una
campana de Gauss, y funciona con pocos datos. El valor p es la probabilidad
de ver una diferencia así de grande si en realidad los dos tratamientos fueran
iguales: si es chico (menos de 0,05, por convención), la diferencia
probablemente no es casualidad.

Uso:
    python graficos.py --carpeta resultados/experimento
"""

import argparse
import itertools
import os
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu

import config
from guardado import cargar_json

TRATAMIENTOS = ("A", "B", "C")
NOMBRES = {"A": "A · ganar", "B": "B · pelotear", "C": "C · precisión"}
COLORES = {"A": "#2a78d6", "B": "#eb6834", "C": "#1baf7a"}    # fijos: mismo color en todos los gráficos
TINTA, TINTA_2, GRILLA = "#0b0b0b", "#52514e", "#e4e3df"

# (clave en las métricas, título, ¿es un porcentaje?)
METRICAS = [
    ("ganados", "Puntos ganados al rival de referencia", True),
    ("peloteo", "Golpes válidos por punto", False),
    ("golpes_validos", "Golpes válidos (% de los propios)", True),
    ("profundidad", "Profundidad media de los botes (unidades)", False),
    ("ganadores", "Puntos ganados con un golpe ganador", True),
    ("errores", "Puntos perdidos por error propio", True),
    ("anulados", "Puntos anulados", True),
]


# --- Datos ---

def por_tratamiento(resumen):
    """{tratamiento: [rama, ...]} con las ramas de cada tratamiento."""
    grupos = {t: [] for t in TRATAMIENTOS}
    for rama in resumen:
        grupos[rama["tratamiento"]].append(rama)
    return {t: ramas for t, ramas in grupos.items() if ramas}


# Dos fuentes de métricas: "metricas" (el campeón, como dice el plan) y
# "metricas_poblacion" (promedio de los 10 mejores; complementaria, más estable).

def finales(ramas, clave, fuente="metricas"):
    """El valor final de una métrica en cada rama (una por semilla)."""
    return [rama[fuente][-1][clave] for rama in ramas]


def curva(ramas, clave, fuente="metricas"):
    """Generaciones medidas y, en cada una, (promedio, desviación) entre semillas."""
    generaciones = sorted({m["generacion"] for rama in ramas for m in rama[fuente]})
    promedios, desvios = [], []
    for g in generaciones:
        valores = [m[clave] for rama in ramas for m in rama[fuente] if m["generacion"] == g]
        promedios.append(statistics.mean(valores))
        desvios.append(statistics.pstdev(valores))
    return generaciones, promedios, desvios


def comparar(grupos, clave, fuente="metricas"):
    """Valor p de Mann-Whitney para cada par de tratamientos (None si hay menos de 2 semillas)."""
    pvalores = {}
    for a, b in itertools.combinations(grupos, 2):
        xa, xb = finales(grupos[a], clave, fuente), finales(grupos[b], clave, fuente)
        if len(xa) < 2 or len(xb) < 2 or len(set(xa + xb)) == 1:
            pvalores[(a, b)] = None
        else:
            pvalores[(a, b)] = mannwhitneyu(xa, xb, alternative="two-sided").pvalue
    return pvalores


# --- Gráficos ---

def _estilo(ax):
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(GRILLA)
    ax.tick_params(colors=TINTA_2, labelsize=8)
    ax.grid(axis="y", color=GRILLA, linewidth=0.8)


def _formato(valor, porcentaje):
    return f"{valor:.0%}" if porcentaje else f"{valor:.2f}"


def grafico_curvas(grupos, ruta, fuente="metricas"):
    fig, ejes = plt.subplots(2, 4, figsize=(14, 6.5), dpi=120)
    for ax, (clave, titulo, porcentaje) in zip(ejes.flat, METRICAS):
        for t, ramas in grupos.items():
            gens, prom, desv = curva(ramas, clave, fuente)
            ax.plot(gens, prom, color=COLORES[t], linewidth=2, label=NOMBRES[t])
            ax.fill_between(gens, [p - d for p, d in zip(prom, desv)],
                            [p + d for p, d in zip(prom, desv)], color=COLORES[t], alpha=0.15, linewidth=0)
        ax.set_title(titulo, fontsize=9, color=TINTA, loc="left")
        if porcentaje:
            ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
        ax.set_xlabel("generación de la etapa 3", fontsize=8, color=TINTA_2)
        _estilo(ax)
    ejes.flat[-1].axis("off")
    ejes.flat[0].legend(frameon=False, fontsize=8)
    quien = "del campeón" if fuente == "metricas" else "de los 10 mejores de la población"
    fig.suptitle(f"Métricas {quien} contra el rival de referencia (promedio ± desviación entre semillas)",
                 fontsize=11, color=TINTA, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def grafico_cajas(grupos, ruta):
    fig, ejes = plt.subplots(2, 4, figsize=(14, 6.5), dpi=120)
    for ax, (clave, titulo, porcentaje) in zip(ejes.flat, METRICAS):
        tratamientos = list(grupos)
        datos = [finales(grupos[t], clave) for t in tratamientos]
        cajas = ax.boxplot(datos, patch_artist=True, widths=0.55, medianprops={"color": TINTA})
        for caja, t in zip(cajas["boxes"], tratamientos):
            caja.set_facecolor(COLORES[t])
            caja.set_alpha(0.35)
            caja.set_edgecolor(COLORES[t])
        for k, (t, valores) in enumerate(zip(tratamientos, datos), start=1):
            ax.scatter([k] * len(valores), valores, color=COLORES[t], s=18, zorder=3)
        ax.set_xticks(range(1, len(tratamientos) + 1), [NOMBRES[t] for t in tratamientos], fontsize=8)
        ax.set_title(titulo, fontsize=9, color=TINTA, loc="left")
        if porcentaje:
            ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
        _estilo(ax)
    ejes.flat[-1].axis("off")
    fig.suptitle("Métricas finales por tratamiento (cada punto es una semilla)",
                 fontsize=11, color=TINTA, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def grafico_botes(grupos, ruta, columnas=24):
    """Mapa de calor: en qué parte del campo rival botan los tiros válidos de cada tratamiento."""
    ancho_campo = config.ANCHO_CANCHA - config.X_RED
    fig, ax = plt.subplots(figsize=(9, 0.9 + 0.7 * len(grupos)), dpi=130)
    filas = []
    for t, ramas in grupos.items():
        conteo = [0] * columnas
        botes = [b for rama in ramas for b in rama["metricas"][-1]["botes"]]
        for x in botes:
            distancia = abs(x - config.X_RED)
            conteo[min(columnas - 1, int(distancia / ancho_campo * columnas))] += 1
        total = sum(conteo) or 1
        filas.append([c / total for c in conteo])
    imagen = ax.imshow(filas, aspect="auto", cmap="Blues", extent=(0, ancho_campo, len(grupos) - 0.5, -0.5))
    ax.set_yticks(range(len(grupos)), [NOMBRES[t] for t in grupos], fontsize=9)
    ax.axvline(ancho_campo * 2 / 3, color=TINTA_2, linewidth=1, linestyle="--")
    ax.text(ancho_campo * 2 / 3 + 5, -0.6, "tercio profundo", fontsize=8, color=TINTA_2, va="bottom")
    ax.set_xlabel("distancia a la red del bote (de la red al fondo rival)", fontsize=9, color=TINTA_2)
    ax.set_title("Dónde botan los tiros válidos (fracción de los botes de cada tratamiento)",
                 fontsize=10, color=TINTA, loc="left")
    fig.colorbar(imagen, ax=ax, fraction=0.03, pad=0.02, format=matplotlib.ticker.PercentFormatter(1.0))
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


# --- Tabla ---

def tabla(grupos, fuente="metricas"):
    """Filas: métricas. Columnas: cada tratamiento (promedio ± desv.) y los valores p."""
    pares = list(itertools.combinations(grupos, 2))
    encabezado = ["Métrica"] + [NOMBRES[t] for t in grupos] + [f"p {a}–{b}" for a, b in pares]
    filas = []
    for clave, titulo, porcentaje in METRICAS:
        fila = [titulo]
        for t in grupos:
            v = finales(grupos[t], clave, fuente)
            fila.append(f"{_formato(statistics.mean(v), porcentaje)} ± {_formato(statistics.pstdev(v), porcentaje)}")
        pvalores = comparar(grupos, clave, fuente)
        fila += ["—" if pvalores[p] is None else f"{pvalores[p]:.3f}" for p in pares]
        filas.append(fila)
    return encabezado, filas


def guardar_tabla(encabezado, filas, carpeta, nombre="tabla"):
    import csv
    with open(os.path.join(carpeta, f"{nombre}.csv"), "w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(encabezado)
        escritor.writerows(filas)
    lineas = ["| " + " | ".join(encabezado) + " |", "|" + "---|" * len(encabezado)]
    lineas += ["| " + " | ".join(fila) + " |" for fila in filas]
    texto = "\n".join(lineas) + "\n"
    with open(os.path.join(carpeta, f"{nombre}.md"), "w", encoding="utf-8") as f:
        f.write(texto)
    return texto


def generar(carpeta_experimento):
    resumen = cargar_json(os.path.join(carpeta_experimento, "resumen.json"))
    grupos = por_tratamiento(resumen)
    salida = os.path.join(carpeta_experimento, "graficos")
    os.makedirs(salida, exist_ok=True)
    grafico_curvas(grupos, os.path.join(salida, "curvas.png"))
    grafico_cajas(grupos, os.path.join(salida, "cajas.png"))
    grafico_botes(grupos, os.path.join(salida, "mapa_botes.png"))
    texto = guardar_tabla(*tabla(grupos), salida)
    if all(rama.get("metricas_poblacion") for ramas in grupos.values() for rama in ramas):
        grafico_curvas(grupos, os.path.join(salida, "curvas_poblacion.png"), "metricas_poblacion")
        texto += "\nPoblación (10 mejores):\n" + guardar_tabla(
            *tabla(grupos, "metricas_poblacion"), salida, "tabla_poblacion")
    return salida, texto


def _principal():
    parser = argparse.ArgumentParser(description="Gráficos y estadística del experimento.")
    parser.add_argument("--carpeta", required=True, help="carpeta del experimento (con resumen.json)")
    salida, texto = generar(parser.parse_args().carpeta)
    print(texto)
    print(f"Gráficos en {salida}")


if __name__ == "__main__":
    _principal()
