"""Salto y agachado con escala fija de calibración, sin puntos faciales."""
from collections import deque
from statistics import median
from math import isfinite

class DetectorSalto:
    def __init__(self):
        self.muestras = deque(maxlen=12)
        self.base = None
        self.en_aire = False
        self.agachado = False
        self.ultimo_salto = -10.0
        self.ultimo_valido = None
        self.escala = None

    def reiniciar(self):
        self.muestras.clear()
        self.base = self.escala = None
        self.en_aire = self.agachado = False
        self.ultimo_valido = None
        self.ultimo_salto = -10.0

    def evaluar(self, cadera, pie_izquierdo, pie_derecho, altura, ahora):
        if not all(isfinite(v) for v in (cadera, pie_izquierdo, pie_derecho, altura, ahora)) or altura <= .1:
            self.reiniciar()
            return False, 'Mostrá hombros, caderas y ambos pies'
        if self.ultimo_valido is not None and ahora - self.ultimo_valido > 1.5:
            self.reiniciar()
        self.ultimo_valido = ahora
        # Guardar cada pie impide que la alternancia entre ambos oculte un paso.
        if self.base is None:
            self.muestras.append((cadera, pie_izquierdo, pie_derecho, altura))
            self.agachado = False
            if len(self.muestras) < 12:
                return False, 'Calibrando: quedate de pie y quieto'
            escala = median(m[3] for m in self.muestras)
            if any(max(m[e] for m in self.muestras) - min(m[e] for m in self.muestras) > escala * .06 for e in (0,1,2)):
                return False, 'Quedate quieto para calibrar'
            self.base = tuple(median(m[e] for m in self.muestras) for e in (0,1,2))
            self.escala = escala
        escala = self.escala
        elevacion = self.base[0] - cadera
        izquierdo = self.base[1] - pie_izquierdo
        derecho = self.base[2] - pie_derecho
        pies_suben = min(izquierdo, derecho) > escala * .035
        if self.en_aire and abs(izquierdo) < escala * .025 and abs(derecho) < escala * .025:
            self.en_aire = False
        # Histéresis: agachado no oscila al quedar cerca del umbral.
        pies_apoyados = max(abs(izquierdo), abs(derecho)) < escala * .06
        if self.en_aire or not pies_apoyados:
            self.agachado = False
        elif not self.agachado and elevacion < -escala * .13:
            self.agachado = True
        elif self.agachado and elevacion > -escala * .08:
            self.agachado = False
        if elevacion > escala * .05 and pies_suben and not self.en_aire and ahora - self.ultimo_salto > .45:
            self.en_aire, self.ultimo_salto = True, ahora
            self.agachado = False
            return True, 'SALTO DETECTADO'
        return False, ('En el aire' if self.en_aire else
                       'AGACHADO' if self.agachado else 'Cuerpo listo: saltá o agachate')
