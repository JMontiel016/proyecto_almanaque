import unittest
from detector_salto import DetectorSalto
from motor import Juego, Jugador

class Movimientos(unittest.TestCase):
    def detector(self, escala=.6):
        d=DetectorSalto()
        for i in range(12): d.evaluar(.5,.9,.9,escala,10+i*.1)
        return d
    def test_salto_unico_y_aterrizaje(self):
        d=self.detector()
        self.assertTrue(d.evaluar(.45,.86,.86,.6,12)[0])
        self.assertFalse(d.evaluar(.44,.85,.85,.6,12.1)[0])
        d.evaluar(.5,.9,.9,.6,12.3)
        self.assertTrue(d.evaluar(.45,.86,.86,.6,12.7)[0])
    def test_agachado_histeresis_y_salida(self):
        d=self.detector()
        self.assertFalse(d.evaluar(.60,.9,.9,.4,12)[0])
        self.assertTrue(d.agachado)
        d.evaluar(.56,.9,.9,.4,12.1)
        self.assertTrue(d.agachado)
        d.evaluar(.53,.9,.9,.6,12.2)
        self.assertFalse(d.agachado)
    def test_paso_y_ruido_no_saltan(self):
        d=self.detector()
        self.assertFalse(d.evaluar(.45,.84,.9,.6,12)[0])
        for i in range(30):
            self.assertFalse(d.evaluar(.5+(i%3-1)*.003,.9,.9,.6,12+i*.05)[0])
    def test_escala_congelada_al_agacharse(self):
        d=self.detector(); d.evaluar(.6,.9,.9,.3,12)
        self.assertEqual(d.escala,.6)
        self.assertTrue(d.agachado)
    def test_perdida_e_invalido_recalibran(self):
        d=self.detector();d.evaluar(.45,.85,.85,.6,20)
        self.assertIsNone(d.base)
        d=self.detector();d.evaluar(float('nan'),.9,.9,.6,12)
        self.assertIsNone(d.base)
    def test_escala_pequena_y_grande(self):
        for escala in [.3,.8]:
            d=self.detector(escala)
            self.assertTrue(d.evaluar(.5-escala*.07,.9-escala*.06,.9-escala*.06,escala,12)[0])
    def sala(self, agachado=False):
        s=Juego();s.estado='jugando'
        s.jugadores['a']=Jugador('a','QA',rastreado=True,ultima_camara=100,agachado=agachado)
        return s
    def test_aereo_de_pie_choca_agachado_pasa(self):
        for agachado in [False,True]:
            s=self.sala(agachado)
            s.obstaculos=[{'tipo':'aereo','x':145,'alto':24,'ancho':40,'y':38}]
            s.avanzar(.02,100)
            self.assertEqual(s.jugadores['a'].vivo,agachado)
    def test_agacharse_no_evade_cactus(self):
        s=self.sala(True);s.obstaculos=[{'x':145,'alto':42,'ancho':26}]
        s.avanzar(.02,100);self.assertFalse(s.jugadores['a'].vivo)
    def test_salto_contra_aereo_choca(self):
        s=self.sala();s.jugadores['a'].altura=45
        s.obstaculos=[{'tipo':'aereo','x':145,'alto':24,'ancho':40,'y':38}]
        s.avanzar(.02,100);self.assertFalse(s.jugadores['a'].vivo)
    def test_genera_ambos_obstaculos(self):
        s=self.sala();s.tiempo=10;s.azar.seed(1);tipos=set()
        for _ in range(50):
            s.siguiente=0;s.obstaculos=[];s.avanzar(.02,100)
            tipos.add(s.obstaculos[0]['tipo'])
        self.assertEqual(tipos,{'suelo','aereo'})

if __name__=='__main__':unittest.main()

class PausaManual(unittest.TestCase):
    def test_pausa_no_avanza_y_continuar_retoma(self):
        s=Juego();s.estado='jugando'
        s.jugadores['a']=Jugador('a','QA',rastreado=True,ultima_camara=100)
        s.pausa_manual=True
        s.avanzar(.05,100)
        self.assertTrue(s.pausada);self.assertEqual(s.tiempo,0)
        self.assertTrue(s.publico()['pausa_manual'])
        s.pausa_manual=False;s.avanzar(.05,100)
        self.assertFalse(s.pausada);self.assertGreater(s.tiempo,0)
    def test_continuar_no_ignora_cuerpo_perdido(self):
        s=Juego();s.estado='jugando';s.pausa_manual=False
        s.jugadores['a']=Jugador('a','QA',rastreado=False,ultima_camara=100)
        s.avanzar(.05,100)
        self.assertTrue(s.pausada);self.assertEqual(s.tiempo,0)
