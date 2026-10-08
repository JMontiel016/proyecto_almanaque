"""Regresiones de cola y seguimiento sin video: no sustituyen la cámara real."""
import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from buzon import Buzon
from detector_salto import DetectorSalto

class PruebasBuzon(unittest.IsolatedAsyncioTestCase):
    async def test_estados_no_descartan_acuse_de_camara(self):
        buzon = Buzon()
        buzon.publicar({'tipo':'vision','listo':True})
        for i in range(1000): buzon.publicar({'tipo':'estado','numero':i})
        self.assertEqual((await buzon.get())['tipo'], 'vision')
        self.assertEqual((await buzon.get())['numero'], 999)
        self.assertEqual(len(buzon.controles), 0)
    async def test_despierta_escritor_sin_perder_mensaje(self):
        buzon = Buzon()
        escritor = asyncio.create_task(buzon.get())
        await asyncio.sleep(0)
        buzon.publicar({'tipo':'vision','puntos':[]})
        self.assertEqual((await asyncio.wait_for(escritor,.2))['tipo'], 'vision')
    async def test_salida_limitada_para_cliente_detenido(self):
        buzon = Buzon()
        for _ in range(16): buzon.publicar({'tipo':'error'})
        with self.assertRaises(RuntimeError): buzon.publicar({'tipo':'error'})
        self.assertEqual(len(buzon.controles), 16)
    async def test_controles_conservan_orden(self):
        buzon = Buzon()
        for i in range(5): buzon.publicar({'tipo':'vision','numero':i})
        self.assertEqual([(await buzon.get())['numero'] for _ in range(5)], list(range(5)))

class ImagenSimulada:
    shape = (480, 270, 3)
class ModeloSimulado:
    def __init__(self, puntos): self.puntos = puntos
    def detect_for_video(self, imagen, marca): return types.SimpleNamespace(pose_landmarks=self.puntos)

class PruebasPose(unittest.TestCase):
    def cargar(self):
        # Los módulos falsos no permiten flip/imencode: fallaría si volvemos a procesar video de salida.
        cv = types.ModuleType('cv2')
        cv.IMREAD_COLOR, cv.COLOR_BGR2RGB = 1, 2
        cv.imdecode = lambda datos, modo: ImagenSimulada() if datos else None
        cv.cvtColor = lambda foto, modo: foto
        np = types.ModuleType('numpy'); np.uint8 = int; np.frombuffer = lambda datos, **kw: datos
        mp = types.ModuleType('mediapipe'); mp.ImageFormat = types.SimpleNamespace(SRGB=1)
        mp.Image = lambda **kw: kw
        ruta = Path(__file__).resolve().parents[1]/'seguimiento.py'
        spec = importlib.util.spec_from_file_location('pose_prueba', ruta)
        modulo = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'cv2':cv,'numpy':np,'mediapipe':mp}): spec.loader.exec_module(modulo)
        detector = modulo.Seguimiento.__new__(modulo.Seguimiento)
        detector.salto = DetectorSalto()
        detector.ultimo_ms = -1
        return detector
    def puntos(self):
        puntos = [types.SimpleNamespace(x=.5,y=.4,visibility=.95) for _ in range(33)]
        puntos[0].y=.1
        for i in [23,24]: puntos[i].y=.5
        for i in [27,28,31,32]: puntos[i].y=.9
        return puntos
    def test_retorna_pose_sin_jpeg_ni_espejo_adicional(self):
        detector = self.cargar(); puntos = self.puntos(); puntos[0].x=.2
        detector.modelo = ModeloSimulado([puntos])
        with patch('time.monotonic', side_effect=[1+i*.13 for i in range(12)]):
            for _ in range(12): salida = detector.procesar(b'jpeg_simulado')
        self.assertTrue(salida['listo'])
        self.assertEqual(salida['puntos'][0], [0,0,0])
        self.assertEqual(len(salida['puntos']),33)
        self.assertNotIn('imagen', salida)
    def test_cara_oculta_no_bloquea_calibracion(self):
        detector = self.cargar(); puntos = self.puntos()
        for i in range(11): puntos[i].visibility = 0; puntos[i].y = -1
        detector.modelo = ModeloSimulado([puntos])
        with patch('time.monotonic', side_effect=[1+i*.13 for i in range(12)]):
            for _ in range(12): salida = detector.procesar(b'jpeg_simulado')
        self.assertTrue(salida['listo'])
        self.assertEqual(salida['puntos'][:11], [[0,0,0]]*11)

    def test_tracking_marcas_estrictamente_crecientes(self):
        detector = self.cargar(); marcas = []
        class Modelo:
            def detect_for_video(self, imagen, marca):
                marcas.append(marca)
                return types.SimpleNamespace(pose_landmarks=[])
        detector.modelo = Modelo()
        with patch('time.monotonic', return_value=1):
            for _ in range(3): detector.procesar(b'jpeg_simulado')
        self.assertEqual(marcas, [1000,1001,1002])

    def test_falta_pie_no_habilita_juego(self):
        detector = self.cargar(); puntos = self.puntos(); puntos[28].visibility=.1
        detector.modelo = ModeloSimulado([puntos])
        salida = detector.procesar(b'jpeg_simulado')
        self.assertFalse(salida['listo']); self.assertIn('pies',salida['mensaje'])
    def test_persona_ausente_borra_esqueleto(self):
        detector = self.cargar(); detector.modelo=ModeloSimulado([])
        salida=detector.procesar(b'jpeg_simulado')
        self.assertEqual(salida['puntos'],[]); self.assertFalse(salida['cuerpo'])
    def test_jpeg_invalido_informa_error(self):
        detector = self.cargar()
        with self.assertRaises(ValueError): detector.procesar(b'')

if __name__ == '__main__': unittest.main()
