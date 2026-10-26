"""
mundo.py — El espacio de física: cancha, red y pelota.

Usa pymunk, un motor de física 2D. Un motor de física hace por nosotros las
cuentas de Newton: cada paso de tiempo aplica la gravedad, mueve los cuerpos y
resuelve los choques (rebotes, fricción). Nosotros solo describimos QUÉ hay en
el mundo y le pedimos que avance.

Paredes invisibles: el plan proponía paredes que solo chocaran con los
jugadores. Las probamos en F1 y no sirven: como fijamos la velocidad del cubo
en cada paso, pymunk lo deja hundirse en la pared y hasta atravesarla. En su
lugar, después de cada paso, Jugador.mantener_en_su_campo() devuelve al
cubo a su mitad. Es más simple y no falla nunca.

Este módulo no sabe de reglas ni de puntos: solo ANOTA lo que tocó la pelota
(el suelo, la red, una raqueta) en la lista `contactos`. Quien decide qué
significa cada contacto es el árbitro (arbitro.py). Separarlos permite probar
las reglas sin física y la física sin reglas.
"""

import pymunk

import config

# Respuestas posibles de Jugador.al_tocar_pelota (definidas aquí y no en
# jugador.py para no crear una importación circular).
CONTACTO_GOLPE = "golpe"        # la pelota sale según el modelo de golpe
CONTACTO_FISICO = "fisico"      # rebote normal de pymunk (sin golpear)
CONTACTO_IGNORAR = "ignorar"    # ese golpe ya pegó: el contacto extra no cuenta

# --- Tipos de colisión ---
# pymunk llama a nuestras funciones cuando chocan dos formas de ciertos tipos.
# Los números en sí no importan; solo tienen que ser distintos.
TIPO_PELOTA = 1
TIPO_SUELO = 2
TIPO_RED = 3
TIPO_RAQUETA = (4, 5)      # raqueta del jugador 0 (izquierda) y del 1 (derecha)

# --- Categorías para los filtros de colisión ---
# Cada forma dice a qué categoría pertenece y con qué categorías choca (su
# "máscara"). Dos formas chocan solo si cada una está en la máscara de la otra.
# Así, por ejemplo, la pelota choca con la raqueta pero no con el cubo.
CAT_PELOTA = 0b000001
CAT_JUGADOR = 0b000010
CAT_RAQUETA = 0b000100
CAT_SUELO = 0b001000
CAT_RED = 0b010000

FILTRO_PELOTA = pymunk.ShapeFilter(categories=CAT_PELOTA,
                                   mask=CAT_SUELO | CAT_RED | CAT_RAQUETA)
FILTRO_SUELO = pymunk.ShapeFilter(categories=CAT_SUELO, mask=CAT_PELOTA | CAT_JUGADOR)
# La red solo choca con la pelota: a los jugadores los mantiene en su mitad
# Jugador.mantener_en_su_campo (ver más abajo por qué no usamos paredes).
FILTRO_RED = pymunk.ShapeFilter(categories=CAT_RED, mask=CAT_PELOTA)


