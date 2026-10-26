"""
ver2d.py — Visor 2D de grabaciones (pygame).

Solo lee archivos de grabación (grabar.py): NUNCA importa la física. Así el
visor no frena el entrenamiento y se puede ver una grabación en cualquier
computadora, aunque cambie la física después.

Todo lo "vistoso" (ojos, gestos, estelas, destellos) se calcula a partir de
la grabación y del instante t: no cambia nada del juego. Por ejemplo, los
ojos miran a la pelota porque el visor conoce su posición en ese cuadro, y un
cubo sonríe si los eventos dicen que acaba de ganar un punto.

Uso:
    python ver2d.py grabaciones/demo.json
    python ver2d.py grabaciones/demo.json --captura cuadro.png --t 5.0   (sin ventana)

Teclas: espacio = pausa, flechas izquierda/derecha = retroceder/avanzar 1 s,
        flechas arriba/abajo = más rápido/lento, R = reiniciar, Esc = salir.
"""

import argparse
import math
import os

import grabar

# --- Ventana y cámara (solo del visor; no son parámetros del experimento) ---
ANCHO_VENTANA = 1280
ALTO_VENTANA = 520
ALTO_SUELO_PX = 70           # franja de cancha "en profundidad" bajo y = 0
# Cámara que sigue la acción: encuadra a los dos jugadores y la pelota, con
# este margen, y nunca muestra menos que ANCHO_MINIMO de mundo. El encuadre se
# suaviza promediando SUAVIZADO_CAMARA cuadros a cada lado, para que no tiemble.
MARGEN_CAMARA = 120.0
ANCHO_MINIMO_CAMARA = 1100.0
ALTO_MINIMO_VISIBLE = 380.0  # al menos esta altura del mundo debe caber en pantalla
SUAVIZADO_CAMARA = 45
FPS = 60
VELOCIDADES = (0.25, 0.5, 1.0, 2.0, 4.0)

# --- Colores ---
CIELO_ARRIBA = (120, 180, 235)
CIELO_ABAJO = (215, 236, 250)
COLINAS = ((150, 200, 170), (125, 182, 150))
NUBE = (255, 255, 255, 170)
CESPED = ((74, 150, 86), (82, 161, 94))     # franjas alternadas, como césped cortado
FUERA = (178, 112, 78)                       # zona fuera de la cancha (tierra batida)
LINEA = (250, 250, 245)
RED_POSTE = (70, 70, 75)
RED_MALLA = (40, 40, 45)
RED_CINTA = (250, 250, 250)
TECHO = (200, 90, 90)
COLOR_JUGADOR = ((42, 120, 214), (235, 104, 52))   # izquierda azul, derecha naranja
MANGO = (90, 60, 40)
CUERDAS = (235, 235, 220)
PELOTA = (215, 230, 60)
PELOTA_COSTURA = (250, 250, 240)
SOMBRA = (20, 50, 25, 90)
OJO_BLANCO = (255, 255, 255)
OJO_PUPILA = (25, 25, 35)
PANEL = (255, 255, 255, 215)
TEXTO = (30, 30, 35)
TEXTO_SUAVE = (90, 90, 100)

# --- Efectos (en segundos o en cuadros) ---
DURACION_GESTO = 1.6         # cuánto dura la cara feliz o triste después de un punto
DURACION_AVISO = 2.2         # cuánto se muestra el aviso "punto para..."
DURACION_BOTE = 0.35         # anillo de polvo al botar
DURACION_DESTELLO = 0.22     # destello al golpear
PERIODO_PARPADEO = (3.3, 4.1)   # cada jugador parpadea con su propio ritmo
DURACION_PARPADEO = 0.12
LARGO_ESTELA = 10            # cuadros de estela de la pelota
FANTASMAS_RAQUETA = (2, 4, 6)   # cuadros atrás de las "raquetas fantasma" durante un golpe
GIRO_MINIMO_FANTASMA = 0.08  # radianes entre cuadros para considerar que está golpeando

MOTIVOS = {
    "doble_bote": "{perdedor} no llegó a la pelota",
    "bote_propio": "{perdedor} la tiró a la red o a su campo",
    "fuera": "{perdedor} la tiró fuera",
    "techo": "{perdedor} la tiró por encima del techo",
}


