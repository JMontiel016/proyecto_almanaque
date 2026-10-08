"""Reglas autoritativas: los celulares dibujan; Python calcula puntos y choques."""
from dataclasses import dataclass, field  # Estructuras legibles para jugador y partida.
import random  # Obstáculos reproducibles mediante una semilla por ronda.
import time  # Reloj monotónico independiente de la fecha del sistema.

@dataclass
class Jugador:
    identificador: str  # Identificador local.
    nombre: str  # Nombre visible, separado del identificador.
    altura: float = 0.0  # Altura del dinosaurio sobre el suelo, en unidades del mundo.
    agachado: bool = False  # Postura confirmada por Python.
    impulso: float = 0.0  # Velocidad vertical del salto.
    puntos: int = 0  # Puntaje calculado exclusivamente en el servidor.
    vivo: bool = True  # Una única vida por intento.
    rastreado: bool = False  # Indica que la cámara ve el cuerpo completo.
    ultima_camara: float = 0.0  # Última imagen procesada para impedir jugar a ciegas.
    conectado: bool = True  # Evita mantener jugadores desconectados en carrera.

@dataclass
class Juego:
    jugadores: dict = field(default_factory=dict)  # Un único jugador por partida.
    estado: str = 'espera'  # espera, cuenta, jugando o terminada.
    tiempo: float = 0.0  # Tiempo activo de la ronda; se congela al perder seguimiento.
    cuenta: float = 3.0  # Cuenta regresiva común a todos.
    obstaculos: list = field(default_factory=list)  # Un mismo recorrido para todos.
    recorrido: float = 0.0  # Distancia acumulada para animar el terreno.
    siguiente: float = 700.0  # Distancia hasta generar otro obstáculo.
    pausa_manual: bool = False
    pausada: bool = False  # Pausa compartida cuando falta seguimiento corporal.
    azar: random.Random = field(default_factory=random.Random)  # Generador del recorrido.

    def comenzar(self):
        """Comienza cuando la cámara del jugador está calibrada."""
        if self.estado not in ('espera', 'terminada'):
            raise ValueError('Ya hay una ronda en curso.')
        if not self.jugadores or not all(j.rastreado for j in self.jugadores.values()):
            raise ValueError('Calibrá primero con hombros y ambos pies visibles.')
        self.pausa_manual = False
        self.estado, self.tiempo, self.cuenta = 'cuenta', 0.0, 3.0  # Reinicia el reloj.
        self.obstaculos, self.recorrido, self.siguiente = [], 0.0, 700.0  # Limpia recorrido.
        self.azar.seed(random.SystemRandom().randrange(2**32))  # Nueva ronda compartida.
        for jugador in self.jugadores.values():
            jugador.altura = jugador.impulso = 0.0  # Coloca cada dinosaurio en tierra.
            jugador.puntos, jugador.vivo = 0, True  # Una vida.

    def saltar(self, identificador):
        """Un evento corporal no permite dobles saltos ni revivir."""
        jugador = self.jugadores.get(identificador)  # Busca al dueño de la cámara.
        if jugador and self.estado == 'jugando' and not self.pausada and jugador.vivo and jugador.altura <= 0:
            jugador.agachado = False
            jugador.impulso = 540.0  # Impulso inicial, compensado por gravedad.

    def avanzar(self, segundos, ahora=None):
        """Avanza física en pasos pequeños; devolver jugadores que acabaron."""
        ahora = time.monotonic() if ahora is None else ahora  # Permite pruebas deterministas.
        dt = min(max(segundos, 0.0), 0.05)  # Limita saltos temporales del servidor.
        activos = [j for j in self.jugadores.values() if j.vivo and j.conectado]  # Participantes.
        self.pausada = self.pausa_manual or any(not j.rastreado or ahora - j.ultima_camara > 1.5 for j in activos)
        if self.estado not in ('cuenta', 'jugando') or self.pausada:
            return []  # Sin puntos gratis durante pausas o fuera de una ronda.
        if self.estado == 'cuenta':
            self.cuenta -= dt  # Todos observan la misma cuenta.
            if self.cuenta <= 0:
                self.estado = 'jugando'  # Comienza el primer intento.
            return []
        self.tiempo += dt  # Puntaje: 25 puntos por segundo activo.
        puntos = int(self.tiempo * 25)  # Comparables entre clientes.
        multiplicador = min(1.5 ** min(puntos // 500, 4), 4.0)  # ×1,5 cada 500; límite ×4.
        distancia = 220 * multiplicador * dt  # Velocidad del recorrido.
        self.recorrido += distancia  # Desplazamiento visual.
        self.siguiente -= distancia  # Cuenta para siguiente cactus.
        if self.siguiente <= 0:
            if puntos >= 100 and self.azar.random() < .35:
                self.obstaculos.append({'tipo':'aereo', 'x':1000.0, 'alto':24, 'ancho':40, 'y':38})
            else:
                self.obstaculos.append({'tipo':'suelo', 'x':1000.0, 'alto':self.azar.choice([42,52,62]), 'ancho':26, 'y':0})
            self.siguiente = self.azar.uniform(310, 470) * multiplicador  # Tiempo viable entre saltos.
        for obstaculo in self.obstaculos:
            obstaculo['x'] -= distancia  # Todos ven el mismo cactus.
        terminados = []  # Jugadores que chocaron.
        for jugador in activos:
            jugador.puntos = puntos  # Nadie informa un puntaje desde el celular.
            jugador.impulso -= 1500 * dt  # Gravedad.
            jugador.altura = max(0.0, jugador.altura + jugador.impulso * dt)  # Suelo.
            if jugador.altura == 0:
                jugador.impulso = 0.0  # Aterrizaje.
            for obstaculo in self.obstaculos:
                alto_jugador = 30 if jugador.agachado and jugador.altura == 0 else 65
                base_obstaculo = obstaculo.get('y', 0)
                choque_vertical = (jugador.altura < base_obstaculo + obstaculo['alto'] - 5 and
                                   jugador.altura + alto_jugador > base_obstaculo + 3)
                if obstaculo['x'] < 154 and obstaculo['x'] + obstaculo['ancho'] > 126 and choque_vertical:
                    jugador.vivo = False  # Un choque termina la vida.
                    terminados.append(jugador)  # Registra el resultado una vez.
                    break
        self.obstaculos = [o for o in self.obstaculos if o['x'] > -60]  # Descarta cactus pasados.
        if not any(j.vivo and j.conectado for j in self.jugadores.values()):
            self.estado = 'terminada'  # Permite reiniciar cuando todos terminan.
        return terminados

    def publico(self):
        """Estado pequeño para dibujar el juego."""
        return {'tipo': 'estado',
                'estado': self.estado, 'cuenta': max(0, self.cuenta), 'pausada': self.pausada, 'pausa_manual': self.pausa_manual,
                'recorrido': self.recorrido, 'velocidad': min(1.5 ** min(int(self.tiempo * 25) // 500, 4), 4.0),
                'obstaculos': self.obstaculos,
                'jugadores': [{k:v for k,v in vars(j).items() if k not in ('identificador_privado','ultima_camara')} for j in self.jugadores.values()]}
