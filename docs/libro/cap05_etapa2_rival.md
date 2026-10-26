# Capítulo 5 · Etapa 2: contra el rival programado (F3)

> Etiqueta: `fase-3` · Archivos: `entrenar.py` (ahora con varias etapas),
> `aptitud.py` (`aptitud_etapa2`), `metricas.py`, `config.py` (etapa 2)

## 5.1 Dónde estamos

Después de la etapa 1, el jugador sabe devolver pelotas cómodas de una
máquina que no le devuelve nada. Jugar es otra cosa: el rival devuelve, a
veces con tiros difíciles, y hay que **ganar puntos**. La etapa 2 enfrenta a
la misma población con el rival programado del capítulo 1.

Este capítulo trata también de un problema que no tiene nada que ver con el
tenis y que aparece en cualquier experimento: **cómo saber si un resultado es
real o fue suerte**.

## 5.2 Teoría

### 5.2.1 La aptitud de la etapa 2

Según el plan (sección 6), por cada punto jugado:

```
aptitud = (puntos ganados + 0,2 × devoluciones válidas) / puntos jugados
```

¿Por qué el `0,2 × devoluciones`? Es otra vez el **problema del arranque**
(capítulo 4). Al principio casi nadie le gana un punto al rival programado, así
que si la aptitud fuera solo "puntos ganados", casi todos tendrían 0. El premio
chico por cada devolución válida permite distinguir al que sostiene el
peloteo del que falla enseguida, aunque los dos pierdan. Es chico (0,2) para que
ganar un punto siga valiendo mucho más que devolver.

### 5.2.2 Un currículo: la población pasa de una etapa a la otra

`entrenar.py` ahora recorre las etapas en orden. Cuando una termina, la **misma
población** sigue en la siguiente (`pasar_a_la_siguiente_etapa`). No se
empieza de cero: lo aprendido en la etapa 1 (tocar y devolver) es la base de
la etapa 2 (ganar). Al terminar la etapa 2 se guarda `poblacion_base.json`, el
punto de partida de los tres tratamientos (capítulo 6).

### 5.2.3 La maldición del ganador

Imagina 60 personas que tiran 10 monedas cada una, y elegimos a la que sacó
más caras: seguramente sacó 8 o 9. ¿Es una "tiradora de caras" excepcional?
No: si le pedimos que tire otras 10, sacará unas 5, como cualquiera. **Al
elegir al mejor de muchos según un resultado con ruido, elegimos también al de
más suerte**, y su resultado está inflado. Se llama la **maldición del
ganador**.

Nos pasó exactamente esto (sección 5.4): cada 5 generaciones elegíamos al
campeón según una batería de prueba, y el que la pasaba era, en parte, el que
había tenido suerte con *esa* batería.

La solución es la misma que usa el aprendizaje automático:

- una batería para **elegir** (la de prueba);
- otra batería, que no se usó para elegir, para **confirmar** (la de
  validación).

Solo si el campeón cumple la meta **en las dos**, la etapa termina. Su
resultado en la batería de validación no está inflado, porque no se lo eligió
por ella.

### 5.2.4 ¿Cuánto ruido tiene un porcentaje?

Si un jugador gana de verdad el 40 % de los puntos, ¿cuánto puede dar una
batería de 100 puntos? La estadística responde con el **error estándar** de una
proporción:

```
error estándar = √( p · (1 − p) / n ) = √( 0,4 · 0,6 / 100 ) ≈ 0,05
```

O sea, ±5 puntos porcentuales "normales". Una batería puede dar 35 % o 45 %
solo por suerte, y de vez en cuando (1 de cada 20) más lejos todavía. Para
reducir el error a la mitad hay que jugar **cuatro veces** más puntos (por la
raíz cuadrada). Lo vamos a necesitar en el análisis (capítulo 8).

## 5.3 Cómo está construido