class Camara:
    """
    Convierte coordenadas del mundo (y hacia arriba) a píxeles (y hacia abajo).
    Muestra el tramo de x entre x_min y x_max (si la altura no alcanza, se
    ensancha para llenar la ventana).
    """

    def __init__(self, x_min, x_max):
        alto_util = ALTO_VENTANA - ALTO_SUELO_PX
        self.escala = min(ANCHO_VENTANA / (x_max - x_min), alto_util / ALTO_MINIMO_VISIBLE)
        centro = (x_min + x_max) / 2
        self.x_min = centro - ANCHO_VENTANA / (2 * self.escala)
        self.y_suelo_px = ALTO_VENTANA - ALTO_SUELO_PX

    def punto(self, x, y):
        return (int((x - self.x_min) * self.escala), int(self.y_suelo_px - y * self.escala))

    def a_mundo_x(self, px):
        return self.x_min + px / self.escala

    def largo(self, d):
        return max(1, int(d * self.escala))


def encuadre_crudo(c):
    """El tramo (x_min, x_max) que encuadra a los dos jugadores y la pelota en un cuadro."""
    xs = (c["izq_x"], c["der_x"], c["pelota_x"])
    lo, hi = min(xs) - MARGEN_CAMARA, max(xs) + MARGEN_CAMARA
    falta = ANCHO_MINIMO_CAMARA - (hi - lo)
    if falta > 0:
        lo, hi = lo - falta / 2, hi + falta / 2
    return lo, hi


def encuadres(g):
    """
    Para cada cuadro, el tramo (x_min, x_max) que debe mostrar la cámara:
    los dos jugadores y la pelota con margen, suavizado con un promedio móvil
    (promediar varios cuadros vecinos quita los saltos bruscos).
    """
    crudos = [encuadre_crudo(grabar.cuadro_como_dict(g, i)) for i in range(len(g["cuadros"]))]
    suaves = []
    for i in range(len(crudos)):
        vecinos = crudos[max(0, i - SUAVIZADO_CAMARA): i + SUAVIZADO_CAMARA + 1]
        suaves.append((sum(v[0] for v in vecinos) / len(vecinos),
                       sum(v[1] for v in vecinos) / len(vecinos)))
    return suaves


# --- Lo que se calcula de la grabación (sin dibujar nada) ---

def marcador_hasta(eventos, t):
    """Puntos ganados por cada lado hasta el instante t (se calcula de los eventos)."""
    ganados = [0, 0]
    for ev in eventos:
        if ev["t"] > t:
            break
        if ev["tipo"] == "punto" and ev["ganador"] is not None:
            ganados[ev["ganador"]] += 1
    return ganados


def ultimo_punto(eventos, t):
    """El último evento PUNTO hasta t (o None)."""
    ultimo = None
    for ev in eventos:
        if ev["t"] > t:
            break
        if ev["tipo"] == "punto":
            ultimo = ev
    return ultimo


def eventos_recientes(eventos, t, tipo, duracion):
    """Eventos de un tipo ocurridos en los últimos `duracion` segundos, con su edad."""
    return [(ev, t - ev["t"]) for ev in eventos
            if ev["tipo"] == tipo and 0.0 <= t - ev["t"] <= duracion]


def gesto(eventos, t, lado):
    """'feliz', 'triste' o 'normal' según si el jugador acaba de ganar o perder un punto."""
    ev = ultimo_punto(eventos, t)
    if ev is None or ev["ganador"] is None or t - ev["t"] > DURACION_GESTO:
        return "normal"
    return "feliz" if ev["ganador"] == lado else "triste"


def esta_parpadeando(t, lado):
    periodo = PERIODO_PARPADEO[lado]
    return (t + 0.7 * lado) % periodo < DURACION_PARPADEO


def texto_aviso(ultimo, nombres):
    if ultimo["ganador"] is None:
        return "Punto anulado: se agotó el tiempo"
    ganador, perdedor = nombres[ultimo["ganador"]], nombres[1 - ultimo["ganador"]]
    detalle = MOTIVOS.get(ultimo["motivo"], ultimo["motivo"]).format(perdedor=perdedor)
    return f"¡Punto para {ganador}!  {detalle}  ·  {ultimo['golpes_validos']} golpes válidos"


def indice_cuadro(g, t):
    return max(0, min(len(g["cuadros"]) - 1, int(round(t / g["dt_cuadro"])) - 1))


