"""
grabar.py — Repeticiones de partidos (formato de grabación).

El FORMATO es interfaz común (decidido en F1, ver docs/libro/cap00_preparacion.md).
R3 es dueño de este módulo y puede agregarle funciones; cambiar el formato
requiere acuerdo (ver docs/interfaces.md).

¿Por qué grabar en vez de dibujar en vivo? El entrenamiento nunca dibuja: así
corre rápido y en paralelo. Los visores (ver2d, ver3d) solo leen estos
archivos, de modo que el 3D no depende de la física ni la frena.

Uso desde partido.py (solo si se pidió grabar):
    g = nueva_grabacion(["IA gen 120", "rival programado"], tratamiento="A")
    ... en cada paso de física con paso % PASOS_POR_CUADRO == 0:
    agregar_cuadro(g, t, (bx, by), jugador_izq, jugador_der)
    ... cuando el árbitro produce un evento:
    agregar_evento(g, ev)
    guardar_grabacion(g, "grabaciones/partido.json")
"""

import os
from datetime import datetime

import config
from guardado import cargar_json, guardar_json

FORMATO = "tenis_evolutivo/grabacion"

# Orden de los números en cada cuadro. Se guarda también dentro del archivo,
# para que cualquiera que lo abra sepa qué es cada número.
# Todo en el marco del MUNDO; los ángulos de raqueta en radianes desde +x, antihorario.
COLUMNAS = [
    "t",
    "pelota_x", "pelota_y",
    "izq_x", "izq_y", "izq_raqueta_x", "izq_raqueta_y", "izq_raqueta_angulo",
    "der_x", "der_y", "der_raqueta_x", "der_raqueta_y", "der_raqueta_angulo",
]


def nueva_grabacion(nombres_jugadores, **meta):
    """
    Crea una grabación vacía. meta son datos libres para el visor y los
    videos: tratamiento, generacion, semilla, etc.

    Las medidas de la cancha se COPIAN de config: si config cambia después,
    las grabaciones viejas se siguen dibujando con sus medidas originales.
    """
    return {
        "formato": FORMATO,
        "version": config.VERSION_GRABACION,
        "meta": {
            "jugadores": list(nombres_jugadores),
            "fecha": datetime.now().isoformat(timespec="seconds"),
            **meta,
        },
        "cancha": {
            "ancho": config.ANCHO_CANCHA,
            "x_red": config.X_RED,
            "alto_red": config.ALTO_RED,
            "techo": config.TECHO,
            "radio_pelota": config.RADIO_PELOTA,
            "tamano_jugador": config.TAMANO_JUGADOR,
            "largo_raqueta": config.LARGO_RAQUETA,
            "grosor_raqueta": config.GROSOR_RAQUETA,
        },
        "dt_cuadro": config.DT * config.PASOS_POR_CUADRO,
        "columnas": COLUMNAS,
        "cuadros": [],
        "eventos": [],
    }


def agregar_cuadro(grabacion, t, pelota, jugador_izq, jugador_der):
    """
    Agrega un cuadro (una "foto" del partido).

    pelota: (x, y)
    jugador_izq, jugador_der: (x, y, raqueta_x, raqueta_y, raqueta_angulo)
    """
    pos = config.DECIMALES_GRABACION
    cuadro = [round(t, 4), round(pelota[0], pos), round(pelota[1], pos)]
    for x, y, rx, ry, angulo in (jugador_izq, jugador_der):
        cuadro += [round(x, pos), round(y, pos), round(rx, pos), round(ry, pos),
                   round(angulo, config.DECIMALES_ANGULO)]
    grabacion["cuadros"].append(cuadro)


def agregar_evento(grabacion, evento):
    """Guarda un evento de eventos.py (golpe, bote, punto...) tal cual."""
    grabacion["eventos"].append(evento)


def guardar_grabacion(grabacion, ruta):
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    guardar_json(ruta, grabacion)


def cargar_grabacion(ruta):
    """Lee una grabación y comprueba que sea de un formato que entendemos."""
    grabacion = cargar_json(ruta)
    if grabacion.get("formato") != FORMATO:
        raise ValueError(f"{ruta} no es una grabación de tenis_evolutivo")
    if grabacion.get("version") != config.VERSION_GRABACION:
        raise ValueError(
            f"{ruta} tiene formato versión {grabacion.get('version')}, "
            f"pero este código lee la versión {config.VERSION_GRABACION}"
        )
    return grabacion


def cuadro_como_dict(grabacion, i):
    """Devuelve el cuadro i con nombres, ej. {"t": 0.5, "pelota_x": 312.4, ...}."""
    return dict(zip(grabacion["columnas"], grabacion["cuadros"][i]))
