# Capítulo 8 · Métricas, gráficos y estadística (D2 + F6)

> Etiqueta: `fase-5` · Archivos: `metricas.py`, `graficos.py`,
> `tests/test_metricas.py`, `tests/test_graficos.py`

## 8.1 Dónde estamos

Tenemos jugadores entrenados con tres aptitudes distintas. Ahora hay que
responder la pregunta del proyecto con **números**: ¿juegan distinto? ¿Cuánto?
¿Es una diferencia real o pudo ser suerte? Este capítulo explica cómo se mide,
cómo se grafica y cómo se decide si una diferencia "cuenta".

## 8.2 Teoría

### 8.2.1 Medir con una vara que no depende de lo que se mide

Cada rama se entrena con su propia aptitud, así que comparar aptitudes no
sirve: un 1,2 en la aptitud B (golpes válidos por punto) no se puede comparar
con un 0,3 en la aptitud A (diferencia de puntos). Hace falta **una misma vara
para todos**: la **batería de referencia** (sección 8 del plan).

- El campeón de cada rama juega **300 puntos** (el plan decía 100; ver el
  capítulo 5) contra el **rival programado**, siempre con los **mismos saques**
  (`metricas.SEMILLA_BATERIA`).
- De esos puntos salen seis métricas (`metricas.calcular`):

| Métrica | Qué mide | Qué esperan las hipótesis |
|---|---|---|
| 1. Puntos ganados | Qué tan bien juega "en serio" | A alto (H1), B bajo (H2) |
| 2. Golpes válidos por punto | Largo del peloteo | B alto (H2), A bajo (H1) |
| 3. % de golpes válidos | Seguridad: cuántos de sus golpes entran | B alto, C bajo (H3) |
| 4. Profundidad media | A qué distancia de la red botan sus tiros | C alto (H3) |
| 5. Ganadores / errores | Cómo terminan los puntos: tiros que el rival no alcanza o errores propios | A muchos ganadores; C muchos errores (H3) |
| 6. Anulados | Puntos que llegan al tiempo máximo | Si B "congela" la pelota, aparece aquí |

Y para el mapa de calor se guarda dónde botó **cada** tiro válido.

### 8.2.2 Las semillas son réplicas

Una corrida de evolución tiene mucho azar: la población inicial, las
mutaciones, los saques. Si la rama A gana más puntos que la B **en una sola
semilla**, puede ser casualidad de esa corrida. Por eso el experimento repite
todo con varias semillas (5 a 10): cada semilla es una **réplica**
independiente, como repetir un experimento de laboratorio.

Para cada métrica y cada tratamiento se informa:

- el **promedio** entre semillas;
- la **desviación estándar**: cuánto varían las semillas entre sí. Una
  desviación grande dice "el resultado depende mucho de la suerte de la
  corrida".

### 8.2.3 La prueba U de Mann-Whitney

¿Cómo decidir si la diferencia entre dos tratamientos es real? La idea de
Mann-Whitney es muy simple:

1. Se juntan los valores de los dos grupos (por ejemplo, los "puntos ganados"
   de las 5 semillas de A y las 5 de B) y se **ordenan** de menor a mayor.
2. Si los dos tratamientos fueran iguales, los de A y los de B quedarían
   **mezclados** en ese orden. Si A es mejor, los de A tienden a quedar arriba.
3. La prueba cuenta qué tan "separados" quedaron y calcula el **valor p**: la
   probabilidad de ver una separación así de grande **si en realidad no
   hubiera diferencia**.

Si p < 0,05, por convención se dice que la diferencia es **significativa**:
pasaría por pura casualidad menos de 1 de cada 20 veces.

¿Por qué esta prueba y no la más conocida, la *t de Student*? Porque Mann-Whitney
no supone que los datos tengan forma de campana (distribución normal), y con 5
semillas no hay forma de saber si la tienen. Solo usa el **orden** de los
valores. Es la que pide el plan.

### 8.2.4 Dos advertencias

**Con pocas semillas, no se puede llegar a p < 0,05.** Con 3 semillas por
tratamiento, el orden más extremo posible (las 3 de A arriba de las 3 de B)
tiene un valor p de 0,10: **nunca** será significativo, por grande que sea la
diferencia. Con 5 semillas, el mínimo es 0,008. Por eso el plan pide 10
semillas y como mínimo 5.

