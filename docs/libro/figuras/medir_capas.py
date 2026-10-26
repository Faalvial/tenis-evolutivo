"""
medir_capas.py — Mide cómo cambia el juego al encender cada capa de realismo
del golpe (capítulo 1, sección 1.6).

Uso (desde la raíz del repositorio):
    python docs/libro/figuras/medir_capas.py

Para cada combinación de capas mide, con el rival programado:
  - precisión SIN errores: % de saques bien devueltos y cuánto se desvía el
    bote del punto apuntado (si el golpe es caótico, esto se dispara);
  - peloteo CON los errores de config: golpes válidos por punto y anulados;
  - dónde toca la pelota en la raqueta (0 = mango, 50 = punta).
"""

import os
import statistics
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, RAIZ)

import config
import jugador
import partido
from controlador import ControladorQuieto
from rivales import RivalProgramado

# (nombre, {parámetro: valor}) — se aplican sobre config, en este orden.
CAPAS = [
    ("capa 0 (base)", {}),
    ("+ capa 1 (potencia que llega)", {"APORTE_PELOTA_ENTRANTE": 0.3}),
    ("+ capa 2 (punto dulce)", {"APORTE_PELOTA_ENTRANTE": 0.3,
                                "PERDIDA_FUERA_DEL_PUNTO_DULCE": 0.3}),
    ("+ capa 3 (ángulo al tocar)", {"APORTE_PELOTA_ENTRANTE": 0.3,
                                    "PERDIDA_FUERA_DEL_PUNTO_DULCE": 0.3,
                                    "MEZCLA_ANGULO_CONTACTO": 1.0}),
]
APAGADAS = {"APORTE_PELOTA_ENTRANTE": 0.0, "PERDIDA_FUERA_DEL_PUNTO_DULCE": 0.0,
            "MEZCLA_ANGULO_CONTACTO": 0.0}
SAQUES = 200
PARTIDOS = 10

contactos = []   # distancias al mango de cada golpe (se llena espiando a Jugador)
_velocidad_original = jugador.Jugador.velocidad_salida


def _espiar(self, pos, vel):
    contactos.append(self.distancia_al_mango(pos))
    return _velocidad_original(self, pos, vel)


def precision_sin_errores():
    devueltas, desvios = 0, []
    for s in range(SAQUES):
        rival = RivalProgramado(s, error_posicion=0.0, error_fuerza=0.0)
        evs = partido.jugar_partido(rival, ControladorQuieto(), 1000 + s, puntos=1)
        botes = [e for e in evs if e["tipo"] == "bote" and e["golpeador"] == 0 and e["valido"]]
        if botes or evs[-1]["golpes_validos"] > 0:
            devueltas += 1
        if botes:
            desvios.append(abs(botes[0]["x"] - rival.x_destino))
    return 100 * devueltas / SAQUES, statistics.mean(desvios), statistics.pstdev(desvios)


def peloteo_con_errores():
    puntos = []
    for s in range(PARTIDOS):
        evs = partido.jugar_partido(RivalProgramado(100 + s), RivalProgramado(200 + s), s)
        puntos += [e for e in evs if e["tipo"] == "punto"]
    golpes = sum(p["golpes_validos"] for p in puntos) / len(puntos)
    anulados = 100 * sum(p["motivo"] == "anulado" for p in puntos) / len(puntos)
    return golpes, anulados


def main():
    jugador.Jugador.velocidad_salida = _espiar
    print("| Capas | Saques devueltos (sin error) | Desvío del bote (sin error) "
          "| Golpes válidos por punto | Anulados | Contacto en la raqueta |")
    print("|---|---|---|---|---|---|")
    for nombre, valores in CAPAS:
        for clave, valor in {**APAGADAS, **valores}.items():
            setattr(config, clave, valor)
        contactos.clear()
        devueltas, desvio, desvio_sd = precision_sin_errores()
        golpes, anulados = peloteo_con_errores()
        r_media, r_sd = statistics.mean(contactos), statistics.pstdev(contactos)
        print(f"| {nombre} | {devueltas:.0f} % | {desvio:.0f} ± {desvio_sd:.0f} "
              f"| {golpes:.1f} | {anulados:.0f} % | {r_media:.0f} ± {r_sd:.0f} |")


if __name__ == "__main__":
    main()
