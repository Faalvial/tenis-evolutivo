"""
jugador.py — El cuerpo de un jugador: un cubo con una raqueta movida por un motor.

El jugador NO decide nada: recibe una Accion (de controlador.py) y la convierte
en fuerzas y velocidades para la física. Quien decide es el controlador (la IA,
el rival programado o el humano).

Simetría: las acciones llegan en el marco PROPIO (como si el jugador estuviera
a la izquierda, con la red hacia +x). Aquí se traducen al mundo: para el
jugador derecho se invierte el movimiento horizontal y se refleja el ángulo de
la raqueta. `signo` vale +1 a la izquierda y -1 a la derecha y hace ese trabajo.

La raqueta es un cuerpo aparte, unido al cubo con un pivote (una "bisagra").
Un motor la hace girar con control proporcional: cuanto más lejos está del
ángulo pedido, más rápido gira. Es la misma idea que las articulaciones de las
criaturas evolutivas.

MODELO DE GOLPE (decisión de F1, ver capítulo 1 del libro). Si la pelota toca
la raqueta mientras el jugador está golpeando, la pelota sale:
  - en la dirección PERPENDICULAR a la cara de la raqueta, tomando el ángulo
    que tenía la raqueta al EMPEZAR el golpe (la "preparación");
  - con una rapidez que depende solo de la fuerza del golpe.
Si la toca sin golpear, rebota con la física normal (un "bloqueo" sin fuerza).
Con un choque 100 % físico el resultado era caótico: un píxel de diferencia en
el punto de contacto cambiaba el destino en cientos de unidades.
"""

import math

import pymunk

import config
import mundo as m
from controlador import IZQUIERDA
from mundo import CONTACTO_FISICO, CONTACTO_GOLPE, CONTACTO_IGNORAR


