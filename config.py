"""
config.py — Todos los parámetros del proyecto en un solo lugar.

Regla del equipo: nunca escribir números "mágicos" dentro del código; si un
valor puede cambiar, va aquí con un comentario que diga qué significa.

Los valores de física y reglas son INICIALES (sección 3 del plan) y se
calibran en la fase F1. Si cambias uno, avisa al equipo: las grabaciones y los
resultados viejos se hicieron con los valores anteriores.
"""

# --- Mundo (unidades de pymunk; no tienen unidades fijas, ver README) ---
ANCHO_CANCHA = 1200.0      # la cancha va de x = 0 a x = ANCHO_CANCHA
X_RED = 600.0              # la red está justo en el centro
ALTO_RED = 60.0
GRAVEDAD = -900.0          # unidades por segundo², hacia abajo (y crece hacia arriba)
TECHO = 600.0              # si la pelota sube más que esto, es "fuera" para quien la golpeó
DT = 1.0 / 60.0            # paso de tiempo FIJO de la física (60 pasos = 1 segundo)
PASOS_POR_DECISION = 2     # los controladores deciden cada 2 pasos (30 Hz) para ahorrar cómputo

# --- Pelota ---
RADIO_PELOTA = 8.0
ELASTICIDAD_PELOTA = 0.75  # 1 = rebota sin perder energía, 0 = no rebota

# --- Jugador (cubo) y raqueta ---
TAMANO_JUGADOR = 40.0      # lado del cubo
LARGO_RAQUETA = 50.0
GROSOR_RAQUETA = 8.0
# Rango del ángulo de la raqueta, medido en el marco PROPIO del jugador:
# 0 = horizontal apuntando hacia la red, positivo = hacia arriba (radianes).
# Valores provisionales: R1 los calibra en F1.
ANGULO_RAQUETA_MIN = -1.0
ANGULO_RAQUETA_MAX = 1.0
RECARGA_GOLPE = 0.4        # segundos que hay que esperar entre dos golpes

# --- Reglas (árbitro) ---
TIEMPO_MAX_PUNTO = 20.0    # segundos; si se agota, el punto se anula
PUNTOS_POR_PARTIDO = 6     # partido de evaluación, con saques alternados

# --- Grabaciones (ver docs/interfaces.md) ---
VERSION_GRABACION = 1      # súbelo solo si el formato cambia de forma incompatible
PASOS_POR_CUADRO = 1       # 1 = se guarda cada paso de física (60 cuadros por segundo)
DECIMALES_GRABACION = 1    # redondear posiciones hace los archivos ~3 veces más pequeños
DECIMALES_ANGULO = 3       # los ángulos (radianes) necesitan más precisión: 0,1 rad ya son ~6°

SEMILLA = None             # pon un número (ej. 42) para obtener siempre los mismos resultados