def mezclar(color, otro, f):
    """Mezcla dos colores RGB: f = 0 da `color`, f = 1 da `otro`."""
    return tuple(int(a + (b - a) * f) for a, b in zip(color, otro))


# --- La escena ---

class Escena:
    """Todo lo necesario para dibujar una grabación: cámara, letras y fondo."""

    def __init__(self, pygame, g, en_vivo=False):
        """
        en_vivo=True: la grabación se va llenando mientras se juega (jugar.py),
        así que la cámara no puede mirar el futuro: se suaviza hacia atrás.
        """
        import pygame.gfxdraw
        self.pg = pygame
        self.gfx = pygame.gfxdraw
        self.g = g
        self.cancha = g["cancha"]
        self.en_vivo = en_vivo
        self.encuadres = None if en_vivo else encuadres(g)
        self._encuadre_suave = None
        self.cam = Camara(0.0, self.cancha["ancho"])
        self.nombres = g["meta"].get("jugadores", ["izquierda", "derecha"])
        self.fuente = pygame.font.Font(None, 22)
        self.fuente_nombre = pygame.font.Font(None, 26)
        self.fuente_marcador = pygame.font.Font(None, 46)
        self.fondo = self._pintar_fondo()
        self.capa = pygame.Surface((ANCHO_VENTANA, ALTO_VENTANA), pygame.SRCALPHA)

    # --- Fondo: cielo, nubes y colinas se pintan una sola vez; la cancha, la
    # red y el techo se mueven con la cámara y se pintan en cada cuadro. ---

    def _pintar_fondo(self):
        pg = self.pg
        fondo = pg.Surface((ANCHO_VENTANA, ALTO_VENTANA))
        for y in range(self.cam.y_suelo_px):          # degradado del cielo
            f = y / self.cam.y_suelo_px
            pg.draw.line(fondo, mezclar(CIELO_ARRIBA, CIELO_ABAJO, f), (0, y), (ANCHO_VENTANA, y))
        self._pintar_nubes(fondo)
        self._pintar_colinas(fondo)
        return fondo

    def _pintar_nubes(self, fondo):
        pg = self.pg
        nubes = pg.Surface((ANCHO_VENTANA, ALTO_VENTANA), pg.SRCALPHA)
        for fx, fy, tam in ((0.12, 0.16, 1.0), (0.38, 0.09, 0.7), (0.63, 0.2, 1.2), (0.88, 0.12, 0.8)):
            cx, cy = int(fx * ANCHO_VENTANA), int(fy * ALTO_VENTANA)
            for dx, dy, r in ((-30, 6, 22), (0, 0, 30), (32, 5, 24), (60, 10, 16)):
                pg.draw.circle(nubes, NUBE, (cx + int(dx * tam), cy + int(dy * tam)), int(r * tam))
        fondo.blit(nubes, (0, 0))

    def _pintar_colinas(self, fondo):
        y0 = self.cam.y_suelo_px
        for i, color in enumerate(COLINAS):
            altura, onda, fase = 55 - 22 * i, 0.006 + 0.003 * i, 1.7 * i
            puntos = [(0, y0)]
            for x in range(0, ANCHO_VENTANA + 20, 20):
                puntos.append((x, y0 - altura - 18 * math.sin(x * onda + fase)))
            puntos.append((ANCHO_VENTANA, y0))
            self.pg.draw.polygon(fondo, color, puntos)

    def _pintar_suelo(self, fondo):
        pg, cam = self.pg, self.cam
        y0 = cam.y_suelo_px
        pg.draw.rect(fondo, FUERA, (0, y0, ANCHO_VENTANA, ALTO_SUELO_PX))
        izq, _ = cam.punto(0, 0)
        der, _ = cam.punto(self.cancha["ancho"], 0)
        franjas = 10                                   # franjas fijas en el MUNDO (se mueven con la cámara)
        ancho_franja = self.cancha["ancho"] / franjas
        for i in range(franjas):
            x1, _ = cam.punto(i * ancho_franja, 0)
            x2, _ = cam.punto((i + 1) * ancho_franja, 0)
            pg.draw.rect(fondo, CESPED[i % 2], (x1, y0, x2 - x1 + 1, ALTO_SUELO_PX))
        pg.draw.line(fondo, LINEA, (izq, y0), (der, y0), 3)             # línea del suelo
        for x in (izq, der):                                            # líneas de fondo
            pg.draw.line(fondo, LINEA, (x, y0), (x, ALTO_VENTANA), 3)

    def _pintar_red(self, fondo):
        pg, cam = self.pg, self.cam
        x, y_abajo = cam.punto(self.cancha["x_red"], 0)
        _, y_arriba = cam.punto(0, self.cancha["alto_red"])
        pg.draw.rect(fondo, RED_POSTE, (x - 2, y_arriba - 4, 5, y_abajo - y_arriba + 4 + ALTO_SUELO_PX // 3))
        malla = pg.Rect(x - 5, y_arriba, 11, y_abajo - y_arriba)
        for y in range(malla.top, malla.bottom, 4):                     # cuadriculado
            pg.draw.line(fondo, RED_MALLA, (malla.left, y), (malla.right, y), 1)
        for xx in range(malla.left, malla.right + 1, 4):
            pg.draw.line(fondo, RED_MALLA, (xx, malla.top), (xx, malla.bottom), 1)
        pg.draw.rect(fondo, RED_CINTA, (x - 6, y_arriba - 3, 13, 4))

    def _pintar_techo(self, fondo):
        pg, cam = self.pg, self.cam
        _, y = cam.punto(0, self.cancha["techo"])
        if y < 0:
            return                                                      # el techo quedó fuera de cuadro
        for x in range(0, ANCHO_VENTANA, 24):                           # línea punteada
            pg.draw.line(fondo, TECHO, (x, y), (x + 12, y), 2)
        fondo.blit(self.fuente.render("techo", True, TECHO), (8, y - 18))

    # --- Cada cuadro ---

    def dibujar(self, pantalla, t, velocidad=1.0, pausado=False):
        g = self.g
        i = indice_cuadro(g, t)
        cuadro = grabar.cuadro_como_dict(g, i)
        self.cam = Camara(*self._encuadre(i, cuadro))
        pantalla.blit(self.fondo, (0, 0))
        self._pintar_suelo(pantalla)
        self._pintar_red(pantalla)
        self._pintar_techo(pantalla)
        self.capa.fill((0, 0, 0, 0))
        self._sombras(cuadro)
        self._efectos(t)
        self._estela_pelota(i)
        pantalla.blit(self.capa, (0, 0))
        for lado, prefijo in enumerate(("izq", "der")):
            self._raqueta(pantalla, i, prefijo, lado)
            self._jugador(pantalla, cuadro, prefijo, lado, t)
        self._pelota(pantalla, cuadro["pelota_x"], cuadro["pelota_y"], t)
        self._marcador(pantalla, t, velocidad, pausado)

    def _encuadre(self, i, cuadro):
        if not self.en_vivo:
            return self.encuadres[i]
        # En vivo: cada cuadro la cámara se acerca un poco al encuadre ideal
        # (suavizado exponencial: no necesita conocer los cuadros futuros).
        objetivo = encuadre_crudo(cuadro)
        if self._encuadre_suave is None:
            self._encuadre_suave = objetivo
        f = 2.0 / (SUAVIZADO_CAMARA + 1)
        self._encuadre_suave = tuple(a + (b - a) * f for a, b in zip(self._encuadre_suave, objetivo))
        return self._encuadre_suave

    def _sombras(self, cuadro):
        """Sombras en el suelo: más chicas y claras cuanto más alto está el objeto."""
        tam = self.cancha["tamano_jugador"]
        objetos = [(cuadro["pelota_x"], cuadro["pelota_y"], 2.2 * self.cancha["radio_pelota"])]
        objetos += [(cuadro[f"{p}_x"], cuadro[f"{p}_y"] - tam / 2, 1.2 * tam) for p in ("izq", "der")]
        for x, altura, ancho in objetos:
            f = max(0.3, 1.0 - altura / 500.0)
            sx, sy = self.cam.punto(x, 0)
            w, h = int(self.cam.largo(ancho) * f), max(3, int(8 * f))
            color = SOMBRA[:3] + (int(SOMBRA[3] * f),)
            self.pg.draw.ellipse(self.capa, color, (sx - w // 2, sy - h // 2 + 2, w, h))

    def _efectos(self, t):
        cam = self.cam
        for ev, edad in eventos_recientes(self.g["eventos"], t, "bote", DURACION_BOTE):
            f = edad / DURACION_BOTE                                  # anillo de polvo
            x, y = cam.punto(ev["x"], 0)
            r = int(self.cam.escala * (10 + 35 * f))
            color = (255, 255, 255, int(200 * (1 - f))) if ev["valido"] else (255, 230, 200, int(160 * (1 - f)))
            self.pg.draw.ellipse(self.capa, color, (x - r, y - r // 3, 2 * r, 2 * (r // 3) + 1), 2)
        for ev, edad in eventos_recientes(self.g["eventos"], t, "golpe", DURACION_DESTELLO):
            f = edad / DURACION_DESTELLO                              # destello en estrella
            x, y = cam.punto(ev["x"], ev["y"])
            color = mezclar(COLOR_JUGADOR[ev["jugador"]], (255, 255, 255), 0.4) + (int(255 * (1 - f)),)
            for k in range(8):
                a = k * math.pi / 4
                r1, r2 = 6 + 10 * f, 12 + 18 * f
                self.pg.draw.line(self.capa, color, (x + r1 * math.cos(a), y + r1 * math.sin(a)),
                                  (x + r2 * math.cos(a), y + r2 * math.sin(a)), 3)

    def _estela_pelota(self, i):
        g, cam = self.g, self.cam
        radio = cam.largo(self.cancha["radio_pelota"])
        for k in range(LARGO_ESTELA, 0, -1):
            j = i - k
            if j < 0:
                continue
            c = grabar.cuadro_como_dict(g, j)
            f = 1 - k / (LARGO_ESTELA + 1)
            self.pg.draw.circle(self.capa, PELOTA + (int(120 * f),),
                                cam.punto(c["pelota_x"], c["pelota_y"]), max(1, int(radio * f)))

    def _circulo(self, superficie, color, centro, radio):
        """Círculo suavizado (antialiasing) con gfxdraw."""
        x, y = int(centro[0]), int(centro[1])
        self.gfx.filled_circle(superficie, x, y, radio, color)
        self.gfx.aacircle(superficie, x, y, radio, color)

    def _pelota(self, pantalla, x, y, t):
        centro = self.cam.punto(x, y)
        r = max(4, self.cam.largo(self.cancha["radio_pelota"]))
        self._circulo(pantalla, PELOTA, centro, r)
        # Costura de pelota de tenis: un arco que gira con el tiempo.
        giro = t * 8.0
        rect = self.pg.Rect(centro[0] - r + 1, centro[1] - r + 1, 2 * r - 2, 2 * r - 2)
        self.pg.draw.arc(pantalla, PELOTA_COSTURA, rect, giro, giro + 2.2, 1)
        self.pg.draw.arc(pantalla, PELOTA_COSTURA, rect, giro + math.pi, giro + math.pi + 2.2, 1)
        self._circulo(pantalla, (255, 255, 230), (centro[0] - r // 3, centro[1] - r // 3), max(1, r // 4))

    def _raqueta(self, pantalla, i, prefijo, lado):
        """Raqueta: mango oscuro y cabeza ovalada con cuerdas, del color del jugador."""
        g = self.g
        actual = grabar.cuadro_como_dict(g, i)
        for atras in FANTASMAS_RAQUETA:                                   # estela de un golpe
            if i - atras < 0:
                continue
            viejo = grabar.cuadro_como_dict(g, i - atras)
            giro = abs(actual[f"{prefijo}_raqueta_angulo"] - viejo[f"{prefijo}_raqueta_angulo"])
            if GIRO_MINIMO_FANTASMA < giro < math.pi:
                alfa = int(110 * (1 - atras / (FANTASMAS_RAQUETA[-1] + 2)))
                self._forma_raqueta(pantalla, viejo, prefijo, lado, alfa)
        self._forma_raqueta(pantalla, actual, prefijo, lado, 255)

    def _forma_raqueta(self, superficie, cuadro, prefijo, lado, alfa):
        largo, grosor = self.cancha["largo_raqueta"], self.cancha["grosor_raqueta"]
        cx, cy = cuadro[f"{prefijo}_raqueta_x"], cuadro[f"{prefijo}_raqueta_y"]
        a = cuadro[f"{prefijo}_raqueta_angulo"]
        ux, uy = math.cos(a), math.sin(a)                     # dirección mango → punta
        mango = (cx - ux * largo / 2, cy - uy * largo / 2)
        cuello = (cx - ux * largo * 0.1, cy - uy * largo * 0.1)
        centro_cabeza = (cx + ux * largo * 0.2, cy + uy * largo * 0.2)
        marco = mezclar(COLOR_JUGADOR[lado], (0, 0, 0), 0.35)
        if alfa == 255:
            # Las raquetas "fantasma" (alfa < 255) son solo la cabeza: gfxdraw
            # sabe mezclar colores transparentes, pygame.draw.line no.
            p_mango, p_cuello = self.cam.punto(*mango), self.cam.punto(*cuello)
            ancho_mango = max(2, self.cam.largo(grosor * 0.55))
            self.pg.draw.line(superficie, MANGO, p_mango, p_cuello, ancho_mango)
        # Cabeza: un óvalo girado, aproximado con un polígono de 20 lados.
        semieje_largo, semieje_corto = largo * 0.3, grosor * 0.8
        puntos = []
        for k in range(20):
            th = 2 * math.pi * k / 20
            px = semieje_largo * math.cos(th)
            py = semieje_corto * math.sin(th)
            puntos.append(self.cam.punto(centro_cabeza[0] + px * ux - py * uy,
                                         centro_cabeza[1] + px * uy + py * ux))
        self.gfx.filled_polygon(superficie, puntos, CUERDAS + (alfa,))
        self.gfx.aapolygon(superficie, puntos, marco + (alfa,))
        if alfa == 255:
            self.pg.draw.polygon(superficie, marco, puntos, 2)
            self.pg.draw.line(superficie, marco, puntos[0], puntos[10], 1)   # cuerda a lo largo

    def _jugador(self, pantalla, cuadro, prefijo, lado, t):
        pg, cam = self.pg, self.cam
        tam = self.cancha["tamano_jugador"]
        x, y = cuadro[f"{prefijo}_x"], cuadro[f"{prefijo}_y"]
        izq, arriba = cam.punto(x - tam / 2, y + tam / 2)
        s = cam.largo(tam)
        cuerpo = pg.Rect(izq, arriba, s, s)
        color = COLOR_JUGADOR[lado]
        radio_borde = max(3, s // 5)
        pg.draw.rect(pantalla, color, cuerpo, border_radius=radio_borde)
        brillo = pg.Rect(izq + 3, arriba + 3, s - 6, s // 3)
        pg.draw.rect(pantalla, mezclar(color, (255, 255, 255), 0.3), brillo, border_radius=radio_borde)
        pg.draw.rect(pantalla, mezclar(color, (0, 0, 0), 0.4), cuerpo, 2, border_radius=radio_borde)
        self._cara(pantalla, cuerpo, lado, cuadro, gesto(self.g["eventos"], t, lado),
                   esta_parpadeando(t, lado))

    def _cara(self, pantalla, cuerpo, lado, cuadro, cara, parpadeo):
        """
        Solo ojos: miran a la pelota y muestran el gesto (feliz = ojos
        cerrados sonriendo; triste = cejas caídas).
        """
        pg = self.pg
        s = cuerpo.width
        hacia_red = 1 if lado == 0 else -1
        cx = cuerpo.centerx + hacia_red * s * 0.12           # la cara mira hacia la red
        y_ojos = cuerpo.top + s * 0.48
        r_ojo, r_pupila = max(3, int(s * 0.17)), max(2, int(s * 0.08))
        pelota = self.cam.punto(cuadro["pelota_x"], cuadro["pelota_y"])
        for desplazamiento in (-0.18, 0.18):
            ojo = (cx + desplazamiento * s, y_ojos)
            if cara == "feliz":                              # ojos cerrados sonriendo: ^ ^
                rect = pg.Rect(ojo[0] - r_ojo, ojo[1] - r_ojo // 2, 2 * r_ojo, 2 * r_ojo)
                pg.draw.arc(pantalla, OJO_PUPILA, rect, 0.2, math.pi - 0.2, 2)
                continue
            if parpadeo:
                pg.draw.line(pantalla, OJO_PUPILA, (ojo[0] - r_ojo, ojo[1]), (ojo[0] + r_ojo, ojo[1]), 2)
                continue
            self._circulo(pantalla, OJO_BLANCO, ojo, r_ojo)
            dx, dy = pelota[0] - ojo[0], pelota[1] - ojo[1]
            d = math.hypot(dx, dy) or 1.0
            alcance = r_ojo - r_pupila - 0.5                 # la pupila no sale del ojo
            self._circulo(pantalla, OJO_PUPILA, (ojo[0] + dx / d * alcance, ojo[1] + dy / d * alcance),
                          r_pupila)
            if cara == "triste":                             # cejas caídas hacia afuera
                afuera = 1 if desplazamiento > 0 else -1
                y_ceja = ojo[1] - r_ojo - 2
                pg.draw.line(pantalla, OJO_PUPILA, (ojo[0] - afuera * r_ojo * 0.2, y_ceja - 2),
                             (ojo[0] + afuera * r_ojo, y_ceja + 1), 2)

    def _marcador(self, pantalla, t, velocidad, pausado):
        pg = self.pg
        ganados = marcador_hasta(self.g["eventos"], t)
        puntos = self.fuente_marcador.render(f"{ganados[0]}  –  {ganados[1]}", True, TEXTO)
        nombres = [self.fuente_nombre.render(n, True, COLOR_JUGADOR[i]) for i, n in enumerate(self.nombres)]
        estado = f"t = {t:5.1f} s   ·   velocidad ×{velocidad}" + ("   ·   PAUSA" if pausado else "")
        linea = self.fuente.render(estado, True, TEXTO_SUAVE)
        # El panel se agranda según el largo de los nombres (simétrico al centro).
        mitad = puntos.get_width() // 2 + 24 + max(n.get_width() for n in nombres) + 20
        panel = pg.Surface((2 * mitad, 74), pg.SRCALPHA)
        pg.draw.rect(panel, PANEL, panel.get_rect(), border_radius=14)
        panel.blit(puntos, (mitad - puntos.get_width() // 2, 8))
        panel.blit(nombres[0], (mitad - puntos.get_width() // 2 - 24 - nombres[0].get_width(), 18))
        panel.blit(nombres[1], (mitad + puntos.get_width() // 2 + 24, 18))
        panel.blit(linea, (mitad - linea.get_width() // 2, 50))
        pantalla.blit(panel, (ANCHO_VENTANA // 2 - mitad, 10))
        self._aviso(pantalla, t)
        ayuda = self.fuente.render("espacio: pausa   flechas izq/der: saltar 1 s   "
                                   "arriba/abajo: velocidad   R: reiniciar   Esc: salir", True, (245, 245, 245))
        franja = pg.Surface((ayuda.get_width() + 16, ayuda.get_height() + 6), pg.SRCALPHA)
        pg.draw.rect(franja, (0, 0, 0, 90), franja.get_rect(), border_radius=6)
        pantalla.blit(franja, (6, ALTO_VENTANA - franja.get_height() - 4))
        pantalla.blit(ayuda, (14, ALTO_VENTANA - franja.get_height() - 1))

    def _aviso(self, pantalla, t):
        ultimo = ultimo_punto(self.g["eventos"], t)
        if ultimo is None or t - ultimo["t"] > DURACION_AVISO:
            return
        pg = self.pg
        texto = self.fuente_nombre.render(texto_aviso(ultimo, self.nombres), True, (255, 255, 255))
        caja = pg.Rect(0, 0, texto.get_width() + 28, texto.get_height() + 14)
        caja.center = (ANCHO_VENTANA // 2, 106)
        fondo = pg.Surface(caja.size, pg.SRCALPHA)
        color = (90, 90, 100) if ultimo["ganador"] is None else COLOR_JUGADOR[ultimo["ganador"]]
        pg.draw.rect(fondo, color + (225,), fondo.get_rect(), border_radius=10)
        pantalla.blit(fondo, caja.topleft)
        pantalla.blit(texto, (caja.left + 14, caja.top + 7))


# --- Uso ---

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
    Escena(pygame, g).dibujar(pantalla, t)
    pygame.image.save(pantalla, ruta)
    pygame.quit()


def reproducir(g):
    import pygame
    _iniciar(pygame)
    pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
    pygame.display.set_caption("Tenis evolutivo — visor 2D")
    reloj = pygame.time.Clock()
    escena = Escena(pygame, g)
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
        escena.dibujar(pantalla, t, VELOCIDADES[i_velocidad], pausado)
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
