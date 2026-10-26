# Capítulo 7 · El experimento (F5)

> Etiqueta: `fase-5` · Archivos: `experimentos.py`, `graficos.py`

## 7.1 Dónde estamos

Todas las piezas están: el juego (capítulo 1), el currículo (4 y 5), las tres
ramas (6) y el análisis (8). El experimento es correrlas **con varias
semillas**, guardar todo y analizar.

Este capítulo tiene dos partes:

1. **Cómo correr el experimento completo** en la laptop del equipo (10
   semillas × 3 tratamientos × 200 generaciones).
2. **Un experimento de ejemplo** que corrimos aquí, más chico, para probar que
   todo funciona de punta a punta y tener gráficos de muestra. **No es el
   resultado del proyecto**: tiene pocas semillas y pocas generaciones.

## 7.2 El diseño, en una tabla

| | Valor | Dónde |
|---|---|---|
| Variable independiente | La aptitud de la etapa 3: A, B o C | `aptitud.APTITUDES` |
| Réplicas | 10 semillas (mínimo 5) | `--semillas` |
| Variables controladas | Física, reglas, red, algoritmo genético, etapas 1 y 2, semillas | `config.py` (no se toca durante el experimento) |
| Variables dependientes | Las métricas de la batería de referencia | `metricas.py` |
| Control clave | Las tres ramas de una semilla parten de la **misma** población base | `experimentos.py` |
| Generaciones de la etapa 3 | 200 | `config.ETAPA3_GENERACIONES` |
| Análisis | Promedio ± desviación, Mann-Whitney entre pares | `graficos.py` |

## 7.3 Cómo correr el experimento completo

### Antes de empezar

1. `git pull` y `pytest`: todas las pruebas deben pasar.
2. **No cambiar `config.py`** durante el experimento. Si hace falta cambiar
   algo, se empieza de nuevo en otra carpeta.
3. Cerrar programas pesados (navegador, juegos) y conectar la laptop al
   cargador, en modo de máximo rendimiento (plan, sección 11).

### El comando

```bash
python experimentos.py --carpeta resultados/experimento --semillas 1 2 3 4 5 6 7 8 9 10
```

Usa todos los núcleos (`--procesos` por defecto). Va imprimiendo cada
generación. **Se puede cortar en cualquier momento** (Ctrl+C, apagar la
computadora): al volver a correr el mismo comando sigue donde quedó, y el
resultado es el mismo que sin cortes (capítulo 4).

### Repartir entre dos laptops

Cada laptop corre semillas distintas **en carpetas con el mismo nombre**:

```bash
# laptop 1
python experimentos.py --carpeta resultados/experimento --semillas 1 2 3 4 5
# laptop 2 (la gamer)
python experimentos.py --carpeta resultados/experimento --semillas 6 7 8 9 10
```

Después se copian las carpetas `semilla_6` ... `semilla_10` de la laptop 2
dentro de `resultados/experimento` de la laptop 1 (por la carpeta en la nube),
y se rearma el resumen y los gráficos:

```bash
python -c "import experimentos; experimentos.resumir('resultados/experimento')"
python graficos.py --carpeta resultados/experimento
```

### ¿Cuánto tarda?

TIEMPOS_F5

## 7.4 Qué mirar mientras corre

- La columna **anulados** de la rama B: si sube mucho, puede ser la trampa de
  "congelar" la pelota.
- La columna **promedio** de la rama C: si se acerca a −1, la población está
  dejando de devolver (la trampa del capítulo 6, que ahora se castiga).
- Cada 10 generaciones se guardan las métricas del campeón en
  `estado.json` (`"metricas"`): `graficos.py` las usa para las curvas.

RESULTADOS_F5

## 7.7 Para estudiar más

- Diseño de experimentos y réplicas: https://es.wikipedia.org/wiki/Dise%C3%B1o_experimental
- Reproducibilidad en experimentos con computadora: Sandve et al., "Ten
  Simple Rules for Reproducible Computational Research", *PLoS Comput Biol*,
  2013 — https://doi.org/10.1371/journal.pcbi.1003285
