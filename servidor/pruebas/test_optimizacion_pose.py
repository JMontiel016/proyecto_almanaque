"""Pruebas de regresión de la detección de saltos sin cámara ni modelo externo."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from detector_salto import DetectorSalto


class PruebasPoseOptimizada(unittest.TestCase):
    def calibrado(self):
        detector = DetectorSalto()
        for indice in range(12):
            detector.evaluar(.55, .9, .9, .75, indice * .12)
        self.assertIsNotNone(detector.base)
        return detector

    def test_un_solo_evento_por_salto(self):
        detector = self.calibrado()
        primero, _ = detector.evaluar(.48, .83, .83, .75, 2.0)
        segundo, _ = detector.evaluar(.47, .82, .82, .75, 2.1)
        self.assertTrue(primero)
        self.assertFalse(segundo)

    def test_no_salta_si_un_tobillo_queda_en_suelo(self):
        detector = self.calibrado()
        salto, _ = detector.evaluar(.48, .83, .90, .75, 2.0)
        self.assertFalse(salto)

    def test_recalibra_tras_perdida(self):
        detector = self.calibrado()
        detector.perdida(4.0)
        self.assertIsNone(detector.base)
        self.assertEqual(len(detector.muestras), 0)


if __name__ == "__main__":
    unittest.main()