**Muchas pruebas, algún falso positivo.** Comparamos 7 métricas en 3 pares de
tratamientos: 21 pruebas. Si en realidad no hubiera ninguna diferencia, con
p < 0,05 esperaríamos igual **una** "significativa" por casualidad (21 × 0,05 ≈ 1).
Hay que mirar el conjunto: si las diferencias apuntan en la dirección que
predicen las hipótesis y se repiten en varias métricas, son creíbles; una
sola p = 0,04 aislada, no tanto. (La corrección de Bonferroni-Holm hace esto
de forma sistemática; se menciona en "Para estudiar más".)

### 8.2.5 Los gráficos

`graficos.py` genera cuatro cosas, con **un color fijo por tratamiento** en
todos los gráficos (A azul, B naranja, C verde agua):

| Archivo | Qué muestra | Para qué |
|---|---|---|
| `curvas.png` | Cada métrica del campeón cada 10 generaciones: línea = promedio entre semillas, sombra = ± desviación | Ver **cómo** se separan los tratamientos con el tiempo |
| `cajas.png` | Diagramas de caja de las métricas finales; cada punto es una semilla | Ver la diferencia final **y** cuánto varían las semillas |
| `mapa_botes.png` | Dónde botan los tiros válidos de cada tratamiento, de la red al fondo | La imagen para el banner: ¿C tira más al fondo? |
| `tabla.md` / `tabla.csv` | Promedio ± desviación y valores p | La tabla del resumen y del banner |

Un **diagrama de caja** resume un conjunto de números: la línea del medio es
la mediana (la mitad de las semillas está por encima), la caja va del primer
al tercer cuartil (la mitad central de los datos) y los "bigotes" llegan a los
valores extremos. Con solo 5 semillas, además, dibujamos cada semilla como un
punto: con tan pocos datos, conviene verlos todos.

## 8.3 Cómo está construido

| Función | Qué hace |
|---|---|
| `metricas.jugar_bateria(controlador)` | 300 puntos contra el rival de referencia, saques fijos |
| `metricas.calcular(eventos)` | Las métricas de la sección 8, solo con los eventos |
| `metricas.medir(controlador)` | Las dos cosas juntas; la usa la etapa 3 cada 10 generaciones |
| `graficos.por_tratamiento(resumen)` | Agrupa las ramas por tratamiento |
| `graficos.comparar(grupos, métrica)` | Valores p de Mann-Whitney para cada par (o "—" si hay menos de 2 semillas) |
| `graficos.generar(carpeta)` | Todo: gráficos y tabla en `carpeta/graficos/` |

`tests/test_graficos.py` prueba todo con un experimento **inventado**
(valores conocidos), así se puede desarrollar el análisis sin esperar las
corridas largas: es lo que el plan llama D2, "probado con datos de corridas
cortas".

## 8.4 Pruébalo tú

```bash
python graficos.py --carpeta resultados/ejemplo        # después del capítulo 7
pytest tests/test_metricas.py tests/test_graficos.py -v
python -c "from scipy.stats import mannwhitneyu; print(mannwhitneyu([1,2,3],[4,5,6]).pvalue)"
```

El último comando muestra la advertencia de 8.2.4: con 3 contra 3, aun con
los grupos totalmente separados, p = 0,10.

Experimentos:

1. En `tests/test_graficos.py`, cambia los niveles de A y B a 0,5 y 0,45: ¿la
   prueba sigue encontrando la diferencia con 5 semillas?
2. Abre `tabla.csv` en una hoja de cálculo y arma tu propio gráfico.

## 8.5 Resultados del experimento de ejemplo

Estas son las tablas que generó `graficos.py` para el experimento de ejemplo
del capítulo 7 (3 semillas, 60 generaciones). **Son de muestra**: sirven para
aprender a leerlas, no para sacar las conclusiones del proyecto.

Campeón de cada rama (la medida del plan):

