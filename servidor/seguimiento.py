"""Seguimiento corporal y reconocimiento de saltos, únicamente en Python."""
import threading  # Protege el único modelo compartido y su inicialización.
import time  # Intervalo entre saltos.
from pathlib import Path  # Modelo junto al servidor.
import cv2  # Decodifica y dibuja sobre imágenes; no hace la inferencia.
import numpy as np  # Convierte JPEG a matriz.
import mediapipe as mp  # Modelo de pose ejecutado en Python.

CONEXIONES = [(11,12),(11,13),(13,15),(12,14),(14,16),(11,23),(12,24),
              (23,24),(23,25),(25,27),(24,26),(26,28),(27,31),(28,32)]  # Esqueleto.

from detector_salto import DetectorSalto  # Regla corporal separada de la inferencia.

_cerrojo = threading.RLock()  # Limita competencia CPU entre cámaras.

class Seguimiento:
    def __init__(self):
        modelo = Path(__file__).parent / 'modelos' / 'pose_landmarker_lite.task'  # Ruta portable.
        if not modelo.exists():
            raise RuntimeError('Falta modelo: ejecuta python descargar_modelo.py')  # Error accionable.
        opciones = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(modelo), delegate=mp.tasks.BaseOptions.Delegate.CPU),
            running_mode=mp.tasks.vision.RunningMode.VIDEO, num_poses=1,
            min_pose_detection_confidence=.5, min_pose_presence_confidence=.5,
            min_tracking_confidence=.5, output_segmentation_masks=False)
        # Cada cámara necesita su propio historial de tracking; no mezclar personas.
        with _cerrojo:
            self.modelo = mp.tasks.vision.PoseLandmarker.create_from_options(opciones)
        self.ultimo_ms = -1
        self.salto = DetectorSalto()

    def cerrar(self):
        with _cerrojo:
            self.modelo.close()

    def procesar(self, datos):
        imagen = cv2.imdecode(np.frombuffer(datos, dtype=np.uint8), cv2.IMREAD_COLOR)  # Respeta EXIF.
        if imagen is None:
            raise ValueError('Imagen JPEG inválida.')  # No procesa basura.
        alto, ancho = imagen.shape[:2]  # Resolución real recibida.
        if max(alto, ancho) > 640:
            imagen = cv2.resize(imagen, (int(ancho * 640 / max(alto, ancho)), int(alto * 640 / max(alto, ancho))))
        # Flutter entrega JPEG orientado y reflejado solo si usa la cámara frontal.
        alto, ancho = imagen.shape[:2]  # Vista de hasta 640 píxeles sin deformación.
        reducida = cv2.resize(imagen, (int(ancho*480/max(alto,ancho)),int(alto*480/max(alto,ancho)))) if max(alto,ancho)>480 else imagen  # Solo inferencia reducida.
        rgb = cv2.cvtColor(reducida, cv2.COLOR_BGR2RGB)  # MediaPipe requiere RGB.
        ahora = time.monotonic()
        inicio = time.perf_counter()
        with _cerrojo:
            marca = max(self.ultimo_ms + 1, int(ahora * 1000))
            self.ultimo_ms = marca
            resultado = self.modelo.detect_for_video(
                mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), marca)
        inferencia_ms = round((time.perf_counter() - inicio) * 1000, 1)
        valido, salto, mensaje = False, False, 'Mostrá hombros, caderas, rodillas y ambos pies'  # Estado inicial.
        if resultado.pose_landmarks:
            puntos = resultado.pose_landmarks[0]  # Persona principal.
            necesarios = [11,12,23,24,25,26,27,28]  # Cuerpo completo.
            valido = all((puntos[i].visibility or 0) > .45 and .005 < puntos[i].x < .995 and .005 < puntos[i].y < .995 for i in necesarios)
            if not valido:
                faltantes = []  # Indica qué zona falta, en lugar de un bloqueo genérico.
                for etiqueta, indices in [('hombros',[11,12]),('caderas',[23,24]),('rodillas',[25,26]),('pies',[27,28])]:
                    if any((puntos[i].visibility or 0) <= .45 or not (.005 < puntos[i].x < .995 and .005 < puntos[i].y < .995) for i in indices):
                        faltantes.append(etiqueta)
                mensaje = 'Falta ver: '+', '.join(faltantes)+'. Alejá el celular y evitá contraluz.'
            if valido:
                altura = max(puntos[27].y,puntos[28].y) - min(puntos[11].y,puntos[12].y)  # Escala del cuerpo.
                salto, mensaje = self.salto.evaluar((puntos[23].y+puntos[24].y)/2, puntos[27].y, puntos[28].y, altura, ahora)
        if not valido:
            self.salto.agachado = False
        listo = valido and self.salto.base is not None  # La partida espera calibración completa.
        # Retorna coordenadas pequeñas: nunca recodifica ni devuelve video HD.
        articulaciones = []
        if resultado.pose_landmarks:
            articulaciones = [[round(p.x, 5), round(p.y, 5), round(p.visibility or 0, 3)]
                              if i >= 11 else [0, 0, 0]
                              for i, p in enumerate(resultado.pose_landmarks[0])]
        return {'tipo':'vision','cuerpo':valido,'listo':listo,'salto':salto,'mensaje':mensaje,
                'ancho':ancho,'alto':alto,'calibracion':len(self.salto.muestras),
                'puntos':articulaciones, 'agachado': valido and self.salto.agachado,
                'inferencia_ms':inferencia_ms}
