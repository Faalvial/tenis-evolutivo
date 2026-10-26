"""
ejercicios/seguir_punto.py — F2a: neuroevolución de juguete, sin física.

Un "bicho" (un punto) vive en un plano y tiene que perseguir a un objetivo que
se mueve. Lo controla una red neuronal pequeña: le entran la dirección hacia
el objetivo y su propia velocidad, y le salen dos números, la aceleración
en x y en y. Nadie le dice cómo perseguir: un algoritmo genético prueba
muchas redes y se queda con las que persiguen mejor.

Es el capítulo 3 del libro (docs/libro/cap03_red_neuronal.md) hecho código.
Todo está en este archivo, para leerlo de arriba abajo:
  1. la red neuronal (neurona -> capa -> red);
  2. el mundo del bicho y la aptitud;
  3. una red escrita A MANO (para entender qué significan los pesos);
  4. el algoritmo genético que encuentra los pesos solo.

Uso:
    python ejercicios/seguir_punto.py                 entrena y muestra el progreso
    python ejercicios/seguir_punto.py --semilla 7 --generaciones 60

Los parámetros están al principio de este archivo y no en config.py porque
no son del experimento de tenis: es un ejercicio para aprender.
"""

import argparse
import math
import random

# --- La red ---
ENTRADAS = 4        # dx, dy (hacia el objetivo) y vx, vy (velocidad propia)
OCULTAS = 4         # neuronas de la capa oculta
SALIDAS = 2         # aceleración en x y en y

# --- El mundo del bicho ---
PASOS = 200             # pasos por episodio
DT = 0.05               # segundos por paso (un episodio dura 10 s)
ACELERACION_MAX = 8.0   # unidades/s² con salida = 1
ROZAMIENTO = 0.9        # cada paso la velocidad se multiplica por esto (frena solo)
ESCALA_DISTANCIA = 5.0  # una distancia de 5 se ve como 1 en la entrada
ESCALA_VELOCIDAD = 5.0
AMPLITUD_OBJETIVO = 4.0  # el objetivo se mueve dentro de un cuadrado de ±4
VELOCIDAD_OBJETIVO = (0.3, 0.8)   # rango de frecuencias (vueltas por segundo ÷ 2π)
EPISODIOS = 2           # episodios por evaluación (con distintos movimientos del objetivo)

# --- El algoritmo genético ---
POBLACION = 40
GENERACIONES = 40
TORNEO = 3          # en cada torneo compiten 3 al azar; gana el de mejor aptitud
ELITE = 2           # los 2 mejores pasan sin cambios a la siguiente generación
SIGMA = 0.3         # tamaño típico de una mutación
LIMITE_PESO = 5.0   # los pesos se recortan a ±5


# =====================================================================
# 1. La red neuronal
# =====================================================================

def neurona(pesos, sesgo, entradas):
    """
    Una neurona artificial: multiplica cada entrada por su peso, suma todo,
    le suma el sesgo y "aplasta" el resultado con tanh, que lo deja entre -1 y 1.

        salida = tanh(w1·x1 + w2·x2 + ... + sesgo)
    """
    suma = sesgo
    for w, x in zip(pesos, entradas):
        suma += w * x
    return math.tanh(suma)


def capa(genoma, inicio, n_entradas, n_neuronas, entradas):
    """
    Una capa: varias neuronas que reciben LAS MISMAS entradas, cada una con sus
    propios pesos. En el genoma, cada neurona ocupa n_entradas pesos + 1 sesgo,
    uno detrás de otro. Devuelve (salidas, posición donde termina la capa).
    """
    salidas = []
    i = inicio
    for _ in range(n_neuronas):
        pesos = genoma[i:i + n_entradas]
        sesgo = genoma[i + n_entradas]
        salidas.append(neurona(pesos, sesgo, entradas))
        i += n_entradas + 1
    return salidas, i


def propagar(genoma, entradas):
    """
    PROPAGACIÓN HACIA ADELANTE: las entradas pasan por la capa oculta y lo que
    sale de ella pasa por la capa de salida. Toda la "inteligencia" está en los
    números del genoma.
    """
    ocultas, i = capa(genoma, 0, ENTRADAS, OCULTAS, entradas)
    salidas, _ = capa(genoma, i, OCULTAS, SALIDAS, ocultas)
    return salidas


