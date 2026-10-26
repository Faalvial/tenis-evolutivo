"""
eventos.py — VOCABULARIO COMÚN de lo que pasa en un partido.

Decidida en F1 (ver docs/libro/cap00_preparacion.md); el equipo puede revisarla.

El árbitro (R1) produce estos eventos; los consumen la aptitud (R2), las
métricas (R4) y las grabaciones (R3). Por eso son interfaz común: si todos
usan los mismos nombres, nadie tiene que adivinar qué significa cada cosa.

Cada evento es un diccionario simple (se guarda tal cual en JSON). Todos
llevan "tipo" y "t" (segundos desde el inicio del partido). Las coordenadas
van en el marco del MUNDO, no en el marco propio de un jugador.

Agregar un campo nuevo a un evento no rompe nada; cambiar o borrar uno sí,
y requiere acuerdo.
"""

# --- Tipos de evento ---
SAQUE = "saque"   # campos: hacia (lado que recibe)
GOLPE = "golpe"   # campos: jugador (lado), x, y (posición de la pelota), fuerza (0..1).
                  # Es un CONTACTO de la pelota con la raqueta, no un swing: un swing
                  # al aire no produce evento. fuerza = 0 si la tocó sin golpear.
BOTE = "bote"     # campos: x, campo (lado donde botó), golpeador (lado o None si viene del saque),
                  #         valido (True si es el primer bote en el campo rival de quien golpeó)
RED = "red"       # campos: golpeador (lado o None). La pelota tocó la red.
PUNTO = "punto"   # campos: ganador (lado o None si se anuló), motivo, golpes_validos,
                  #         distancia_minima ([izq, der]: lo más cerca que estuvo cada
                  #         raqueta de la pelota; la usa la aptitud de la etapa 1)

TIPOS = (SAQUE, GOLPE, BOTE, RED, PUNTO)

# --- Motivos por los que termina un punto (sección 3.5 del plan) ---
DOBLE_BOTE = "doble_bote"     # el que deja botar dos veces pierde (lo usual: el rival hizo un ganador)
BOTE_PROPIO = "bote_propio"   # golpeó y botó primero en su campo (incluye pegarle a la red)
FUERA = "fuera"               # golpeó y la pelota cayó fuera de la cancha
SOBRE_TECHO = "techo"         # golpeó y la pelota superó el techo
ANULADO = "anulado"           # se agotó TIEMPO_MAX_PUNTO; no hay ganador

MOTIVOS = (DOBLE_BOTE, BOTE_PROPIO, FUERA, SOBRE_TECHO, ANULADO)


def evento(tipo, t, **campos):
    """Crea un evento comprobando que el tipo exista (evita errores de tipeo)."""
    if tipo not in TIPOS:
        raise ValueError(f"Tipo de evento desconocido: {tipo!r}. Usa uno de {TIPOS}")
    if tipo == PUNTO and campos.get("motivo") not in MOTIVOS:
        raise ValueError(f"Motivo de punto desconocido: {campos.get('motivo')!r}")
    return {"tipo": tipo, "t": t, **campos}
