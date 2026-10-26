"""
ver3d.py — Visor 3D de grabaciones (Ursina), para la feria.

Como ver2d.py, SOLO lee grabaciones: nunca importa la física. La simulación es
2D (plano x-y); aquí ese plano se dibuja dentro de una cancha con
profundidad, con los jugadores y la pelota en z = 0, y una cámara que gira
alrededor (con el mouse o sola). La sombra bajo la pelota ayuda a percibir a
qué altura está, algo que en 3D cuesta más que en 2D.

Requiere: pip install -r requirements-3d.txt

Uso:
    python ver3d.py grabaciones/demo.json
    python ver3d.py grabaciones/demo.json --lento      (empieza a velocidad ×0,5)
    python ver3d.py grabaciones/demo.json --captura cuadro.png --t 5.0   (sin ventana)

Teclas: espacio = pausa, flechas arriba/abajo = velocidad, R = reiniciar,
        G = girar sola la cámara (para la feria), Esc = salir.
Mouse:  clic derecho + arrastrar = girar, rueda = acercar/alejar.
"""

import argparse
import math
import os
import sys

import grabar
from ver2d import VELOCIDADES, gesto, indice_cuadro, marcador_hasta

ESCALA = 0.01            # 1 unidad de pymunk = 0,01 unidades de Ursina (la cancha mide 12)
PROFUNDIDAD = 5.5        # ancho de la cancha "hacia adentro" (solo visual)
VELOCIDAD_GIRO = 8.0     # grados por segundo de la cámara en modo automático
COLOR_JUGADOR = ((42, 120, 214), (235, 104, 52))
COLOR_PELOTA = (215, 230, 60)
COLOR_CESPED = (74, 150, 86)
COLOR_FUERA = (178, 112, 78)


def a_3d(x, y):
    """Coordenadas de la simulación (x, y) -> posición de Ursina (x, y, z=0)."""
    return (x * ESCALA, y * ESCALA, 0.0)


