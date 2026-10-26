"""
jugar.py — Humano contra IA (V3): una persona juega con el teclado.

La persona es un Controlador más (controlador.py): recibe la misma Percepcion
que la IA y devuelve una Accion. La diferencia es que su Accion sale del
teclado. Juega siempre a la IZQUIERDA (azul), así su marco propio es el del
mundo: "derecha" es "hacia la red".

La simulación avanza UN paso de física por cuadro de pantalla (60 por
segundo), o sea en tiempo real; con --velocidad 0.7 va más lenta (más fácil).
Se dibuja con el mismo visor que ver2d.py, en modo "en vivo".

Uso:
    python jugar.py                                       contra el rival programado
    python jugar.py --campeon resultados/prueba           contra el campeón de ese entrenamiento
    python jugar.py --campeon resultados/experimento/semilla_1/rama_A
    python jugar.py --puntos 10 --velocidad 0.7 --grabar grabaciones/partida.json

Teclas:
    flechas izquierda/derecha  moverse          flecha arriba  saltar
    W / S                      raqueta: globo alto / tiro plano (sin tecla: intermedio)
    espacio                    golpear (con Shift: fuerte; con Ctrl: suave)
    Esc                        salir
"""

import argparse
import os
import random

import config
import grabar
from arbitro import Arbitro
from controlador import Accion, Controlador
from partido import Punto, saque_neutro

FUERZA_NORMAL, FUERZA_FUERTE, FUERZA_SUAVE = 0.6, 1.0, 0.3
PAUSA_ENTRE_PUNTOS = 1.2     # segundos para ver cómo terminó cada punto


class ControladorHumano(Controlador):
    """Traduce las teclas apretadas (un conjunto de nombres) a una Accion."""

    nombre = "humano"

    def __init__(self):
        self.teclas = set()

    def decidir(self, p):
        t = self.teclas
        mover = (1.0 if "derecha" in t else 0.0) - (1.0 if "izquierda" in t else 0.0)
        angulo = (1.0 if "globo" in t else 0.0) - (1.0 if "plano" in t else 0.0)
        golpe = 0.0
        if "golpe" in t:
            golpe = FUERZA_FUERTE if "fuerte" in t else FUERZA_SUAVE if "suave" in t else FUERZA_NORMAL
        return Accion(mover=mover, saltar="saltar" in t, angulo_raqueta=angulo, golpe=golpe)


def rival_desde_carpeta(carpeta):
    """El campeón más avanzado de una carpeta de entrenamiento (o de una rama de la etapa 3)."""
    from entrenar import campeon_mas_reciente
    from guardado import cargar_json
    from red import ControladorRed
    estado = cargar_json(os.path.join(carpeta, "estado.json"))
    if "salon" in estado:                                  # una rama de la etapa 3
        genoma, nombre = estado["salon"][-1], f"IA {estado['tratamiento']} gen {estado['generacion']}"
    else:
        etapa, genoma = campeon_mas_reciente(estado)
        nombre = f"IA etapa {etapa}"
    return ControladorRed(genoma, nombre=nombre)


class Juego:
    """
    Una partida en vivo. cuadro(teclas) avanza un paso y devuelve False cuando
    terminó. Está separada de la ventana para poder probarla sin teclado.
    """

    def __init__(self, rival, puntos, semilla):
        self.humano = ControladorHumano()
        self.controladores = (self.humano, rival)
        self.puntos = puntos
        self.azar = random.Random(semilla)
        self.arbitro = Arbitro()
        self.g = grabar.nueva_grabacion([self.humano.nombre, rival.nombre])
        self.g["eventos"] = self.arbitro.eventos          # el visor ve los eventos mientras ocurren
        self.n, self.t, self.pausa = 0, 0.0, 0.0
        self.punto = self._nuevo_punto()

    def _nuevo_punto(self):
        receptor = self.n % 2
        return Punto(self.controladores, self.arbitro, receptor,
                     saque_neutro(self.azar, receptor), self.t, self.g)

    def cuadro(self, teclas):
        if self.pausa > 0:                                 # pausa corta entre puntos
            self.pausa -= config.DT
            return True
        self.humano.teclas = teclas
        self.punto.avanzar()
        self.t = self.punto.t
        if self.punto.terminado:
            self.punto.cerrar()
            self.n += 1
            if self.n >= self.puntos:
                return False
            self.pausa = PAUSA_ENTRE_PUNTOS
            self.punto = self._nuevo_punto()
        return True


TECLAS = {"left": "izquierda", "right": "derecha", "up": "saltar", "w": "globo", "s": "plano",
          "space": "golpe"}


def teclas_apretadas(pygame):
    apretadas = pygame.key.get_pressed()
    teclas = {nombre for clave, nombre in TECLAS.items() if apretadas[pygame.key.key_code(clave)]}
    modificadores = pygame.key.get_mods()
    if modificadores & pygame.KMOD_SHIFT:
        teclas.add("fuerte")
    if modificadores & pygame.KMOD_CTRL:
        teclas.add("suave")
    return teclas


def jugar(rival, puntos, velocidad, semilla, ruta_grabacion=None):
    import pygame
    import ver2d
    ver2d._iniciar(pygame)
    pantalla = pygame.display.set_mode((ver2d.ANCHO_VENTANA, ver2d.ALTO_VENTANA))
    pygame.display.set_caption("Tenis evolutivo — humano contra IA")
    reloj = pygame.time.Clock()
    juego = Juego(rival, puntos, semilla)
    escena = ver2d.Escena(pygame, juego.g, en_vivo=True)
    sigue = True
    while sigue:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT or (evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE):
                sigue = False
        if sigue:
            sigue = juego.cuadro(teclas_apretadas(pygame))
        escena.dibujar(pantalla, juego.t)
        pygame.display.flip()
        reloj.tick(ver2d.FPS * velocidad)
    if ruta_grabacion:
        grabar.guardar_grabacion(juego.g, ruta_grabacion)
        print(f"Partida guardada en {ruta_grabacion}")
    ganados = ver2d.marcador_hasta(juego.arbitro.eventos, juego.t)
    print(f"Resultado: {juego.humano.nombre} {ganados[0]} - {ganados[1]} {rival.nombre}")
    pygame.quit()


def _principal():
    from rivales import RivalProgramado
    parser = argparse.ArgumentParser(description="Humano contra IA.")
    parser.add_argument("--campeon", metavar="CARPETA", help="jugar contra el campeón de esta carpeta")
    parser.add_argument("--puntos", type=int, default=config.PUNTOS_POR_PARTIDO)
    parser.add_argument("--velocidad", type=float, default=1.0, help="1 = tiempo real; 0,7 = más lento")
    parser.add_argument("--semilla", type=int, default=0)
    parser.add_argument("--grabar", metavar="RUTA", help="guardar la partida para verla con ver2d/ver3d")
    args = parser.parse_args()
    rival = rival_desde_carpeta(args.campeon) if args.campeon else RivalProgramado(args.semilla)
    jugar(rival, args.puntos, args.velocidad, args.semilla, args.grabar)


if __name__ == "__main__":
    _principal()
