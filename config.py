"""
config.py — Todos los parámetros del proyecto en un solo lugar.

Regla del equipo: nunca escribir números "mágicos" dentro del código; si un
valor puede cambiar, va aquí con un comentario que diga qué significa.

Los valores de física y reglas se CALIBRARON en la fase F1 (el porqué de
cada cambio está en docs/libro/cap01_fisica_y_reglas.md). Si cambias uno,
avisa al equipo: las grabaciones y los resultados viejos se hicieron con los
valores anteriores.
"""

# --- Mundo (unidades de pymunk; no tienen unidades fijas, ver README) ---
ANCHO_CANCHA = 1200.0      # la cancha va de x = 0 a x = ANCHO_CANCHA
X_RED = 600.0              # la red está justo en el centro
ALTO_RED = 60.0
GRAVEDAD = -900.0          # unidades por segundo², hacia abajo (y crece hacia arriba)
TECHO = 600.0              # si la pelota sube más que esto, es "fuera" para quien la golpeó
DT = 1.0 / 60.0            # paso de tiempo FIJO de la física (60 pasos = 1 segundo)
PASOS_POR_DECISION = 2     # los controladores deciden cada 2 pasos (30 Hz) para ahorrar cómputo
# Subpasos: cada paso de DT se divide en SUBPASOS pasos más chicos de pymunk.
# Así la pelota avanza menos entre dos cálculos y no "atraviesa" la raqueta
# (ver el capítulo 1 del libro y la prueba de 1000 golpes).
SUBPASOS = 2
# El suelo se extiende más allá de la cancha para que una pelota "fuera"
# bote en algún lado y el árbitro la vea caer.
LARGO_SUELO_FUERA = 1200.0
# Espacio detrás de la línea de fondo donde el jugador puede pararse (como en
# una cancha real). Sin él, una pelota que bota cerca del fondo y sigue de
# largo sería imposible de devolver.
ESPACIO_DETRAS_FONDO = 400.0

# --- Pelota ---
RADIO_PELOTA = 8.0
ELASTICIDAD_PELOTA = 0.75  # 1 = rebota sin perder energía, 0 = no rebota
FRICCION_PELOTA = 0.3      # frena un poco la pelota al botar (como un césped)
MASA_PELOTA = 0.1          # liviana frente a la raqueta, para que no la desvíe
VEL_MAX_PELOTA = 1100.0    # tope de rapidez: evita que atraviese la raqueta

# --- Jugador (cubo) y raqueta ---
TAMANO_JUGADOR = 40.0      # lado del cubo
LARGO_RAQUETA = 50.0
GROSOR_RAQUETA = 8.0
# Rango del ángulo de la raqueta, medido en el marco PROPIO del jugador:
# 0 = horizontal apuntando hacia la red, positivo = hacia arriba (radianes).
# La raqueta espera inclinada hacia abajo-adelante: en un golpe la pelota sale
# perpendicular a ella, así que este rango da tiros de 11° a 69° sobre la
# horizontal (ver jugador.velocidad_salida).
ANGULO_RAQUETA_MIN = -1.4
ANGULO_RAQUETA_MAX = -0.4
# Zona junto a la red donde los jugadores no pueden entrar: el largo de la
# raqueta más medio grosor y el radio de la pelota. Así la raqueta nunca
# alcanza una pelota que ya está del otro lado (en el tenis real, golpear en
# el campo rival está prohibido).
MARGEN_RED_JUGADOR = LARGO_RAQUETA + GROSOR_RAQUETA / 2 + RADIO_PELOTA
RECARGA_GOLPE = 0.4        # segundos que hay que esperar entre dos golpes
MASA_JUGADOR = 10.0
MASA_RAQUETA = 1.0
VEL_MAX_JUGADOR = 400.0    # rapidez horizontal con mover = 1 (cruza su mitad en ~1,5 s)
VEL_SALTO = 450.0          # rapidez vertical al saltar (sube ~110 unidades)
TOLERANCIA_SUELO = 1.0     # a menos de esto del suelo, el jugador "está en el suelo"
# Pivote de la raqueta: en la cara del cubo que mira a la red, a esta altura
# sobre el centro del cubo.
ALTURA_PIVOTE = 20.0
ELASTICIDAD_RAQUETA = 1.0  # pymunk multiplica las dos: pelota (0,75) × raqueta (1) = 0,75
# Motor de la raqueta (control proporcional, como las articulaciones de las
# criaturas): velocidad de giro = GANANCIA × (ángulo objetivo − ángulo actual).
GANANCIA_RAQUETA = 12.0
VEL_MAX_RAQUETA = 10.0     # rad/s fuera del golpe
FUERZA_MOTOR_RAQUETA = 2.0e6
# Golpe (swing): la raqueta barre hacia arriba (sentido antihorario en el
# marco propio) AMPLITUD_GOLPE radianes, o hasta que pase DURACION_GOLPE.
DURACION_GOLPE = 0.12      # segundos
VEL_GIRO_GOLPE = 12.0      # rad/s durante el golpe
AMPLITUD_GOLPE = 1.0       # radianes que barre un golpe desde el ángulo en que empieza
# Modelo de golpe: rapidez con que sale la pelota según la fuerza (0 a 1).
VEL_SALIDA_MIN = 300.0
VEL_SALIDA_MAX = 1000.0

