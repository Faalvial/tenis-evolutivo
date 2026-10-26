"""
ver2d.py — Visor 2D de grabaciones (pygame), para depurar.

Solo lee archivos de grabación (grabar.py): NUNCA importa la física. Así el
visor no frena el entrenamiento y se puede ver una grabación en cualquier
computadora, aunque cambie la física después.

Uso:
    python ver2d.py grabaciones/demo.json
    python ver2d.py grabaciones/demo.json --captura cuadro.png --t 5.0   (sin ventana)

Teclas: espacio = pausa, ← → = retroceder/avanzar 1 s, ↑ ↓ = más rápido/lento,
        R = reiniciar, Esc = salir.
"""

import argparse
import math
import os

import grabar

# --- Aspecto (solo del visor; no son parámetros del experimento) ---
ANCHO_VENTANA = 1200
ALTO_VENTANA = 520
MARGEN_X = 400.0             # unidades del mundo visibles a cada lado de la cancha
ALTO_VISIBLE = 650.0         # unidades del mundo visibles hacia arriba
ALTO_SUELO_PX = 50           # franja de suelo bajo y = 0
FPS = 60
VELOCIDADES = (0.25, 0.5, 1.0, 2.0, 4.0)

COLOR_CIELO = (225, 236, 245)
COLOR_SUELO = (90, 150, 90)
COLOR_FUERA = (120, 120, 120)
COLOR_LINEA = (250, 250, 250)
COLOR_RED = (40, 40, 40)
COLOR_TECHO = (200, 120, 120)
COLOR_JUGADOR = ((42, 120, 214), (235, 104, 52))   # izquierda azul, derecha naranja
COLOR_RAQUETA = (60, 60, 60)
COLOR_PELOTA = (230, 220, 40)
COLOR_SOMBRA = (60, 110, 60)
COLOR_TEXTO = (20, 20, 20)


class Camara:
    """Convierte coordenadas del mundo (y hacia arriba) a píxeles (y hacia abajo)."""

    def __init__(self, cancha):
        self.x_min = -MARGEN_X
        ancho_mundo = cancha["ancho"] + 2 * MARGEN_X
        self.escala = min(ANCHO_VENTANA / ancho_mundo,
                          (ALTO_VENTANA - ALTO_SUELO_PX) / ALTO_VISIBLE)
        self.y_suelo_px = ALTO_VENTANA - ALTO_SUELO_PX

    def punto(self, x, y):
        return (int((x - self.x_min) * self.escala), int(self.y_suelo_px - y * self.escala))

    def largo(self, d):
        return max(1, int(d * self.escala))


def marcador_hasta(eventos, t):
    """Puntos ganados por cada lado hasta el instante t (se calcula de los eventos)."""
    ganados = [0, 0]
    ultimo = ""
    for ev in eventos:
        if ev["t"] > t:
            break
        if ev["tipo"] == "punto":
            if ev["ganador"] is not None:
                ganados[ev["ganador"]] += 1
            ultimo = f"último punto: {ev['motivo']} ({ev['golpes_validos']} golpes válidos)"
    return ganados, ultimo


def dibujar_cancha(pantalla, pygame, cam, cancha):
    pantalla.fill(COLOR_CIELO)
    izq, _ = cam.punto(0, 0)
    der, _ = cam.punto(cancha["ancho"], 0)
    pygame.draw.rect(pantalla, COLOR_FUERA, (0, cam.y_suelo_px, ANCHO_VENTANA, ALTO_SUELO_PX))
    pygame.draw.rect(pantalla, COLOR_SUELO, (izq, cam.y_suelo_px, der - izq, ALTO_SUELO_PX))
    pygame.draw.line(pantalla, COLOR_LINEA, (izq, cam.y_suelo_px), (der, cam.y_suelo_px), 3)
    red_abajo = cam.punto(cancha["x_red"], 0)
    red_arriba = cam.punto(cancha["x_red"], cancha["alto_red"])
    pygame.draw.line(pantalla, COLOR_RED, red_abajo, red_arriba, 3)
    techo_izq = cam.punto(-MARGEN_X, cancha["techo"])
    techo_der = cam.punto(cancha["ancho"] + MARGEN_X, cancha["techo"])
    pygame.draw.line(pantalla, COLOR_TECHO, techo_izq, techo_der, 1)


def esquinas_raqueta(rx, ry, angulo, largo, grosor):
    """Las 4 esquinas del rectángulo de la raqueta (centro + ángulo) en el mundo."""
    c, s = math.cos(angulo), math.sin(angulo)
    puntos = []
    for dx, dy in ((-largo / 2, -grosor / 2), (largo / 2, -grosor / 2),
                   (largo / 2, grosor / 2), (-largo / 2, grosor / 2)):
        puntos.append((rx + dx * c - dy * s, ry + dx * s + dy * c))
    return puntos