class Escena3D:
    """Arma la cancha, los jugadores y la pelota, y los mueve según la grabación."""

    def __init__(self, ursina, g):
        self.u = ursina
        self.g = g
        self.cancha = g["cancha"]
        self.nombres = g["meta"].get("jugadores", ["izquierda", "derecha"])
        c = ursina.color
        self.rgb = lambda r, gg, b, a=255: c.rgba(r / 255, gg / 255, b / 255, a / 255)
        self._cancha()
        self.jugadores = [self._jugador(lado) for lado in (0, 1)]
        self.pelota = ursina.Entity(model="sphere", color=self.rgb(*COLOR_PELOTA),
                                    scale=2 * self.cancha["radio_pelota"] * ESCALA)
        self.sombra = ursina.Entity(model="circle", rotation_x=90, color=self.rgb(0, 0, 0, 90),
                                    scale=2.4 * self.cancha["radio_pelota"] * ESCALA)
        self.marcador = ursina.Text(text="", origin=(0, 0), y=0.43, scale=1.3,
                                    color=self.rgb(30, 30, 35))

    # --- Construcción ---

    def _cancha(self):
        u, ancho = self.u, self.cancha["ancho"] * ESCALA
        centro = ancho / 2
        u.Entity(model="plane", scale=(ancho * 2.2, 1, PROFUNDIDAD * 2.5), position=(centro, -0.01, 0),
                 color=self.rgb(*COLOR_FUERA))
        u.Entity(model="plane", scale=(ancho, 1, PROFUNDIDAD), position=(centro, 0, 0),
                 color=self.rgb(*COLOR_CESPED))
        blanco = self.rgb(250, 250, 245)
        for x in (0, ancho):                                         # líneas de fondo
            u.Entity(model="cube", scale=(0.05, 0.005, PROFUNDIDAD), position=(x, 0.003, 0), color=blanco)
        for z in (-PROFUNDIDAD / 2, PROFUNDIDAD / 2):                # líneas laterales
            u.Entity(model="cube", scale=(ancho, 0.005, 0.05), position=(centro, 0.003, z), color=blanco)
        x_red, alto = self.cancha["x_red"] * ESCALA, self.cancha["alto_red"] * ESCALA
        u.Entity(model="cube", scale=(0.02, alto, PROFUNDIDAD), position=(x_red, alto / 2, 0),
                 color=self.rgb(30, 30, 35, 150))                    # la red (semitransparente)
        u.Entity(model="cube", scale=(0.04, 0.03, PROFUNDIDAD), position=(x_red, alto, 0), color=blanco)
        for z in (-PROFUNDIDAD / 2, PROFUNDIDAD / 2):                # postes
            u.Entity(model="cube", scale=(0.05, alto + 0.05, 0.05), position=(x_red, (alto + 0.05) / 2, z),
                     color=self.rgb(70, 70, 75))

    def _jugador(self, lado):
        u = self.u
        tam = self.cancha["tamano_jugador"] * ESCALA
        cubo = u.Entity(model="cube", scale=tam, color=self.rgb(*COLOR_JUGADOR[lado]))
        raqueta = u.Entity(model="cube", color=self.rgb(*[int(v * 0.65) for v in COLOR_JUGADOR[lado]]),
                           scale=(self.cancha["largo_raqueta"] * ESCALA,
                                  self.cancha["grosor_raqueta"] * ESCALA, 0.12))
        # Ojos en la cara que mira a la cámara (z negativa), corridos hacia la red.
        hacia_red = 1 if lado == 0 else -1
        ojos = []
        for dx in (-0.18, 0.18):
            blanco = u.Entity(parent=cubo, model="sphere", color=u.color.white, scale=0.32,
                              position=(hacia_red * 0.12 + dx, 0.05, -0.5))
            pupila = u.Entity(parent=blanco, model="sphere", color=self.rgb(25, 25, 35), scale=0.5,
                              position=(0, 0, -0.35))
            ojos.append((blanco, pupila))
        return {"cubo": cubo, "raqueta": raqueta, "ojos": ojos}

    # --- Cada cuadro ---

    def mostrar(self, t, velocidad=1.0, pausado=False):
        cuadro = grabar.cuadro_como_dict(self.g, indice_cuadro(self.g, t))
        for lado, prefijo in enumerate(("izq", "der")):
            j = self.jugadores[lado]
            j["cubo"].position = a_3d(cuadro[f"{prefijo}_x"], cuadro[f"{prefijo}_y"])
            j["raqueta"].position = a_3d(cuadro[f"{prefijo}_raqueta_x"], cuadro[f"{prefijo}_raqueta_y"])
            # Ursina gira en sentido horario con ángulos positivos; la simulación, antihorario.
            j["raqueta"].rotation_z = -math.degrees(cuadro[f"{prefijo}_raqueta_angulo"])
            self._mirar(j, cuadro, gesto(self.g["eventos"], t, lado))
        bx, by = cuadro["pelota_x"], cuadro["pelota_y"]
        self.pelota.position = a_3d(bx, by)
        self.sombra.position = (bx * ESCALA, 0.005, 0)
        # La sombra se achica y aclara con la altura.
        f = max(0.35, 1 - by / 500)
        self.sombra.scale = 2.4 * self.cancha["radio_pelota"] * ESCALA * f
        izq, der = marcador_hasta(self.g["eventos"], t)
        estado = "  (pausa)" if pausado else ""
        meta = self.g["meta"]
        extra = "  ·  ".join(f"{k} {meta[k]}" for k in ("tratamiento", "generacion") if k in meta)
        self.marcador.text = (f"{self.nombres[0]}  {izq} - {der}  {self.nombres[1]}\n"
                              f"t = {t:5.1f} s   ×{velocidad}{estado}" + (f"\n{extra}" if extra else ""))

    def _mirar(self, jugador, cuadro, cara):
        """Las pupilas se corren hacia la pelota; feliz = ojos chatos (cerrados), triste = caídos."""
        for blanco, pupila in jugador["ojos"]:
            dx = cuadro["pelota_x"] * ESCALA - blanco.world_x
            dy = cuadro["pelota_y"] * ESCALA - blanco.world_y
            d = math.hypot(dx, dy) or 1.0
            pupila.x, pupila.y = 0.25 * dx / d, 0.25 * dy / d
            blanco.scale_y = 0.32 * (0.25 if cara == "feliz" else 1.0)
            blanco.rotation_z = 0
        if cara == "triste":
            jugador["ojos"][0][0].rotation_z, jugador["ojos"][1][0].rotation_z = -20, 20


