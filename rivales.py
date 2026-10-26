"""
rivales.py — Jugadores escritos a mano (sin IA).

RivalProgramado: "sigue la pelota con error y potencia aleatorios" (plan,
sección 6). Se usa para tres cosas:
  1. comprobar en F1 que la física y las reglas permiten pelotear;
  2. ser el rival de la etapa 2 del entrenamiento;
  3. ser la BATERÍA DE REFERENCIA de las métricas (sección 8): todos los
     tratamientos se miden contra él, así que no debe cambiar a mitad del
     experimento.

Cómo piensa (todo en su marco propio, como si jugara a la izquierda):
  - Si la pelota se aleja (la acaba de golpear), vuelve a su posición de espera.
  - Si la pelota viene, PREDICE dónde estará cuando, después de botar en su
    campo, baje a la altura de golpe. Para eso usa las fórmulas del tiro
    parabólico (la misma gravedad y elasticidad que la física).
  - Camina hasta quedar a la distancia justa de ese punto, con un pequeño
    error al azar (para no ser perfecto).
  - Elige al azar un ángulo de tiro y un punto del campo rival donde quiere
    que bote, y calcula (otra vez con el tiro parabólico) la fuerza necesaria,
    descontando la potencia que trae la pelota (capa 1 del golpe). Supone
    que le pega con el punto dulce: si se ubica mal, el tiro sale corto.
    A esa fuerza le suma un error al azar: la "potencia aleatoria" del plan.
  - Cuando faltan RIVAL_ANTICIPACION segundos para que la pelota llegue,
    golpea.

Como el árbitro, no lee la física directamente: solo ve la Percepcion.
"""

import math
import random

import config
from controlador import Accion, Controlador
from jugador import valor_para_angulo

# Sin altura inicial, el tiro de mayor alcance es a 45° (alcance = v²·sen(2a)/|g|).
# No es un parámetro para calibrar: es un dato de la física.
ANGULO_MAYOR_ALCANCE = 45.0