def dibujar_cuadro(pantalla, pygame, cam, g, cuadro):
    cancha = g["cancha"]
    lado_cubo = cancha["tamano_jugador"]
    for i, prefijo in enumerate(("izq", "der")):
        x, y = cuadro[f"{prefijo}_x"], cuadro[f"{prefijo}_y"]
        esquina = cam.punto(x - lado_cubo / 2, y + lado_cubo / 2)
        lado_px = cam.largo(lado_cubo)
        pygame.draw.rect(pantalla, COLOR_JUGADOR[i], (*esquina, lado_px, lado_px))
        esquinas = esquinas_raqueta(cuadro[f"{prefijo}_raqueta_x"], cuadro[f"{prefijo}_raqueta_y"],
                                    cuadro[f"{prefijo}_raqueta_angulo"],
                                    cancha["largo_raqueta"], cancha["grosor_raqueta"])
        pygame.draw.polygon(pantalla, COLOR_RAQUETA, [cam.punto(*p) for p in esquinas])
    bx, by = cuadro["pelota_x"], cuadro["pelota_y"]
    # Sombra en el suelo: ayuda a ver la altura de la pelota.
    sx, sy = cam.punto(bx, 0)
    ancho_sombra = cam.largo(2 * cancha["radio_pelota"])
    pygame.draw.ellipse(pantalla, COLOR_SOMBRA, (sx - ancho_sombra // 2, sy - 3, ancho_sombra, 6))
    pygame.draw.circle(pantalla, COLOR_PELOTA, cam.punto(bx, by), cam.largo(cancha["radio_pelota"]))


def dibujar_textos(pantalla, fuente, g, t, velocidad, pausado):
    (izq, der), ultimo = marcador_hasta(g["eventos"], t)
    nombres = g["meta"].get("jugadores", ["izquierda", "derecha"])
    lineas = [f"{nombres[0]}  {izq}  -  {der}  {nombres[1]}",
              f"t = {t:5.1f} s   velocidad x{velocidad}" + ("   (pausa)" if pausado else ""),
              ultimo]
    for i, texto in enumerate(lineas):
        pantalla.blit(fuente.render(texto, True, COLOR_TEXTO), (10, 8 + 22 * i))


def indice_cuadro(g, t):
    return max(0, min(len(g["cuadros"]) - 1, int(round(t / g["dt_cuadro"])) - 1))


def _iniciar(pygame):
    # Solo pantalla y letras: pygame.init() también abre el sonido, que no
    # usamos y en algunas computadoras da avisos molestos.
    pygame.display.init()
    pygame.font.init()


def guardar_captura(g, t, ruta):
    """Dibuja el instante t en un archivo de imagen, sin abrir ventana."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame
    _iniciar(pygame)
    pantalla = pygame.Surface((ANCHO_VENTANA, ALTO_VENTANA))
    cam = Camara(g["cancha"])
    dibujar_cancha(pantalla, pygame, cam, g["cancha"])
    dibujar_cuadro(pantalla, pygame, cam, g, grabar.cuadro_como_dict(g, indice_cuadro(g, t)))
    dibujar_textos(pantalla, pygame.font.SysFont(None, 24), g, t, 1.0, False)
    pygame.image.save(pantalla, ruta)
    pygame.quit()


def reproducir(g):
    import pygame
    _iniciar(pygame)
    pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
    pygame.display.set_caption("Tenis evolutivo — visor 2D")
    reloj = pygame.time.Clock()
    fuente = pygame.font.SysFont(None, 24)
    cam = Camara(g["cancha"])
    duracion = len(g["cuadros"]) * g["dt_cuadro"]
    t, i_velocidad, pausado = 0.0, VELOCIDADES.index(1.0), False
    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                return
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
                if evento.key == pygame.K_SPACE:
                    pausado = not pausado
                elif evento.key == pygame.K_r:
                    t = 0.0
                elif evento.key == pygame.K_RIGHT:
                    t = min(duracion, t + 1.0)
                elif evento.key == pygame.K_LEFT:
                    t = max(0.0, t - 1.0)
                elif evento.key == pygame.K_UP:
                    i_velocidad = min(len(VELOCIDADES) - 1, i_velocidad + 1)
                elif evento.key == pygame.K_DOWN:
                    i_velocidad = max(0, i_velocidad - 1)
        if not pausado:
            t = min(duracion, t + VELOCIDADES[i_velocidad] / FPS)
        dibujar_cancha(pantalla, pygame, cam, g["cancha"])
        dibujar_cuadro(pantalla, pygame, cam, g, grabar.cuadro_como_dict(g, indice_cuadro(g, t)))
        dibujar_textos(pantalla, fuente, g, t, VELOCIDADES[i_velocidad], pausado)
        pygame.display.flip()
        reloj.tick(FPS)


def _principal():
    parser = argparse.ArgumentParser(description="Reproduce una grabación en 2D.")
    parser.add_argument("ruta", help="archivo .json de grabar.py")
    parser.add_argument("--captura", metavar="PNG", help="guardar una imagen en vez de abrir ventana")
    parser.add_argument("--t", type=float, default=0.0, help="instante de la captura (segundos)")
    args = parser.parse_args()
    g = grabar.cargar_grabacion(args.ruta)
    if args.captura:
        guardar_captura(g, args.t, args.captura)
        print(f"Captura guardada en {args.captura}")
    else:
        reproducir(g)


if __name__ == "__main__":
    _principal()
