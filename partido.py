"""
partido.py — Simula un partido entre dos controladores y devuelve sus eventos.

Aquí se juntan las piezas: el mundo (física), los jugadores (cuerpos), el
árbitro (reglas) y los controladores (quién decide). partido.py no sabe si
juega una IA, el rival programado o un humano: a todos les entrega una
Percepcion y les pide una Accion (ver controlador.py).

Bucle de un punto, en cada paso de física (DT = 1/60 s):
  1. cada PASOS_POR_DECISION pasos, los controladores deciden una acción;
  2. los jugadores aplican su acción (moverse, saltar, raqueta);
  3. el mundo avanza (pymunk) y anota los contactos de la pelota;
  4. el árbitro convierte esos contactos en eventos y decide si hay punto;
  5. si se pidió, se guarda un cuadro de la grabación.

Cada punto se juega en un mundo NUEVO: así nada de un punto (una raqueta que
quedó girando, por ejemplo) contamina el siguiente.
"""

import random

import config
import eventos
import grabar
from arbitro import Arbitro
from controlador import DERECHA, IZQUIERDA, Percepcion, espejar_percepcion
from jugador import Jugador
from mundo import Mundo


def jugar_partido(ctrl_izq, ctrl_der, semilla, puntos=config.PUNTOS_POR_PARTIDO,
                  grabacion=None, saque=None):
    """
    Simula un partido y devuelve la lista de eventos (eventos.py).

    - semilla: decide los saques. La misma semilla da el mismo partido.
    - grabacion: si se pasa una (grabar.nueva_grabacion), se llena cuadro a cuadro.
    - saque: función opcional saque(azar, receptor) -> (x, y, vx, vy) para
      reemplazar el saque neutro (el lanzapelotas de la etapa 1 la usa).
    """
    azar = random.Random(semilla)
    funcion_saque = saque or saque_neutro
    arbitro = Arbitro()
    controladores = (ctrl_izq, ctrl_der)
    t = 0.0
    for n in range(puntos):
        receptor = IZQUIERDA if n % 2 == 0 else DERECHA   # saques alternados
        lanzamiento = funcion_saque(azar, receptor)
        t = jugar_punto(controladores, arbitro, receptor, lanzamiento, t, grabacion)
    if grabacion is not None:
        for ev in arbitro.eventos:
            grabar.agregar_evento(grabacion, ev)
    return arbitro.eventos


def saque_neutro(azar, receptor):
    """
    Saque automático (sección 3.5): la pelota sale desde lo alto de la red
    hacia el campo del receptor, con velocidad al azar dentro de un rango.
    Nadie tiene que aprender a sacar, y nadie puede "negarse" a sacar.
    """
    vx = azar.uniform(*config.VX_SAQUE)
    vy = azar.uniform(*config.VY_SAQUE)
    direccion = -1 if receptor == IZQUIERDA else 1
    return (config.X_RED, config.ALTURA_SAQUE, direccion * vx, vy)


def jugar_punto(controladores, arbitro, receptor, lanzamiento, t, grabacion=None):
    """Juega un punto completo y devuelve el tiempo en que terminó."""
    mundo = Mundo()
    jugadores = (Jugador(mundo, IZQUIERDA, config.X_INICIO_JUGADOR),
                 Jugador(mundo, DERECHA, config.ANCHO_CANCHA - config.X_INICIO_JUGADOR))
    mundo.colocar_pelota(*lanzamiento)
    for c in controladores:
        c.reiniciar()
    arbitro.nuevo_punto(t, receptor)
    acciones = [None, None]
    distancia_minima = [float("inf"), float("inf")]
    paso = 0
    while not arbitro.punto_terminado:
        if paso % config.PASOS_POR_DECISION == 0:
            for lado in (IZQUIERDA, DERECHA):
                acciones[lado] = controladores[lado].decidir(percibir(mundo, jugadores, lado))
                # La distancia pelota-raqueta se mide solo cuando se decide
                # (cada 2 pasos): medirla en cada paso costaba ~25 % del tiempo.
                d = jugadores[lado].distancia_a(mundo.pelota.position)
                distancia_minima[lado] = min(distancia_minima[lado], d)
        for lado in (IZQUIERDA, DERECHA):
            jugadores[lado].aplicar(acciones[lado], config.DT)
        mundo.avanzar()
        paso += 1
        t += config.DT
        avisar_al_arbitro(mundo, jugadores, arbitro, t)
        if grabacion is not None and paso % config.PASOS_POR_CUADRO == 0:
            grabar.agregar_cuadro(grabacion, t, tuple(mundo.pelota.position),
                                  jugadores[IZQUIERDA].estado_grabacion(),
                                  jugadores[DERECHA].estado_grabacion())
    # Campo agregado al evento PUNTO (compatible con la interfaz): la menor
    # distancia entre la pelota y cada raqueta durante el punto. La usa la
    # aptitud de la etapa 1 para premiar "acercarse a la pelota".
    arbitro.eventos[-1]["distancia_minima"] = [round(d, 1) for d in distancia_minima]
    return t