class RivalProgramado(Controlador):
    nombre = "rival programado"

    def __init__(self, semilla, error_posicion=config.RIVAL_ERROR_POSICION,
                 error_fuerza=config.RIVAL_ERROR_FUERZA):
        # Azar propio (regla del contrato): la misma semilla da el mismo rival.
        self.azar = random.Random(semilla)
        self.error_posicion = error_posicion
        self.error_fuerza = error_fuerza
        self.reiniciar()

    def reiniciar(self):
        self.ya_boto = False      # ¿la pelota que viene ya botó en mi campo?
        self.vy_anterior = 0.0
        self.viene_anterior = False
        self._planear_jugada()

    def _planear_jugada(self):
        """Decide al azar cómo va a responder la próxima pelota."""
        self.error_actual = self.azar.gauss(0.0, self.error_posicion)
        self.angulo_tiro = self.azar.uniform(*config.RIVAL_ANGULO_TIRO)
        self.x_destino = self.azar.uniform(*config.RIVAL_DESTINO)
        self.factor_fuerza = 1.0 + self.azar.gauss(0.0, self.error_fuerza)

    def decidir(self, p):
        viene = p.pelota_vx < 0.0 or p.pelota_x < config.X_RED
        if viene and not self.viene_anterior:
            # Pelota nueva hacia mí: planeo de nuevo la jugada.
            self.ya_boto = False
            self._planear_jugada()
        self.viene_anterior = viene
        self._detectar_bote(p)
        if not viene:
            return self._volver_a_casa(p)
        return self._ir_y_golpear(p)

    # --- Partes del comportamiento ---

    def _detectar_bote(self, p):
        # Un bote se nota porque la velocidad vertical pasa de bajar a subir
        # cerca del suelo, y en mi lado de la red.
        cerca_del_suelo = p.pelota_y < 4 * config.RADIO_PELOTA
        if (self.vy_anterior < 0.0 <= p.pelota_vy and cerca_del_suelo
                and p.pelota_x < config.X_RED):
            self.ya_boto = True
        self.vy_anterior = p.pelota_vy

    def _angulo_raqueta(self):
        # La pelota sale perpendicular a la raqueta: raqueta = tiro − 90°.
        return valor_para_angulo(math.radians(self.angulo_tiro) - math.pi / 2)

    def _volver_a_casa(self, p):
        return Accion(mover=_mover_hacia(p.propio_x, config.RIVAL_X_CASA),
                      angulo_raqueta=self._angulo_raqueta())

    def _ir_y_golpear(self, p):
        objetivo = prediccion_golpe(p, self.ya_boto)
        if objetivo is None:
            return self._volver_a_casa(p)
        x_golpe, t_golpe = objetivo
        destino = x_golpe - config.RIVAL_DISTANCIA_GOLPE + self.error_actual
        # Rapidez que necesita el tiro planeado. Se recalcula en cada decisión
        # porque el punto de golpe predicho cambia mientras la pelota viene.
        rapidez = rapidez_para_llegar(self.x_destino - x_golpe, config.RIVAL_ALTURA_GOLPE,
                                      math.radians(self.angulo_tiro))
        if rapidez > config.VEL_SALIDA_MAX:
            # Desde muy atrás no llega con ese ángulo: cambia a 45°, el
            # ángulo de mayor alcance, y recalcula.
            self.angulo_tiro = ANGULO_MAYOR_ALCANCE
            rapidez = rapidez_para_llegar(self.x_destino - x_golpe, config.RIVAL_ALTURA_GOLPE,
                                          math.radians(self.angulo_tiro))
        golpe = 0.0
        if self.ya_boto and t_golpe <= config.RIVAL_ANTICIPACION:
            # Capa 1 del golpe: la pelota que llega aporta rapidez, así que la
            # raqueta tiene que poner menos. Predice con qué rapidez llegará
            # (vx casi no cambia; vy cambia por la gravedad en t_golpe).
            rapidez_entrante = math.hypot(p.pelota_vx, p.pelota_vy + config.GRAVEDAD * t_golpe)
            rapidez_raqueta = rapidez * self.factor_fuerza - config.APORTE_PELOTA_ENTRANTE * rapidez_entrante
            golpe = fuerza_para_rapidez(rapidez_raqueta)
        return Accion(mover=_mover_hacia(p.propio_x, destino),
                      angulo_raqueta=self._angulo_raqueta(), golpe=golpe)


def prediccion_golpe(p, ya_boto):
    """
    Predice (x, t) del punto de golpe: dónde estará la pelota y en cuántos
    segundos, cuando baje a RIVAL_ALTURA_GOLPE después de botar.

    Tiro parabólico: y(t) = y0 + vy·t + ½·g·t² (g es negativa).
    Devuelve None si la pelota no va a llegar a esa altura en mi campo.
    """
    g = config.GRAVEDAD
    x, y, vx, vy = p.pelota_x, p.pelota_y, p.pelota_vx, p.pelota_vy
    h = config.RIVAL_ALTURA_GOLPE
    t_total = 0.0
    if not ya_boto:
        # 1) Tiempo hasta tocar el suelo (centro de la pelota a la altura del radio).
        t_suelo = tiempo_hasta_altura(y, vy, config.RADIO_PELOTA, g)
        if t_suelo is None:
            return None
        x += vx * t_suelo
        vy = -config.ELASTICIDAD_PELOTA * (vy + g * t_suelo)   # rebota y pierde energía
        y = config.RADIO_PELOTA
        t_total += t_suelo
        if x >= config.X_RED or x < 0.0:
            return None   # no bota en mi campo: no es mi pelota (va fuera o a la red)
    # 2) Tiempo hasta bajar a la altura de golpe.
    t_bajar = tiempo_hasta_altura(y, vy, h, g)
    if t_bajar is None:
        # Bote demasiado bajo: golpearla en lo más alto (cuando vy = 0).
        t_bajar = max(0.0, vy / -g)
    return x + vx * t_bajar, t_total + t_bajar