def _crear_app(ursina, sin_ventana):
    from panda3d.core import loadPrcFileData
    loadPrcFileData("", "win-size 1280 720")
    if sin_ventana and not os.environ.get("DISPLAY"):
        # Sin pantalla: se dibuja en memoria (necesita OpenGL sin ventana).
        # En Linux sin pantalla también sirve: xvfb-run python ver3d.py ... --captura
        loadPrcFileData("", "window-type offscreen")
    app = ursina.Ursina(title="Tenis evolutivo — visor 3D", borderless=False, development_mode=False)
    ursina.window.color = ursina.color.rgb(0.75, 0.86, 0.95)
    ursina.DirectionalLight(rotation=(45, -30, 0), shadows=False)
    ursina.AmbientLight(color=ursina.color.rgba(0.6, 0.6, 0.6, 1))
    return app


def _camara(ursina, cancha):
    centro = cancha["ancho"] * ESCALA / 2
    pivote = ursina.EditorCamera(rotation_speed=120, panning_speed=0)
    pivote.position = (centro, 1.0, 0)
    pivote.rotation = (22, -28, 0)      # un poco de costado: así la red no se ve de canto
    ursina.camera.z = -13
    ursina.camera.fov = 50
    return pivote


def guardar_captura(g, t, ruta):
    """Dibuja el instante t en una imagen sin abrir ventana (necesita OpenGL)."""
    import ursina
    app = _crear_app(ursina, sin_ventana=True)
    escena = Escena3D(ursina, g)
    _camara(ursina, g["cancha"])
    escena.mostrar(t)
    for _ in range(3):           # unos cuadros para que todo quede dibujado
        app.step()
    from panda3d.core import Filename
    ursina.application.base.win.saveScreenshot(Filename.fromOsSpecific(ruta))


def reproducir(g, lento=False):
    import ursina
    app = _crear_app(ursina, sin_ventana=False)
    escena = Escena3D(ursina, g)
    pivote = _camara(ursina, g["cancha"])
    duracion = len(g["cuadros"]) * g["dt_cuadro"]
    estado = {"t": 0.0, "i": VELOCIDADES.index(0.5 if lento else 1.0), "pausa": False, "girar": False}

    def update():
        if not estado["pausa"]:
            estado["t"] = min(duracion, estado["t"] + ursina.time.dt * VELOCIDADES[estado["i"]])
        if estado["girar"]:
            pivote.rotation_y += VELOCIDAD_GIRO * ursina.time.dt
        escena.mostrar(estado["t"], VELOCIDADES[estado["i"]], estado["pausa"])

    def input(tecla):
        if tecla == "space":
            estado["pausa"] = not estado["pausa"]
        elif tecla == "r":
            estado["t"] = 0.0
        elif tecla == "g":
            estado["girar"] = not estado["girar"]
        elif tecla == "up arrow":
            estado["i"] = min(len(VELOCIDADES) - 1, estado["i"] + 1)
        elif tecla == "down arrow":
            estado["i"] = max(0, estado["i"] - 1)
        elif tecla == "escape":
            sys.exit()

    # Ursina busca funciones llamadas update e input en el módulo principal.
    modulo = sys.modules["__main__"]
    modulo.update, modulo.input = update, input
    app.run()


def _principal():
    parser = argparse.ArgumentParser(description="Reproduce una grabación en 3D.")
    parser.add_argument("ruta", help="archivo .json de grabar.py")
    parser.add_argument("--lento", action="store_true", help="empezar en cámara lenta")
    parser.add_argument("--captura", metavar="PNG", help="guardar una imagen en vez de abrir ventana")
    parser.add_argument("--t", type=float, default=0.0, help="instante de la captura (segundos)")
    args = parser.parse_args()
    g = grabar.cargar_grabacion(args.ruta)
    if args.captura:
        guardar_captura(g, args.t, args.captura)
        print(f"Captura guardada en {args.captura}")
    else:
        reproducir(g, args.lento)


if __name__ == "__main__":
    _principal()
