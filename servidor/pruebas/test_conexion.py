"""Prueba del handshake con transporte/modelo simulados; no sustituye hardware."""
import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

class AppSimulada:
    def __init__(self, **kwargs): pass
    def get(self, ruta): return lambda funcion: funcion
    def post(self, ruta): return lambda funcion: funcion
    def websocket(self, ruta): return lambda funcion: funcion

class Desconexion(Exception): pass

class CanalSimulado:
    def __init__(self): self.mensajes = []; self.cerrado = False
    async def accept(self): pass
    async def receive_json(self): return {'nombre':'Jaime','identidad':'a'*32,'sala':''}
    async def send_json(self, mensaje): self.mensajes.append(mensaje)
    async def receive(self): return {'type':'websocket.disconnect'}
    async def close(self, **kwargs): self.cerrado = True

class DetectorSimulado:
    def cerrar(self): pass

class PruebasConexion(unittest.IsolatedAsyncioTestCase):
    def cargar(self):
        biblioteca = types.ModuleType('fastapi')
        biblioteca.FastAPI, biblioteca.WebSocket, biblioteca.WebSocketDisconnect = AppSimulada, CanalSimulado, Desconexion
        especificacion = importlib.util.spec_from_file_location('servidor_prueba', Path(__file__).resolve().parents[1]/'servidor.py')
        modulo = importlib.util.module_from_spec(especificacion)
        with patch.dict(sys.modules, {'fastapi':biblioteca}): especificacion.loader.exec_module(modulo)
        return modulo
    async def test_bienvenida_antes_de_cargar_detector(self):
        servidor = self.cargar()
        canal = CanalSimulado()
        seguimiento = types.ModuleType('seguimiento')
        def construir():
            self.assertEqual(canal.mensajes[0]['tipo'],'bienvenida')
            self.assertTrue(canal.mensajes[0]['sala'])
            self.assertTrue(canal.mensajes[0]['administrador'])
            return DetectorSimulado()
        seguimiento.Seguimiento = construir
        with patch.dict(sys.modules, {'seguimiento':seguimiento}), patch.object(Path, 'is_file', return_value=True):
            await servidor.conectar(canal)
        self.assertEqual([m['tipo'] for m in canal.mensajes], ['bienvenida','preparando','detector_listo'])
        self.assertFalse(servidor.salas)
        self.assertFalse(servidor.conexiones)
    async def test_reserva_invita_antes_de_cargar_detector(self):
        servidor = self.cargar()
        with patch.object(servidor,'crear_detector',side_effect=AssertionError('No debe cargar detector')):
            datos = await servidor.reservar_sala({'nombre':'Jaime'})
        self.assertIn(datos['sala'],servidor.salas)
        self.assertEqual(servidor.salas[datos['sala']].jugadores,{})
        self.assertEqual(datos['version'],'0.4.0')

    async def test_modelo_faltante_explica_solucion(self):
        servidor = self.cargar()
        canal = CanalSimulado()
        with patch.object(Path, 'is_file', return_value=False), patch.object(servidor.logging, 'exception'):
            await servidor.conectar(canal)
        self.assertEqual(canal.mensajes[0]['tipo'],'error')
        self.assertIn('descargar_modelo.py',canal.mensajes[0]['mensaje'])
        self.assertTrue(canal.cerrado)
        self.assertFalse(servidor.salas)
    async def test_error_detector_no_deja_sala_colgada(self):
        servidor = self.cargar()
        canal = CanalSimulado()
        seguimiento = types.ModuleType('seguimiento')
        def fallar(): raise RuntimeError('Detector no disponible')
        seguimiento.Seguimiento = fallar
        with patch.dict(sys.modules, {'seguimiento':seguimiento}), patch.object(Path,'is_file',return_value=True), patch.object(servidor.logging,'exception'):
            await servidor.conectar(canal)
        self.assertEqual(canal.mensajes[-1]['tipo'],'error')
        self.assertIn('Detector no disponible',canal.mensajes[-1]['mensaje'])
        self.assertFalse(servidor.salas)
        self.assertFalse(servidor.conexiones)

if __name__ == '__main__': unittest.main()