# --- Reglas (árbitro) ---
TIEMPO_MAX_PUNTO = 30.0    # segundos; si se agota, el punto se anula (calibrado en F1: el plan decía 20)
PUNTOS_POR_PARTIDO = 6     # partido de evaluación, con saques alternados
# Dos contactos del mismo jugador separados por menos que esto son UN golpe
# (la pelota puede tocar la raqueta varios subpasos seguidos).
TIEMPO_MISMO_GOLPE = 0.1
# Saque neutro: la pelota sale desde lo alto de la red hacia el receptor.
ALTURA_SAQUE = 120.0       # altura inicial de la pelota (por encima de la red)
VX_SAQUE = (180.0, 320.0)  # rango de rapidez horizontal (hacia el receptor)
VY_SAQUE = (150.0, 350.0)  # rango de rapidez vertical inicial (hacia arriba)
X_INICIO_JUGADOR = 300.0   # distancia del jugador a su fondo al empezar cada punto

# --- Rival programado (rivales.py) ---
# Valores calibrados en F1 (ver capítulo 1 del libro): con ellos dos rivales
# programados pelotean.
RIVAL_X_CASA = 300.0           # dónde espera (marco propio) cuando la pelota se aleja
RIVAL_ALTURA_GOLPE = 40.0      # altura a la que golpea la pelota, después del bote
RIVAL_DISTANCIA_GOLPE = 50.0   # distancia horizontal cubo-pelota al golpear
RIVAL_ANTICIPACION = 0.05      # segundos antes de que llegue la pelota para empezar el golpe
RIVAL_ANGULO_TIRO = (25.0, 45.0)   # grados sobre la horizontal (se elige al azar)
RIVAL_DESTINO = (800.0, 1100.0)    # dónde quiere que bote, en x del marco propio
RIVAL_ERROR_FUERZA = 0.10      # error relativo de la fuerza (0,10 = ±10 % típico)
RIVAL_ERROR_POSICION = 20.0    # desviación típica (en unidades) del error al ubicarse
RIVAL_ZONA_FRENADO = 20.0      # a esta distancia del destino empieza a frenar

# --- Grabaciones (ver docs/interfaces.md) ---
VERSION_GRABACION = 1      # súbelo solo si el formato cambia de forma incompatible
PASOS_POR_CUADRO = 1       # 1 = se guarda cada paso de física (60 cuadros por segundo)
DECIMALES_GRABACION = 1    # redondear posiciones hace los archivos ~3 veces más pequeños
DECIMALES_ANGULO = 3       # los ángulos (radianes) necesitan más precisión: 0,1 rad ya son ~6°

SEMILLA = None             # pon un número (ej. 42) para obtener siempre los mismos resultados