def avisar_al_arbitro(mundo, jugadores, arbitro, t):
    """Traduce los contactos que anotó la física en avisos para el árbitro."""
    x, y = mundo.pelota.position
    for contacto in mundo.contactos:
        if contacto[0] == "bote":
            arbitro.bote(t, contacto[1])
        elif contacto[0] == "red":
            arbitro.red(t)
        elif contacto[0] == "toque":
            lado = contacto[1]
            arbitro.golpe(t, lado, round(x, 1), round(y, 1),
                          round(jugadores[lado].fuerza_golpe, 3))
    mundo.contactos.clear()
    # Si la pelota se escapó más allá del suelo, cuenta como bote fuera.
    if y < -config.RADIO_PELOTA:
        arbitro.bote(t, x)
    arbitro.revisar(t, y)


def percibir(mundo, jugadores, lado):
    """Arma la Percepcion del jugador `lado`, ya en su marco propio."""
    propio, rival = jugadores[lado], jugadores[1 - lado]
    pelota = mundo.pelota
    p = Percepcion(
        pelota_x=pelota.position.x, pelota_y=pelota.position.y,
        pelota_vx=pelota.velocity.x, pelota_vy=pelota.velocity.y,
        propio_x=propio.cuerpo.position.x, propio_y=propio.cuerpo.position.y,
        propio_vy=propio.cuerpo.velocity.y, en_suelo=propio.en_suelo(),
        raqueta_angulo=propio.angulo_raqueta_mundo(), recarga=propio.recarga,
        rival_x=rival.cuerpo.position.x, rival_y=rival.cuerpo.position.y,
    )
    return p if lado == IZQUIERDA else espejar_percepcion(p)


def resumen(eventos_partido):
    """Cuenta puntos por jugador y motivos; útil para imprimir y en pruebas."""
    puntos = [ev for ev in eventos_partido if ev["tipo"] == eventos.PUNTO]
    ganados = [sum(1 for ev in puntos if ev["ganador"] == lado) for lado in (0, 1)]
    motivos = {}
    for ev in puntos:
        motivos[ev["motivo"]] = motivos.get(ev["motivo"], 0) + 1
    golpes = [ev["golpes_validos"] for ev in puntos]
    return {"puntos": len(puntos), "ganados": ganados, "motivos": motivos,
            "golpes_validos_por_punto": sum(golpes) / len(golpes) if golpes else 0.0}


# --- Uso desde la terminal ---
#   python partido.py                         un partido entre dos rivales programados
#   python partido.py --grabar grabaciones/demo.json   ...y lo graba para ver2d.py
#   python partido.py --medir 20              mide cuánto tarda un partido

def _principal():
    import argparse
    import time

    from rivales import RivalProgramado

    parser = argparse.ArgumentParser(description="Partido entre dos rivales programados.")
    parser.add_argument("--semilla", type=int, default=0)
    parser.add_argument("--puntos", type=int, default=config.PUNTOS_POR_PARTIDO)
    parser.add_argument("--grabar", metavar="RUTA", help="guardar la grabación en RUTA (.json)")
    parser.add_argument("--medir", type=int, metavar="N", help="jugar N partidos y medir el tiempo")
    args = parser.parse_args()

    if args.medir:
        inicio = time.perf_counter()
        simulado = 0.0
        for s in range(args.medir):
            evs = jugar_partido(RivalProgramado(100 + s), RivalProgramado(200 + s), s, args.puntos)
            simulado += evs[-1]["t"]
        total = time.perf_counter() - inicio
        print(f"{args.medir} partidos de {args.puntos} puntos en {total:.1f} s")
        print(f"  {total / args.medir:.3f} s por partido (un solo núcleo)")
        print(f"  {simulado / args.medir:.1f} s de juego simulado por partido "
              f"({simulado / total:.0f} veces más rápido que el tiempo real)")
        return

    g = None
    if args.grabar:
        g = grabar.nueva_grabacion(["rival programado A", "rival programado B"],
                                   semilla=args.semilla)
    evs = jugar_partido(RivalProgramado(args.semilla), RivalProgramado(args.semilla + 1000),
                        args.semilla, args.puntos, grabacion=g)
    for ev in evs:
        if ev["tipo"] == eventos.PUNTO:
            quien = "anulado" if ev["ganador"] is None else f"gana el jugador {ev['ganador']}"
            print(f"t = {ev['t']:6.1f} s  {quien:18s} motivo: {ev['motivo']:12s} "
                  f"golpes válidos: {ev['golpes_validos']}")
    print(resumen(evs))
    if g is not None:
        grabar.guardar_grabacion(g, args.grabar)
        print(f"Grabación guardada en {args.grabar}  (verla con: python ver2d.py {args.grabar})")


if __name__ == "__main__":
    _principal()
