"""
arbitro.py — Las reglas del tenis simplificado (sección 3.5 del plan).

El árbitro NO usa física: recibe avisos de lo que pasó ("la pelota botó en
x = 812", "el jugador 0 la tocó", "tocó la red") y decide qué significa según
las reglas. Por eso se puede probar con pytest sin simular nada: basta con
contarle una jugada inventada y ver si da el punto a quien corresponde.

Produce los eventos de eventos.py, que después usan la aptitud (R2), las
métricas (R4) y las grabaciones (R3).

Reglas. Pierde el punto el jugador que:
- deja botar la pelota dos veces en su campo (motivo DOBLE_BOTE);
- golpea y la pelota bota primero en su propio campo o toca la red (BOTE_PROPIO);
- golpea y la pelota cae fuera de la cancha (FUERA) o supera el techo (SOBRE_TECHO).
Un golpe es VÁLIDO si la pelota cruza la red y bota en el campo rival, o si
el rival la golpea en el aire (volea) cuando ya está de su lado.
Si se agota TIEMPO_MAX_PUNTO, el punto se anula (ANULADO).
"""

import config
import eventos
from controlador import DERECHA, IZQUIERDA


def campo_de(x):
    """Lado al que pertenece la posición x: 0, 1 o None si está fuera de la cancha."""
    if x < 0.0 or x > config.ANCHO_CANCHA:
        return None
    return IZQUIERDA if x < config.X_RED else DERECHA


def rival_de(lado):
    return 1 - lado


class Arbitro:
    """
    Lleva el estado de un punto y la lista de eventos de todo el partido.

    Uso (lo hace partido.py):
        arb = Arbitro()
        arb.nuevo_punto(t, receptor)
        ... en cada paso: arb.golpe(...), arb.bote(...), arb.red(...), arb.revisar(...)
        ... hasta que arb.punto_terminado sea True
    """

    def __init__(self):
        self.eventos = []
        self.punto_terminado = True

    # --- Inicio de un punto ---

    def nuevo_punto(self, t, receptor):
        self.t_inicio = t
        self.receptor = receptor
        self.golpeador = None        # quién golpeó por última vez (None = viene del saque)
        self.bote_valido = False     # ¿el último golpe ya botó bien en el campo rival?
        self.botes_saque = 0         # botes del saque antes de que alguien lo toque
        self.golpes_validos = 0
        self.t_ultimo_toque = None
        self.punto_terminado = False
        self._anotar(eventos.SAQUE, t, hacia=receptor)

    # --- Avisos que llegan de la física ---

    def golpe(self, t, jugador, x, y, fuerza):
        """La pelota tocó la raqueta de `jugador` en (x, y)."""
        if self.punto_terminado:
            return
        mismo_golpe = (jugador == self.golpeador and self.t_ultimo_toque is not None
                       and t - self.t_ultimo_toque < config.TIEMPO_MISMO_GOLPE)
        self.t_ultimo_toque = t
        if mismo_golpe:
            return   # varios contactos seguidos con la misma raqueta = un solo golpe
        # Volea: el rival la golpea en el aire cuando ya cruzó a su lado.
        # Cuenta como golpe válido de quien la mandó.
        if (self.golpeador is not None and jugador != self.golpeador
                and not self.bote_valido and campo_de(x) == jugador):
            self.golpes_validos += 1
        self.golpeador = jugador
        self.bote_valido = False
        self._anotar(eventos.GOLPE, t, jugador=jugador, x=x, y=y, fuerza=fuerza)

    def bote(self, t, x):
        """La pelota tocó el suelo en x."""
        if self.punto_terminado:
            return
        campo = campo_de(x)
        if self.golpeador is None:
            self._bote_de_saque(t, x, campo)
        elif self.bote_valido:
            # Ya botó bien en el campo rival: este es el segundo bote, el
            # rival no la devolvió. No importa si cae dentro o fuera.
            self._anotar(eventos.BOTE, t, x=x, campo=campo, golpeador=self.golpeador, valido=False)
            self._terminar(t, perdedor=rival_de(self.golpeador), motivo=eventos.DOBLE_BOTE)
        elif campo == rival_de(self.golpeador):
            self.bote_valido = True
            self.golpes_validos += 1
            self._anotar(eventos.BOTE, t, x=x, campo=campo, golpeador=self.golpeador, valido=True)
        else:
            self._anotar(eventos.BOTE, t, x=x, campo=campo, golpeador=self.golpeador, valido=False)
            motivo = eventos.BOTE_PROPIO if campo == self.golpeador else eventos.FUERA
            self._terminar(t, perdedor=self.golpeador, motivo=motivo)

    def red(self, t):
        """La pelota tocó la red."""
        if self.punto_terminado:
            return
        self._anotar(eventos.RED, t, golpeador=self.golpeador)
        # Si viene de un golpe que todavía no botó en el campo rival, el
        # golpe no pasó: es como botar en el propio campo. (Si ya botó bien,
        # o es el saque, la pelota sigue en juego hasta que bote.)
        if self.golpeador is not None and not self.bote_valido:
            self._terminar(t, perdedor=self.golpeador, motivo=eventos.BOTE_PROPIO)

    def revisar(self, t, y_pelota):
        """Se llama en cada paso: revisa el techo y el tiempo máximo."""
        if self.punto_terminado:
            return
        if y_pelota > config.TECHO and self.golpeador is not None and not self.bote_valido:
            self._terminar(t, perdedor=self.golpeador, motivo=eventos.SOBRE_TECHO)
        elif t - self.t_inicio >= config.TIEMPO_MAX_PUNTO:
            self._terminar(t, perdedor=None, motivo=eventos.ANULADO)

    # --- Interno ---

    def _bote_de_saque(self, t, x, campo):
        self._anotar(eventos.BOTE, t, x=x, campo=campo, golpeador=None, valido=False)
        if campo != self.receptor:
            # El saque es automático y siempre apunta al receptor; si cae en
            # otro lado no es culpa de nadie.
            self._terminar(t, perdedor=None, motivo=eventos.ANULADO)
            return
        self.botes_saque += 1
        if self.botes_saque >= 2:
            self._terminar(t, perdedor=self.receptor, motivo=eventos.DOBLE_BOTE)

    def _terminar(self, t, perdedor, motivo):
        ganador = None if perdedor is None else rival_de(perdedor)
        self._anotar(eventos.PUNTO, t, ganador=ganador, motivo=motivo,
                     golpes_validos=self.golpes_validos)
        self.punto_terminado = True

    def _anotar(self, tipo, t, **campos):
        self.eventos.append(eventos.evento(tipo, t, **campos))