class Jugador:
    def __init__(self, mundo, lado, x):
        self.lado = lado
        self.signo = 1 if lado == IZQUIERDA else -1
        self.recarga = 0.0              # segundos que faltan para poder golpear otra vez
        self.tiempo_golpe = 0.0         # > 0 mientras dura un golpe
        self.fuerza_golpe = 0.0         # fuerza del golpe en curso (0 si no hay)
        self.angulo_inicio_golpe = 0.0  # ángulo propio de la raqueta al empezar el golpe
        self.ya_pego = False            # ¿el golpe en curso ya tocó la pelota?
        # Mismo grupo para el cubo y su raqueta: pymunk no hace chocar formas
        # del mismo grupo, así la raqueta puede atravesar su propio cubo.
        grupo = lado + 1
        self.cuerpo = self._crear_cubo(mundo, x, grupo)
        self.raqueta = self._crear_raqueta(mundo, grupo)
        self.motor = self._unir_raqueta(mundo)
        mundo.inscribir_jugador(self)

    # --- Construcción ---

    def _crear_cubo(self, mundo, x, grupo):
        lado = config.TAMANO_JUGADOR
        # Momento de inercia infinito = no puede girar: el cubo nunca se voltea.
        cuerpo = pymunk.Body(config.MASA_JUGADOR, float("inf"))
        cuerpo.position = (x, lado / 2)
        forma = pymunk.Poly.create_box(cuerpo, (lado, lado))
        forma.friction = 0.0    # la velocidad la fijamos nosotros; la fricción solo estorbaría
        forma.filter = pymunk.ShapeFilter(group=grupo, categories=m.CAT_JUGADOR,
                                          mask=m.CAT_SUELO)
        mundo.espacio.add(cuerpo, forma)
        return cuerpo

    def _crear_raqueta(self, mundo, grupo):
        largo, grosor = config.LARGO_RAQUETA, config.GROSOR_RAQUETA
        cuerpo = pymunk.Body(config.MASA_RAQUETA,
                             pymunk.moment_for_box(config.MASA_RAQUETA, (largo, grosor)))
        # El rectángulo está centrado en el origen del cuerpo; el mango es el
        # extremo (-largo/2, 0). La ubicamos con el mango en el pivote, ya en
        # el ángulo de espera del medio del rango.
        cuerpo.angle = self.angulo_mundo(traducir_angulo(0.0))
        cuerpo.position = self.pivote_mundo() + pymunk.Vec2d(largo / 2, 0).rotated(cuerpo.angle)
        forma = pymunk.Poly.create_box(cuerpo, (largo, grosor))
        forma.elasticity = config.ELASTICIDAD_RAQUETA
        forma.friction = 0.5
        forma.collision_type = m.TIPO_RAQUETA[self.lado]
        forma.filter = pymunk.ShapeFilter(group=grupo, categories=m.CAT_RAQUETA,
                                          mask=m.CAT_PELOTA)
        mundo.espacio.add(cuerpo, forma)
        return cuerpo

    def _unir_raqueta(self, mundo):
        pivote = pymunk.PivotJoint(self.cuerpo, self.raqueta,
                                   self.pivote_local(), (-config.LARGO_RAQUETA / 2, 0))
        motor = pymunk.SimpleMotor(self.cuerpo, self.raqueta, 0.0)
        motor.max_force = config.FUERZA_MOTOR_RAQUETA
        mundo.espacio.add(pivote, motor)
        return motor

    # --- Geometría y marco propio ---

    def pivote_local(self):
        """Punto del cubo donde va la bisagra: la cara que mira a la red."""
        return pymunk.Vec2d(self.signo * config.TAMANO_JUGADOR / 2, config.ALTURA_PIVOTE)

    def pivote_mundo(self):
        return self.cuerpo.position + self.pivote_local()

    def angulo_mundo(self, angulo_propio):
        """
        Ángulo propio -> ángulo del mundo. A la izquierda son iguales; a la
        derecha se refleja respecto de la vertical (θ -> π − θ).

        No usamos controlador.reflejar_angulo aquí porque esa función deja el
        resultado en (−π, π]: para el motor necesitamos un ángulo CONTINUO
        alrededor de π, o creería que tiene que dar casi una vuelta entera.
        """
        if self.signo == 1:
            return angulo_propio
        return math.pi - angulo_propio

    def angulo_propio(self):
        """Ángulo actual de la raqueta en el marco propio (0 = hacia la red)."""
        return self.angulo_mundo(self.raqueta.angle)   # reflejar dos veces = identidad

    def angulo_raqueta_mundo(self):
        """Ángulo del mundo dejado en (−π, π], como lo esperan Percepcion y la grabación."""
        a = self.raqueta.angle
        return math.atan2(math.sin(a), math.cos(a))

    def en_suelo(self):
        altura_base = self.cuerpo.position.y - config.TAMANO_JUGADOR / 2
        return altura_base <= config.TOLERANCIA_SUELO and self.cuerpo.velocity.y <= 1.0

    def limites_x(self):
        """
        Mínimo y máximo de la x del CENTRO del cubo: desde el espacio detrás
        de su fondo hasta la zona prohibida junto a la red (MARGEN_RED_JUGADOR).
        Esa zona hace que la raqueta nunca cruce la red.
        """
        mitad = config.TAMANO_JUGADOR / 2
        fondo = config.ESPACIO_DETRAS_FONDO
        if self.signo == 1:
            return -fondo + mitad, config.X_RED - config.MARGEN_RED_JUGADOR - mitad
        return (config.X_RED + config.MARGEN_RED_JUGADOR + mitad,
                config.ANCHO_CANCHA + fondo - mitad)

    def mantener_en_su_campo(self):
        """Si el cubo se salió de su mitad, lo devuelve al borde y lo frena."""
        x_min, x_max = self.limites_x()
        x, y = self.cuerpo.position
        vx, vy = self.cuerpo.velocity
        if x < x_min:
            self.cuerpo.position = (x_min, y)
            self.cuerpo.velocity = (max(vx, 0.0), vy)
        elif x > x_max:
            self.cuerpo.position = (x_max, y)
            self.cuerpo.velocity = (min(vx, 0.0), vy)

    def esta_golpeando(self):
        return self.tiempo_golpe > 0.0

    # --- Aplicar una acción (se llama en cada paso de física) ---

    def aplicar(self, accion, dt):
        self._mover(accion)
        self._actualizar_golpe(accion, dt)
        self._mover_raqueta(accion)

    def _mover(self, accion):
        # Fijamos la velocidad horizontal directamente (en lugar de empujar con
        # una fuerza): el control es inmediato y fácil de entender.
        vx = self.signo * accion.mover * config.VEL_MAX_JUGADOR
        vy = self.cuerpo.velocity.y
        if accion.saltar and self.en_suelo():
            vy = config.VEL_SALTO
        self.cuerpo.velocity = (vx, vy)

    def _actualizar_golpe(self, accion, dt):
        self.recarga = max(0.0, self.recarga - dt)
        if self.tiempo_golpe > 0.0:
            self.tiempo_golpe -= dt
            barrido = self.angulo_propio() - self.angulo_inicio_golpe
            if self.tiempo_golpe <= 0.0 or barrido >= config.AMPLITUD_GOLPE:
                self.tiempo_golpe = 0.0
                self.fuerza_golpe = 0.0
        elif accion.golpe > 0.0 and self.recarga == 0.0:
            # Empieza un golpe. La recarga cuenta desde el inicio del golpe.
            self.tiempo_golpe = config.DURACION_GOLPE
            self.fuerza_golpe = accion.golpe
            self.recarga = config.RECARGA_GOLPE
            self.angulo_inicio_golpe = self.angulo_propio()
            self.ya_pego = False

    def _mover_raqueta(self, accion):
        if self.esta_golpeando():
            # Durante el golpe la raqueta barre hacia arriba a velocidad fija:
            # así cubre una zona amplia y es más fácil hacer contacto.
            giro_propio = config.VEL_GIRO_GOLPE
        else:
            # Control proporcional hacia el ángulo pedido. accion.angulo_raqueta
            # va de -1 a 1 y se traduce al rango permitido de config.
            objetivo = traducir_angulo(accion.angulo_raqueta)
            giro_propio = config.GANANCIA_RAQUETA * (objetivo - self.angulo_propio())
            giro_propio = max(-config.VEL_MAX_RAQUETA, min(config.VEL_MAX_RAQUETA, giro_propio))
        # El giro propio se pasa al mundo con `signo` (a la derecha, "hacia
        # arriba" es sentido horario). El signo menos es por la convención de
        # pymunk: SimpleMotor hace que la raqueta gire a -rate respecto del cubo.
        self.motor.rate = -self.signo * giro_propio

    # --- Contacto con la pelota (lo llama mundo.py durante un choque) ---

    def al_tocar_pelota(self, pelota):
        """
        Decide qué pasa cuando la pelota toca esta raqueta y, si es un golpe,
        le pone su nueva velocidad. Devuelve CONTACTO_GOLPE, _FISICO o _IGNORAR.
        """
        if not self.esta_golpeando():
            return CONTACTO_FISICO
        if self.ya_pego:
            return CONTACTO_IGNORAR
        self.ya_pego = True
        pelota.velocity = self.velocidad_salida()
        return CONTACTO_GOLPE

    def velocidad_salida(self):
        """
        Velocidad (en el mundo) con que sale la pelota en un golpe.

        Dirección: perpendicular a la cara de arriba de la raqueta, o sea el
        ángulo de preparación + 90°. Una raqueta inclinada hacia abajo-adelante
        (ángulo negativo) manda la pelota hacia arriba-adelante.
        Rapidez: de VEL_SALIDA_MIN (fuerza 0) a VEL_SALIDA_MAX (fuerza 1).
        """
        direccion = self.angulo_inicio_golpe + math.pi / 2
        rapidez = (config.VEL_SALIDA_MIN
                   + self.fuerza_golpe * (config.VEL_SALIDA_MAX - config.VEL_SALIDA_MIN))
        return (self.signo * rapidez * math.cos(direccion), rapidez * math.sin(direccion))

    # --- Datos para la percepción y la grabación ---

    def estado_grabacion(self):
        """(x, y, raqueta_x, raqueta_y, raqueta_angulo) en el mundo, para grabar.py."""
        x, y = self.cuerpo.position
        rx, ry = self.raqueta.position
        return (x, y, rx, ry, self.angulo_raqueta_mundo())

    def distancia_a(self, punto):
        """Distancia del punto a la raqueta (al segmento del mango a la punta)."""
        mango = self.pivote_mundo()
        punta = mango + pymunk.Vec2d(config.LARGO_RAQUETA, 0).rotated(self.raqueta.angle)
        return _distancia_a_segmento(pymunk.Vec2d(*punto), mango, punta)


def traducir_angulo(valor):
    """Convierte un valor de -1 a 1 al rango ANGULO_RAQUETA_MIN..MAX (radianes)."""
    fraccion = (valor + 1.0) / 2.0
    return config.ANGULO_RAQUETA_MIN + fraccion * (config.ANGULO_RAQUETA_MAX - config.ANGULO_RAQUETA_MIN)


def valor_para_angulo(angulo):
    """Lo inverso de traducir_angulo: radianes -> valor de -1 a 1 para Accion."""
    rango = config.ANGULO_RAQUETA_MAX - config.ANGULO_RAQUETA_MIN
    return 2.0 * (angulo - config.ANGULO_RAQUETA_MIN) / rango - 1.0


def _distancia_a_segmento(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / ab.dot(ab)))
    return (p - (a + ab * t)).length
