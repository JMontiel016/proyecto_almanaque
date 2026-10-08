"""Pruebas reales de reglas, detección geométrica y persistencia, sin cámara ni SDK."""
import sys  # Importa servidor desde carpeta de pruebas.
from pathlib import Path  # Rutas portables.
import unittest  # Biblioteca estándar; no requiere pip.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # Módulos del proyecto.
from motor import Juego, Jugador  # Física autoritativa.
from detector_salto import DetectorSalto  # Geometría corporal.

class PruebasMotor(unittest.TestCase):
    def setUp(self):
        self.sala = Juego()  # Sala de prueba.
        self.jugador = Jugador('a','Jaime',rastreado=True,ultima_camara=100)  # Pose vigente.
        self.jugador.identificador_privado = 'secreto-del-dispositivo'  # No debe salir por red.
        self.sala.jugadores['a'] = self.jugador
    def test_requiere_cuerpo_y_listo(self):
        self.jugador.rastreado = False  # Cámara perdida.
        with self.assertRaises(ValueError): self.sala.comenzar()
    def test_un_choque_termina_vida(self):
        self.sala.estado = 'jugando'  # Física activa.
        self.sala.obstaculos = [{'x':145,'alto':50,'ancho':26}]  # Cactus en dinosaurio.
        terminados = self.sala.avanzar(.02,100)  # Choque real.
        self.assertEqual(terminados,[self.jugador])
        self.assertFalse(self.jugador.vivo)
        self.assertEqual(self.sala.estado,'terminada')
    def test_salto_supera_cactus(self):
        self.sala.estado = 'jugando'
        self.jugador.altura = 90  # Por encima de obstáculo.
        self.sala.obstaculos = [{'x':145,'alto':50,'ancho':26}]
        self.assertEqual(self.sala.avanzar(.02,100),[])
        self.assertTrue(self.jugador.vivo)
    def test_no_doble_salto(self):
        self.sala.estado = 'jugando'
        self.sala.saltar('a')
        self.sala.avanzar(.02,100)
        previo = self.jugador.impulso
        self.sala.saltar('a')  # Segundo evento no reinicia impulso.
        self.assertEqual(self.jugador.impulso,previo)
    def test_pausa_no_suma_puntos(self):
        self.sala.estado = 'jugando'
        self.sala.avanzar(.05,103)  # Cámara caducada.
        self.assertTrue(self.sala.pausada)
        self.assertEqual(self.jugador.puntos,0)
        self.assertEqual(self.sala.tiempo,0)
    def test_500_puntos_multiplican_velocidad(self):
        self.sala.estado = 'jugando'
        self.sala.tiempo = 20  # 500 puntos, 25 por segundo.
        self.sala.avanzar(.02,100)
        self.assertAlmostEqual(self.sala.recorrido,220*1.5*.02)
    def test_identidad_privada_no_se_publica(self):
        self.assertNotIn('identificador_privado',self.sala.publico()['jugadores'][0])
class PruebasSalto(unittest.TestCase):
    def setUp(self):
        self.detector = DetectorSalto()
        for i in range(12): self.detector.evaluar(.5,.9,.9,.8,10+i*.15)  # De pie, quieto.
    def test_calibra(self):
        self.assertIsNotNone(self.detector.base)
    def test_salto_completo_un_evento(self):
        salto,_ = self.detector.evaluar(.42,.83,.83,.8,12)
        self.assertTrue(salto)
        self.assertFalse(self.detector.evaluar(.41,.82,.82,.8,12.1)[0])
    def test_agacharse_no_es_salto(self):
        self.assertFalse(self.detector.evaluar(.6,.9,.9,.8,12)[0])  # Caderas bajan, pies quietos.
    def test_un_solo_pie_no_es_salto(self):
        self.assertFalse(self.detector.evaluar(.42,.82,.9,.8,12)[0])
    def test_aterrizaje_permite_otro_salto(self):
        self.detector.evaluar(.42,.83,.83,.8,12)
        self.detector.evaluar(.5,.9,.9,.8,12.3)
        self.assertTrue(self.detector.evaluar(.42,.83,.83,.8,12.7)[0])
    def test_perder_cuerpo_recalibra(self):
        self.assertFalse(self.detector.evaluar(.42,.83,.83,.8,20)[0])
        self.assertIsNone(self.detector.base)

if __name__ == '__main__': unittest.main()