| Métrica | A · ganar | B · pelotear | C · precisión | p A–B | p A–C | p B–C |
|---|---|---|---|---|---|---|
| Puntos ganados al rival de referencia | 11% ± 6% | 17% ± 5% | 15% ± 6% | 0.200 | 0.507 | 1.000 |
| Golpes válidos por punto | 0.92 ± 0.34 | 2.96 ± 1.07 | 1.71 ± 0.92 | 0.100 | 0.700 | 0.400 |
| Golpes válidos (% de los propios) | 41% ± 2% | 13% ± 3% | 34% ± 17% | 0.100 | 0.700 | 0.400 |
| Profundidad media de los botes (unidades) | 310.14 ± 61.17 | 278.15 ± 71.83 | 325.79 ± 47.53 | 0.700 | 0.700 | 0.400 |
| Puntos ganados con un golpe ganador | 4% ± 5% | 7% ± 5% | 6% ± 7% | 0.507 | 0.376 | 1.000 |
| Puntos perdidos por error propio | 21% ± 19% | 11% ± 3% | 18% ± 13% | 1.000 | 1.000 | 1.000 |
| Puntos anulados | 0% ± 0% | 5% ± 3% | 2% ± 3% | 0.077 | 1.000 | 0.376 |

Los 10 mejores de cada población (la medida complementaria):

| Métrica | A · ganar | B · pelotear | C · precisión | p A–B | p A–C | p B–C |
|---|---|---|---|---|---|---|
| Puntos ganados al rival de referencia | 14% ± 5% | 18% ± 2% | 14% ± 5% | 0.700 | 1.000 | 0.700 |
| Golpes válidos por punto | 0.91 ± 0.07 | 2.22 ± 0.51 | 1.59 ± 0.42 | 0.100 | 0.100 | 0.400 |
| Golpes válidos (% de los propios) | 42% ± 7% | 19% ± 4% | 24% ± 3% | 0.100 | 0.100 | 0.400 |
| Profundidad media de los botes (unidades) | 315.65 ± 66.40 | 302.68 ± 37.99 | 332.12 ± 44.22 | 1.000 | 1.000 | 0.400 |
| Puntos ganados con un golpe ganador | 5% ± 5% | 7% ± 3% | 5% ± 5% | 0.700 | 1.000 | 0.700 |
| Puntos perdidos por error propio | 21% ± 8% | 14% ± 2% | 18% ± 8% | 0.400 | 0.700 | 0.700 |
| Puntos anulados | 0% ± 0% | 3% ± 2% | 2% ± 1% | 0.100 | 0.100 | 0.400 |

Cómo leerlas:

- **El mejor valor p posible con 3 semillas es 0,100**, y aparece varias veces:
  por ejemplo, "golpes válidos por punto" entre A y B en las dos tablas. Eso
  quiere decir que las 3 semillas de B quedaron **todas** por encima de las 3
  de A. Es lo más fuerte que pueden decir 3 semillas, y aun así no llega a 0,05.
  Con 5 semillas y la misma separación daría 0,008.
- **La tabla de la población es más "limpia"** que la del campeón: las
  desviaciones son más chicas (por ejemplo, golpes válidos por punto de A:
  0,91 ± 0,07 en la población contra 0,92 ± 0,34 en el campeón). Por eso la
  agregamos.
- Las diferencias que se repiten en las dos tablas y van en la dirección de
  las hipótesis (B pelotea más que A) son las candidatas a confirmarse en el
  experimento completo. Las que aparecen en una sola tabla, no tanto.


## 8.6 Para estudiar más

- Prueba U de Mann-Whitney, explicada paso a paso:
  https://es.wikipedia.org/wiki/Prueba_U_de_Mann-Whitney
- El valor p y cómo NO interpretarlo: American Statistical Association,
  "Statement on p-Values", 2016 — https://doi.org/10.1080/00031305.2016.1154108
- Comparaciones múltiples y la corrección de Holm:
  https://es.wikipedia.org/wiki/M%C3%A9todo_de_Holm%E2%80%93Bonferroni
- Diagramas de caja: https://es.wikipedia.org/wiki/Diagrama_de_caja
- `scipy.stats.mannwhitneyu` —
  https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.mannwhitneyu.html