| Pieza | Qué hace |
|---|---|
| `entrenar.Etapa` | Describe una etapa: cómo se evalúa, cuántos puntos, la meta, el máximo de generaciones |
| `entrenar.entrenar` | Recorre las etapas en orden; `--hasta-etapa` dice hasta dónde |
| `entrenar.elegir_campeon` | Prueba a los 5 mejores de la generación con la batería de prueba y elige al mejor |
| `SEMILLA_VALIDACION` | La batería de validación: confirma la meta antes de terminar la etapa |
| `aptitud.aptitud_etapa2` | Puntos ganados + 0,2 × devoluciones válidas, por punto |
| `metricas.py` | La batería de referencia de la sección 8 (100 puntos fijos contra el rival programado) y las 6 métricas |

El historial (`historial.csv`) tiene ahora una columna `validacion` y otra
`etapa`. Los estados guardados con la versión del capítulo 4 se actualizan
solos al cargarlos (`_actualizar_formato`).

## 5.4 Diario de decisiones

### a) La primera etapa 2 "cumplió", pero no

La primera corrida terminó la etapa 2 en 36 generaciones con un campeón que
ganaba el **42 %** de la batería de prueba. Al medirlo con la batería de
referencia de las métricas (100 puntos que nunca vio) ganaba solo el **26 %**.
Era la maldición del ganador de 5.2.3.

### b) Validación y candidatos

Hicimos dos cambios, en las dos etapas:

1. **Validación:** si el campeón cumple la meta en la prueba, se lo confirma
   con una batería independiente.
2. **Cinco candidatos:** con solo 8 pelotas (o puntos) por evaluación, el
   "mejor de la generación" muchas veces es el de más suerte. Ahora se prueba a
   los 5 mejores y se elige al que mejor hace la prueba.

### c) Con la regla nueva, la etapa 1 tarda más

Con la validación, la etapa 1 de la semilla 1 ya no terminó en la generación
36: en la 35 el campeón hizo 60 % en la prueba pero 57 % en la validación, así
que siguió. Terminó en la generación **150** con 60 % en las dos. La primera
corrida (capítulo 4) había pasado la meta con un poco de suerte; el campeón
nuevo la pasa de verdad.

### d) La batería de referencia también tiene ruido

El campeón de la etapa 2 (ver 5.5) ganó el 41 % en la prueba y el 42 % en la
validación, pero solo el 29 % en la batería de referencia. ¿Otra vez la
maldición? No: lo medimos en **10 baterías nuevas** de 100 puntos y dio
40 % ± 4 %. La batería de referencia simplemente le tocó difícil: 29 % está a
unos 2 errores estándar del 40 %, algo que pasa 1 de cada 20 veces.

Lección para el experimento: con 100 puntos, la métrica "% de puntos ganados"
tiene ±5 puntos de ruido. Como todos los tratamientos se miden con la misma
batería, la comparación entre ellos es justa, pero las diferencias chicas
pueden ser ruido. **Recomendación para el equipo** (no lo cambiamos porque las
métricas son parte del diseño experimental): subir la batería a 300 puntos
(`metricas.PUNTOS_BATERIA`), que baja el ruido a ±3 puntos y cuesta menos de
un segundo por medición.

## 5.5 Resultados (semilla 1)

```
$ python entrenar.py --carpeta resultados/curriculo_s1 --semilla 1 --procesos 4
...
Etapa 1 terminada en la generación 150: el campeón logra 60% (devueltas) en la prueba y 60% en la validación.

Etapa 2 (rival programado)
gen    mejor  promedio  ganados(mejor)  prueba campeón  validación  segundos
  0    0.750     0.159           62%             20%                   3.6
  5    0.525     0.174           38%             29%                   4.3
 10    0.425     0.173           38%             22%                   5.0
 15    ...                                      41%         42%
Etapa 2 terminada en la generación 16: el campeón logra 41% (ganados) en la prueba y 42% en la validación.
```

La etapa 2 fue **rápida** (16 generaciones, unos 40 segundos): la población ya
sabía devolver, y solo tuvo que aprender a ganar.