def tamano_genoma():
    """Cuántos números tiene una red: pesos y sesgos de las dos capas."""
    return OCULTAS * (ENTRADAS + 1) + SALIDAS * (OCULTAS + 1)


# =====================================================================
# 2. El mundo del bicho y la aptitud
# =====================================================================

def movimiento_objetivo(azar):
    """
    El objetivo recorre una curva de Lissajous: x e y oscilan con frecuencias
    distintas, y dibujan figuras como un ocho o un lazo. Se eligen al azar.
    """
    return {"fx": azar.uniform(*VELOCIDAD_OBJETIVO), "fy": azar.uniform(*VELOCIDAD_OBJETIVO),
            "fase": azar.uniform(0, 2 * math.pi)}


def posicion_objetivo(mov, t):
    return (AMPLITUD_OBJETIVO * math.sin(mov["fx"] * t + mov["fase"]),
            AMPLITUD_OBJETIVO * math.sin(mov["fy"] * t))


def limitar(valor, minimo=-1.0, maximo=1.0):
    return max(minimo, min(maximo, valor))


def percibir(bicho, objetivo):
    """Las 4 entradas de la red, normalizadas para quedar más o menos en [-1, 1]."""
    (x, y, vx, vy), (ox, oy) = bicho, objetivo
    return [limitar((ox - x) / ESCALA_DISTANCIA), limitar((oy - y) / ESCALA_DISTANCIA),
            limitar(vx / ESCALA_VELOCIDAD), limitar(vy / ESCALA_VELOCIDAD)]


def simular(genoma, mov, guardar_recorrido=False):
    """
    Un episodio. Devuelve la distancia promedio al objetivo (y, si se pide, el
    recorrido del bicho y del objetivo, para dibujarlos).
    La física es mínima: la red elige una aceleración, la velocidad cambia con
    ella y con el rozamiento, y la posición cambia con la velocidad.
    """
    x = y = vx = vy = 0.0
    distancia_total = 0.0
    recorrido = []
    for paso in range(PASOS):
        t = paso * DT
        objetivo = posicion_objetivo(mov, t)
        ax, ay = propagar(genoma, percibir((x, y, vx, vy), objetivo))
        vx = vx * ROZAMIENTO + ax * ACELERACION_MAX * DT
        vy = vy * ROZAMIENTO + ay * ACELERACION_MAX * DT
        x += vx * DT
        y += vy * DT
        distancia_total += math.hypot(objetivo[0] - x, objetivo[1] - y)
        if guardar_recorrido:
            recorrido.append(((x, y), objetivo))
    promedio = distancia_total / PASOS
    return (promedio, recorrido) if guardar_recorrido else promedio


def aptitud(genoma, movimientos):
    """
    APTITUD (fitness): un número que dice qué tan bien lo hace una red. Aquí,
    menos la distancia promedio al objetivo: cuanto más cerca, más alta.
    Todos los individuos de una generación se evalúan con los MISMOS
    movimientos del objetivo, para que la comparación sea justa.
    """
    return -sum(simular(genoma, mov) for mov in movimientos) / len(movimientos)


# =====================================================================
# 3. Una red escrita a mano
# =====================================================================

def red_a_mano():
    """
    Pesos elegidos por nosotros, para entender qué significan:
      - oculta 0 copia dx y oculta 1 copia dy (peso 3: "sé sensible a la distancia");
      - oculta 2 copia vx y oculta 3 copia vy (peso 1);
      - salida x = acelerar hacia dx y FRENAR según vx (peso negativo);
      - salida y = lo mismo para y.
    Es un control "proporcional + amortiguado", como el motor de la raqueta
    del capítulo 1 pero con un freno. Ningún sesgo: si ya estás en el
    objetivo y quieto, no hagas nada.
    """
    ocultas = [
        [3.0, 0.0, 0.0, 0.0, 0.0],    # oculta 0: pesos de (dx, dy, vx, vy) y sesgo
        [0.0, 3.0, 0.0, 0.0, 0.0],    # oculta 1
        [0.0, 0.0, 1.0, 0.0, 0.0],    # oculta 2
        [0.0, 0.0, 0.0, 1.0, 0.0],    # oculta 3
    ]
    salidas = [
        [2.0, 0.0, -1.0, 0.0, 0.0],   # salida x: pesos de (oculta 0..3) y sesgo
        [0.0, 2.0, 0.0, -1.0, 0.0],   # salida y
    ]
    return [w for neurona_ in ocultas + salidas for w in neurona_]


