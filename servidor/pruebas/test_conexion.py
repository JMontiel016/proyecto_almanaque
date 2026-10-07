"""Contrato individual con transporte y detector simulados."""
import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from detector_salto import DetectorSalto

class App:
    def __init__(self, **kw): pass
    def get(self, ruta): return lambda f:f
    def websocket(self, ruta): return lambda f:f
class Desconexion(Exception): pass
class Canal:
    def __init__(self, paquetes=None): self.mensajes=[];self.cerrado=False;self.paquetes=list(paquetes or [])
    async def accept(self): pass
    async def receive_json(self): return {'nombre':'Jugador'}
    async def send_json(self,m): self.mensajes.append(m)
    async def receive(self):
        await asyncio.sleep(0)
        return self.paquetes.pop(0) if self.paquetes else {'type':'websocket.disconnect'}
    async def close(self,**kw): self.cerrado=True
class Detector:
    def __init__(self): self.salto=DetectorSalto();self.cerrado=False
    def procesar(self, datos): return {'tipo':'vision','listo':True,'salto':False,'agachado':True}
    def cerrar(self): self.cerrado=True

class Conexion(unittest.IsolatedAsyncioTestCase):
    def cargar(self):
        api=types.ModuleType('fastapi');api.FastAPI=App;api.WebSocket=Canal;api.WebSocketDisconnect=Desconexion
        spec=importlib.util.spec_from_file_location('servidor_qa',Path(__file__).resolve().parents[1]/'servidor.py')
        m=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'fastapi':api}):spec.loader.exec_module(m)
        return m
    async def test_salud_individual(self):
        m=self.cargar();r=await m.salud()
        self.assertEqual(r['version'],'0.5.0');self.assertEqual(r['modo'],'individual')
    async def test_bienvenida_y_cierre_liberan_modelo(self):
        m=self.cargar();c=Canal();d=Detector()
        def crear():
            self.assertEqual(c.mensajes[0]['tipo'],'bienvenida');return d
        with patch.object(m,'crear_detector',side_effect=crear):await m.conectar(c)
        self.assertEqual([x['tipo'] for x in c.mensajes[:3]],['bienvenida','preparando','detector_listo'])
        self.assertNotIn('sala',c.mensajes[0]);self.assertFalse(m.ocupado);self.assertTrue(d.cerrado)
    async def test_segundo_celular_no_carga_modelo(self):
        m=self.cargar();m.ocupado=True;c=Canal()
        with patch.object(m,'crear_detector',side_effect=AssertionError):await m.conectar(c)
        self.assertTrue(c.cerrado);self.assertEqual(c.mensajes[0]['tipo'],'error');self.assertTrue(m.ocupado)
    async def test_error_modelo_libera_conexion(self):
        m=self.cargar();c=Canal()
        with patch.object(m,'crear_detector',side_effect=RuntimeError('falta modelo')),patch.object(m.logging,'exception'):
            await m.conectar(c)
        self.assertFalse(m.ocupado);self.assertTrue(c.cerrado);self.assertIn('falta modelo',c.mensajes[-1]['mensaje'])
    async def test_camara_y_comando_iniciar(self):
        m=self.cargar();c=Canal([{'type':'websocket.receive','bytes':b'jpeg'},
                               {'type':'websocket.receive','text':'{"accion":"iniciar"}'}])
        juegos=[];Original=m.Juego
        def crear_juego():
            j=Original();juegos.append(j);return j
        with patch.object(m,'crear_detector',return_value=Detector()),patch.object(m,'Juego',side_effect=crear_juego):
            await m.conectar(c)
        self.assertEqual(juegos[0].estado,'cuenta');self.assertTrue(juegos[0].jugadores['local'].agachado)
        self.assertFalse(m.ocupado)
    async def test_imagen_grande_rechazada(self):
        m=self.cargar();c=Canal([{'type':'websocket.receive','bytes':b'x'*500001}]);d=Detector()
        with patch.object(m,'crear_detector',return_value=d),patch.object(m.logging,'exception'):await m.conectar(c)
        self.assertTrue(c.cerrado);self.assertTrue(d.cerrado);self.assertFalse(m.ocupado)

if __name__=='__main__':unittest.main()