Métricas en la batería de referencia (100 puntos, sección 8):

| Métrica | Campeón etapa 1 | Campeón etapa 2 | Rival programado |
|---|---|---|---|
| Puntos ganados | 13 % | 29 % (40 % en 10 baterías) | 44 % |
| Golpes válidos por punto | 0,55 | 1,17 | 4,39 |
| Golpes válidos (% de los propios) | 27 % | 55 % | 82 % |
| Profundidad de los botes | 452 | 380 | 300 |
| Puntos ganados con un golpe ganador | 3 % | **18 %** | 4 % |
| Puntos perdidos por error propio | 22 % | 35 % | 40 % |

¿Cómo juega el campeón de la etapa 2? Peloteos cortos (1,2 golpes válidos por
punto), muchos **golpes ganadores** (18 % de los puntos, el rival programado
solo 4 %) y muchos errores (35 %). Tira **profundo** (380, frente a 300 del rival)
y arriesga. Ganar puntos contra este rival se consigue así: tiros al fondo,
que el rival programado, con su error de posición, no alcanza a devolver.
Nadie le enseñó esta estrategia; la encontró la evolución, y es justo lo que
la hipótesis H1 predice para el tratamiento A (capítulo 6): agresividad.

## 5.6 Pruébalo tú

```bash
git checkout fase-3
python entrenar.py --carpeta resultados/mi_curriculo --semilla 1          # etapas 1 y 2
python entrenar.py --carpeta resultados/mi_curriculo --grabar-campeon
python ver2d.py resultados/mi_curriculo/campeon_etapa2.json
python jugar.py --campeon resultados/mi_curriculo                        # ¡jugarle tú!
python -c "import metricas, red, guardado; e = guardado.cargar_json('resultados/mi_curriculo/estado.json'); print(metricas.medir(red.ControladorRed(e['campeones']['2'])))"
```

Experimentos:

1. **La maldición, en vivo.** En `config.py`, pon `CANDIDATOS_PRUEBA = 20` y
   mira la columna "prueba campeón": ¿sube? ¿Y la "validación"?
2. **Sin el premio por devolver.** `PESO_DEVOLUCIONES = 0`: ¿cuánto tarda en
   arrancar la etapa 2?
3. **El ruido de un porcentaje.** Mide al mismo campeón con 10 semillas de
   batería distintas (como en 5.4 d) y con 300 puntos en vez de 100: ¿cuánto
   cambia la desviación?

## 5.7 Criterios de aceptación

| Criterio del plan | Resultado |
|---|---|
| El campeón gana ≥ 40 % de los puntos contra el rival programado | 41 % en la prueba, 42 % en la validación, 40 % ± 4 % en 10 baterías nuevas (semilla 1, generación 16) |
| (Y la etapa 1, con la regla nueva) | 60 % de devoluciones en la prueba y en la validación (generación 150) |

## 5.8 Puente al capítulo 6

Ya tenemos la **población base**: jugadores que devuelven y le ganan puntos
al rival programado. Ahora viene el experimento de verdad. De esa misma
población salen tres ramas, y cada una evoluciona **contra sí misma** (IA contra
IA) con una aptitud distinta: ganar (A), pelotear (B) o precisión (C). La
pregunta del proyecto es si eso basta para que aparezcan estilos de juego
distintos.

## 5.9 Para estudiar más

- La maldición del ganador: https://es.wikipedia.org/wiki/Maldici%C3%B3n_del_ganador
- Entrenamiento, validación y prueba en aprendizaje automático: *Google Machine
  Learning Crash Course*, "Training and Test Sets" —
  https://developers.google.com/machine-learning/crash-course/overfitting
- Error estándar de una proporción: https://es.wikipedia.org/wiki/Error_est%C3%A1ndar
- Currículos de entrenamiento: Y. Bengio et al., "Curriculum Learning", ICML 2009 —
  https://dl.acm.org/doi/10.1145/1553374.1553380