def tiempo_hasta_altura(y0, vy, altura, g):
    """
    Tiempo (el MAYOR, es decir, bajando) en que y0 + vy·t + ½·g·t² = altura.
    Es la fórmula de la ecuación de segundo grado. None si nunca llega.
    """
    a, b, c = 0.5 * g, vy, y0 - altura
    discriminante = b * b - 4 * a * c
    if discriminante < 0.0:
        return None
    t = (-b - math.sqrt(discriminante)) / (2 * a)   # con a < 0, esta es la raíz mayor
    return t if t >= 0.0 else None


def rapidez_para_llegar(distancia, altura, angulo):
    """
    Rapidez inicial para que un tiro con ese ángulo, lanzado desde `altura`,
    caiga (centro de la pelota a la altura del radio) a `distancia` hacia adelante.

    Sale de juntar las dos ecuaciones del tiro parabólico:
      x(t) = v·cos(a)·t   y   y(t) = altura + v·sen(a)·t − ½·|g|·t²
    y despejar v cuando x = distancia e y = radio.
    """
    g = -config.GRAVEDAD
    caida = altura - config.RADIO_PELOTA + distancia * math.tan(angulo)
    if distancia <= 0.0 or caida <= 0.0:
        return config.VEL_SALIDA_MIN
    return math.sqrt(g * distancia ** 2 / (2 * math.cos(angulo) ** 2 * caida))


def fuerza_para_rapidez(rapidez):
    """Lo inverso del modelo de golpe: rapidez deseada -> fuerza de 0 a 1."""
    fuerza = (rapidez - config.VEL_SALIDA_MIN) / (config.VEL_SALIDA_MAX - config.VEL_SALIDA_MIN)
    # Nunca 0 exacto: golpe = 0 significa "no golpear".
    return max(0.01, min(1.0, fuerza))


def _mover_hacia(x_actual, x_destino):
    """Velocidad proporcional a la distancia: frena al acercarse al destino."""
    return max(-1.0, min(1.0, (x_destino - x_actual) / config.RIVAL_ZONA_FRENADO))


# --- Etapa 1: el lanzapelotas ---

def lanzapelotas(azar, receptor):
    """
    Función de saque para la etapa 1 (se le pasa a partido.jugar_partido):
    lanza la pelota desde el campo rival para que bote en el campo del
    receptor, como si fuera un tiro de un rival. Elige al azar desde dónde,
    a qué altura, con qué ángulo y dónde quiere que bote, y calcula la
    rapidez con el tiro parabólico (la misma cuenta que usa el rival programado).

    Las posiciones de config están en el marco propio del receptor (su fondo
    en 0); para el jugador derecho se reflejan.
    """
    x_lanza = azar.uniform(*config.LANZAPELOTAS_X)
    altura = azar.uniform(*config.LANZAPELOTAS_ALTURA)
    x_bote = azar.uniform(*config.LANZAPELOTAS_DESTINO)
    angulo = math.radians(azar.uniform(*config.LANZAPELOTAS_ANGULO))
    rapidez = rapidez_para_llegar(x_lanza - x_bote, altura, angulo)
    vx, vy = -rapidez * math.cos(angulo), rapidez * math.sin(angulo)   # hacia el receptor
    if receptor == 0:
        return (x_lanza, altura, vx, vy)
    return (config.ANCHO_CANCHA - x_lanza, altura, -vx, vy)


class ControladorAusente(Controlador):
    """
    El "rival" de la etapa 1: se va al fondo de su campo y no hace nada, para
    no tocar las pelotas que devuelve el que aprende.
    """

    nombre = "lanzapelotas"

    def decidir(self, p):
        return Accion(mover=-1.0, angulo_raqueta=-1.0)