# =====================================================================
# 4. El algoritmo genético
# =====================================================================

def genoma_al_azar(azar):
    return [azar.gauss(0.0, 1.0) for _ in range(tamano_genoma())]


def torneo(poblacion, aptitudes, azar):
    """SELECCIÓN POR TORNEO: se eligen TORNEO individuos al azar y gana el mejor."""
    elegidos = azar.sample(range(len(poblacion)), TORNEO)
    ganador = max(elegidos, key=lambda i: aptitudes[i])
    return poblacion[ganador]


def mutar(genoma, azar):
    """MUTACIÓN: a cada peso se le suma un pequeño número al azar (gaussiano)."""
    return [limitar(w + azar.gauss(0.0, SIGMA), -LIMITE_PESO, LIMITE_PESO) for w in genoma]


def siguiente_generacion(poblacion, aptitudes, azar):
    """
    ELITISMO: los ELITE mejores pasan tal cual (así nunca se pierde lo mejor).
    El resto: hijos de ganadores de torneo, con mutación.
    (En F2b se agrega el CRUCE, que mezcla dos padres.)
    """
    orden = sorted(range(len(poblacion)), key=lambda i: aptitudes[i], reverse=True)
    nueva = [poblacion[i] for i in orden[:ELITE]]
    while len(nueva) < len(poblacion):
        nueva.append(mutar(torneo(poblacion, aptitudes, azar), azar))
    return nueva


def evolucionar(semilla, generaciones=GENERACIONES, al_terminar_generacion=None):
    """
    El bucle de la evolución:
      población al azar -> evaluar -> seleccionar + mutar -> evaluar -> ...
    Devuelve el historial [(mejor, promedio), ...] y el mejor genoma de cada
    generación (para comparar el principio con el final).
    """
    azar = random.Random(semilla)
    poblacion = [genoma_al_azar(azar) for _ in range(POBLACION)]
    historial, campeones = [], []
    for gen in range(generaciones):
        # El objetivo se mueve distinto en cada generación: así no se memoriza un recorrido.
        movimientos = [movimiento_objetivo(azar) for _ in range(EPISODIOS)]
        aptitudes = [aptitud(g, movimientos) for g in poblacion]
        mejor = max(range(POBLACION), key=lambda i: aptitudes[i])
        historial.append((aptitudes[mejor], sum(aptitudes) / POBLACION))
        campeones.append(poblacion[mejor])
        if al_terminar_generacion:
            al_terminar_generacion(gen, aptitudes[mejor], historial[-1][1])
        poblacion = siguiente_generacion(poblacion, aptitudes, azar)
    return historial, campeones


def comparar(genoma, semilla=12345, episodios=20):
    """Distancia promedio en episodios NUEVOS (que nunca vio al entrenar)."""
    azar = random.Random(semilla)
    movimientos = [movimiento_objetivo(azar) for _ in range(episodios)]
    return -aptitud(genoma, movimientos)


def _principal():
    parser = argparse.ArgumentParser(description="Neuroevolución de juguete: seguir un punto.")
    parser.add_argument("--semilla", type=int, default=1)
    parser.add_argument("--generaciones", type=int, default=GENERACIONES)
    args = parser.parse_args()

    print(f"Red de {ENTRADAS} entradas, {OCULTAS} ocultas y {SALIDAS} salidas: "
          f"{tamano_genoma()} números en el genoma.\n")
    print("generación   mejor distancia   distancia promedio")

    def mostrar(gen, mejor, promedio):
        if gen % 5 == 0 or gen == args.generaciones - 1:
            print(f"{gen:9d}   {-mejor:15.2f}   {-promedio:18.2f}")

    historial, campeones = evolucionar(args.semilla, args.generaciones, mostrar)
    azar = random.Random(0)
    print("\nDistancia promedio en 20 recorridos nuevos (más chica = mejor):")
    print(f"  red al azar          {comparar(genoma_al_azar(azar)):5.2f}")
    print(f"  campeón generación 0 {comparar(campeones[0]):5.2f}")
    print(f"  campeón final        {comparar(campeones[-1]):5.2f}")
    print(f"  red escrita a mano   {comparar(red_a_mano()):5.2f}")


if __name__ == "__main__":
    _principal()
