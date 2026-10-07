"""Reglas autoritativas: los celulares dibujan; Python calcula puntos y choques."""
from dataclasses import dataclass, field  # Estructuras legibles para jugadores y salas.
import random  # Obstáculos reproducibles mediante una semilla por ronda.
import time  # Reloj monotónico independiente de la fecha del sistema.

@dataclass
class Jugador:
    identificador: str  # Identidad pública dentro de una sala.
    nombre: str  # Nombre visible, separado del identificador.
    altura: float = 0.0  # Altura del dinosaurio sobre el suelo, en unidades del mundo.
    impulso: float = 0.0  # Velocidad vertical del salto.
    puntos: int = 0  # Puntaje calculado exclusivamente en el servidor.
    vivo: bool = True  # Una única vida por intento.
    listo: bool = False  # Confirmación antes de comenzar una ronda.
    rastreado: bool = False  # Indica que la cámara ve el cuerpo completo.
    ultima_camara: float = 0.0  # Última imagen procesada para impedir jugar a ciegas.
    conectado: bool = True  # Evita mantener jugadores desconectados en carrera.
    guardado: bool = False  # Impide guardar dos veces el mismo resultado.

@dataclass
class Sala:
    codigo: str  # Código incluido en el QR.
    administrador: str  # Primer jugador; se transfiere al siguiente si sale.
    jugadores: dict = field(default_factory=dict)  # Máximo cuatro conexiones.
    estado: str = 'espera'  # espera, cuenta, jugando o terminada.
    tiempo: float = 0.0  # Tiempo activo de la ronda; se congela al perder seguimiento.
    cuenta: float = 3.0  # Cuenta regresiva común a todos.
    obstaculos: list = field(default_factory=list)  # Un mismo recorrido para todos.
    recorrido: float = 0.0  # Distancia acumulada para animar el terreno.
    siguiente: float = 700.0  # Distancia hasta generar otro obstáculo.
    pausada: bool = False  # Pausa compartida cuando falta seguimiento corporal.
    azar: random.Random = field(default_factory=random.Random)  # Generador de cada sala.

    def comenzar(self, solicitante):
        """Solo el administrador inicia, con todos listos y cuerpo visible."""
        if solicitante != self.administrador:
            raise ValueError('Solo el administrador puede iniciar.')
        if self.estado not in ('espera', 'terminada'):
            raise ValueError('Ya hay una ronda en curso.')
        if not self.jugadores or not all(j.listo and j.rastreado for j in self.jugadores.values()):
            raise ValueError('Todos deben estar listos y con el cuerpo completo visible.')
        self.estado, self.tiempo, self.cuenta = 'cuenta', 0.0, 3.0  # Reinicia el reloj.
        self.obstaculos, self.recorrido, self.siguiente = [], 0.0, 700.0  # Limpia recorrido.
        self.azar.seed(random.SystemRandom().randrange(2**32))  # Nueva ronda compartida.
        for jugador in self.jugadores.values():
            jugador.altura = jugador.impulso = 0.0  # Coloca cada dinosaurio en tierra.
            jugador.puntos, jugador.vivo, jugador.guardado = 0, True, False  # Una vida.

    def saltar(self, identificador):
        """Un evento corporal no permite dobles saltos ni revivir."""
        jugador = self.jugadores.get(identificador)  # Busca al dueño de la cámara.
        if jugador and self.estado == 'jugando' and not self.pausada and jugador.vivo and jugador.altura <= 0:
            jugador.impulso = 540.0  # Impulso inicial, compensado por gravedad.

    def avanzar(self, segundos, ahora=None):
        """Avanza física en pasos pequeños; devolver jugadores que acabaron."""
        ahora = time.monotonic() if ahora is None else ahora  # Permite pruebas deterministas.
        dt = min(max(segundos, 0.0), 0.05)  # Limita saltos temporales del servidor.
        activos = [j for j in self.jugadores.values() if j.vivo and j.conectado]  # Participantes.
        self.pausada = any(not j.rastreado or ahora - j.ultima_camara > 1.5 for j in activos)
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
            self.obstaculos.append({'x': 1000.0, 'alto': self.azar.choice([42, 52, 62]), 'ancho': 26})
            self.siguiente = self.azar.uniform(310, 470) * multiplicador  # Tiempo viable entre saltos.
        for obstaculo in self.obstaculos:
            obstaculo['x'] -= distancia  # Todos ven el mismo cactus.
        terminados = []  # Resultados que persistirá el servidor.
        for jugador in activos:
            jugador.puntos = puntos  # Nadie informa un puntaje desde el celular.
            jugador.impulso -= 1500 * dt  # Gravedad.
            jugador.altura = max(0.0, jugador.altura + jugador.impulso * dt)  # Suelo.
            if jugador.altura == 0:
                jugador.impulso = 0.0  # Aterrizaje.
            for obstaculo in self.obstaculos:
                if obstaculo['x'] < 154 and obstaculo['x'] + obstaculo['ancho'] > 126 and jugador.altura < obstaculo['alto'] - 5:
                    jugador.vivo = False  # Un choque termina la vida.
                    terminados.append(jugador)  # Registra el resultado una vez.
                    break
        self.obstaculos = [o for o in self.obstaculos if o['x'] > -60]  # Descarta cactus pasados.
        if not any(j.vivo and j.conectado for j in self.jugadores.values()):
            self.estado = 'terminada'  # Permite reiniciar cuando todos terminan.
            for jugador in self.jugadores.values():
                jugador.listo = False  # Requiere nueva confirmación.
        return terminados

    def publico(self):
        """Estado pequeño que comparten todos los celulares y la OLED."""
        return {'tipo': 'estado', 'sala': self.codigo, 'administrador': self.administrador,
                'estado': self.estado, 'cuenta': max(0, self.cuenta), 'pausada': self.pausada,
                'recorrido': self.recorrido, 'velocidad': min(1.5 ** min(int(self.tiempo * 25) // 500, 4), 4.0),
                'obstaculos': self.obstaculos,
                'jugadores': [{k:v for k,v in vars(j).items() if k not in ('identificador_privado','ultima_camara')} for j in self.jugadores.values()]}
