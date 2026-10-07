"""Salida acotada: reemplaza estados viejos sin perder respuestas de la cámara."""
import asyncio  # Espera sin bloquear otros jugadores.
from collections import deque  # Control y visión conservan su orden.

class Buzon:
    def __init__(self):
        self.estado = None  # Solo interesa el último estado de física.
        self.controles = deque()  # Una respuesta por imagen admitida.
        self.disponible = asyncio.Event()  # Despierta al único escritor de la conexión.

    def publicar(self, mensaje):
        if mensaje.get('tipo') == 'estado':
            self.estado = mensaje  # Nunca borra un acuse de visión.
        else:
            if len(self.controles) >= 16:
                raise RuntimeError('El cliente no consume respuestas. Reconectá la sala.')
            self.controles.append(mensaje)  # Memoria limitada incluso en una conexión detenida.
        self.disponible.set()

    async def get(self):
        while True:
            if self.controles:
                return self.controles.popleft()  # La cámara obtiene prioridad sobre estados obsoletos.
            if self.estado is not None:
                resultado, self.estado = self.estado, None
                return resultado
            self.disponible.clear()  # No hay await entre la inspección y este cambio.
            await self.disponible.wait()