class Mundo:
    """
    Contiene el espacio de pymunk y la pelota. Los jugadores los agrega
    jugador.py (cada Jugador se "inscribe" en un Mundo).

    Atributo importante:
    - contactos: lista de tuplas que se llena durante avanzar(). Ejemplos:
        ("bote", x)          la pelota tocó el suelo en x
        ("red",)             la pelota tocó la red
        ("toque", lado)      la pelota tocó la raqueta del jugador `lado`
      partido.py la lee y la vacía después de cada paso.
    """

    def __init__(self):
        self.espacio = pymunk.Space()
        self.espacio.gravity = (0.0, config.GRAVEDAD)
        self.contactos = []
        self.jugadores = {}      # lado -> Jugador; se llena con inscribir_jugador
        self._crear_suelo()
        self._crear_red()
        self.pelota = self._crear_pelota()
        self._registrar_choques()

    # --- Construcción ---

    def _crear_suelo(self):
        # Un cuerpo "estático" no se mueve nunca (masa infinita).
        suelo = pymunk.Segment(self.espacio.static_body,
                               (-config.LARGO_SUELO_FUERA, 0.0),
                               (config.ANCHO_CANCHA + config.LARGO_SUELO_FUERA, 0.0),
                               0.0)
        suelo.elasticity = 1.0   # la elasticidad real la pone la pelota (se multiplican)
        suelo.friction = 1.0
        suelo.collision_type = TIPO_SUELO
        suelo.filter = FILTRO_SUELO
        self.espacio.add(suelo)

    def _crear_red(self):
        red = pymunk.Segment(self.espacio.static_body,
                             (config.X_RED, 0.0), (config.X_RED, config.ALTO_RED), 1.0)
        red.elasticity = 0.3     # la red "amortigua": la pelota cae casi muerta
        red.friction = 0.5
        red.collision_type = TIPO_RED
        red.filter = FILTRO_RED
        self.espacio.add(red)

    def _crear_pelota(self):
        radio = config.RADIO_PELOTA
        cuerpo = pymunk.Body(config.MASA_PELOTA,
                             pymunk.moment_for_circle(config.MASA_PELOTA, 0, radio))
        cuerpo.velocity_func = _limitar_velocidad_pelota
        forma = pymunk.Circle(cuerpo, radio)
        forma.elasticity = config.ELASTICIDAD_PELOTA
        forma.friction = config.FRICCION_PELOTA
        forma.collision_type = TIPO_PELOTA
        forma.filter = FILTRO_PELOTA
        self.espacio.add(cuerpo, forma)
        return cuerpo

    def _registrar_choques(self):
        # "begin" se llama en el primer instante en que dos formas se tocan.
        # Por eso un bote se anota una vez, aunque la pelota quede apoyada.
        self.espacio.on_collision(TIPO_PELOTA, TIPO_SUELO, begin=self._al_tocar_suelo)
        self.espacio.on_collision(TIPO_PELOTA, TIPO_RED, begin=self._al_tocar_red)
        for lado, tipo in enumerate(TIPO_RAQUETA):
            self.espacio.on_collision(TIPO_PELOTA, tipo, begin=self._al_tocar_raqueta,
                                      data={"lado": lado})

    # --- Funciones que llama pymunk durante un choque ---

    def _al_tocar_suelo(self, choque, espacio, datos):
        self.contactos.append(("bote", self.pelota.position.x))

    def _al_tocar_red(self, choque, espacio, datos):
        self.contactos.append(("red",))

    def _al_tocar_raqueta(self, choque, espacio, datos):
        # El jugador decide si es un golpe (modelo de golpe), un rebote
        # físico normal o un contacto repetido que se ignora.
        lado = datos["lado"]
        resultado = self.jugadores[lado].al_tocar_pelota(self.pelota)
        if resultado != CONTACTO_FISICO:
            # process_collision = False le dice a pymunk "no resuelvas este
            # choque": la velocidad ya la puso el jugador (o no debe cambiar).
            choque.process_collision = False
        if resultado != CONTACTO_IGNORAR:
            self.contactos.append(("toque", lado))

    # --- Uso ---

    def inscribir_jugador(self, jugador):
        """Lo llama Jugador al crearse, para que el mundo le avise de sus contactos."""
        self.jugadores[jugador.lado] = jugador

    def colocar_pelota(self, x, y, vx, vy):
        self.pelota.position = (x, y)
        self.pelota.velocity = (vx, vy)
        self.pelota.angular_velocity = 0.0

    def avanzar(self):
        """
        Avanza la física un paso de config.DT, dividido en SUBPASOS pasos
        pequeños. Con pasos más cortos la pelota se mueve menos entre dos
        revisiones de choques, y así no puede "saltarse" la raqueta.
        """
        dt = config.DT / config.SUBPASOS
        for _ in range(config.SUBPASOS):
            self.espacio.step(dt)
        for jugador in self.jugadores.values():
            jugador.mantener_en_su_campo()


def _limitar_velocidad_pelota(cuerpo, gravedad, amortiguacion, dt):
    """
    pymunk llama a esta función para actualizar la velocidad de la pelota.
    Primero hacemos lo normal (aplicar la gravedad) y luego recortamos la
    rapidez a VEL_MAX_PELOTA, conservando la dirección.
    """
    pymunk.Body.update_velocity(cuerpo, gravedad, amortiguacion, dt)
    rapidez = cuerpo.velocity.length
    if rapidez > config.VEL_MAX_PELOTA:
        cuerpo.velocity = cuerpo.velocity * (config.VEL_MAX_PELOTA / rapidez)
