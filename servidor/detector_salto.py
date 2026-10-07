"""Detector geométrico de salto, independiente del modelo y comprobable sin cámara."""
from collections import deque  # Ventana de calibración.
from statistics import median  # Filtra ruido.

class DetectorSalto:
    """Exige desplazamiento de caderas Y ambos pies; no basta agacharse."""
    def __init__(self):
        self.muestras = deque(maxlen=12)  # Aproximadamente dos segundos de calibración.
        self.base = None  # Referencia cadera/pies en posición de pie.
        self.en_aire = False  # Bloquea múltiples eventos de un mismo salto.
        self.ultimo_salto = -10.0  # Permite el primer salto.
        self.ultimo_valido = 0.0  # Resetea si la persona desaparece.

    def reiniciar(self):
        self.muestras.clear()  # Elimina referencias anteriores.
        self.base, self.en_aire = None, False  # Vuelve a calibrar.

    def evaluar(self, cadera, pie_izquierdo, pie_derecho, altura, ahora):
        if self.ultimo_valido and ahora - self.ultimo_valido > 1.5:
            self.reiniciar()  # No reutiliza calibración tras moverse fuera del cuadro.
        self.ultimo_valido = ahora  # Marca seguimiento vigente.
        pies = max(pie_izquierdo, pie_derecho)  # Ambos deben subir para validar el salto.
        if self.base is None:
            self.muestras.append((cadera, pies))  # Mantenerse quieto al inicio.
            if len(self.muestras) < 12:
                return False, 'Calibrando: quedate de pie y quieto'
            if any(max(m[eje] for m in self.muestras) - min(m[eje] for m in self.muestras) > altura * .06 for eje in (0,1)):
                return False, 'Quedate quieto para calibrar'  # No calibra mientras salta.
            self.base = (median(m[0] for m in self.muestras), median(m[1] for m in self.muestras))
        subio_cadera = self.base[0] - cadera > altura * .045  # Desplazamiento relativo al cuerpo.
        subieron_pies = self.base[1] - pies > altura * .035  # Confirma despegue.
        if subio_cadera and subieron_pies and not self.en_aire and ahora - self.ultimo_salto > .45:
            self.en_aire, self.ultimo_salto = True, ahora  # Un único evento por salto.
            return True, 'SALTO DETECTADO'
        if self.en_aire and abs(self.base[1] - pies) < altura * .025:
            self.en_aire = False  # Rearma al aterrizar.
        return False, 'En el aire' if self.en_aire else 'Cuerpo listo: salta'

