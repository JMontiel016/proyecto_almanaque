"""Descarga explícita del modelo oficial; ejecutar una vez con internet."""
from pathlib import Path  # Destino junto al código.
from urllib.request import urlretrieve  # Descarga HTTPS del proveedor.

carpeta = Path(__file__).parent / 'modelos'  # No depende de dónde se ejecute.
carpeta.mkdir(exist_ok=True)  # Prepara carpeta.
url = 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task'  # Modelo oficial lite.
destino = carpeta / 'pose_landmarker_lite.task'  # Nombre esperado por seguimiento.py.
if not destino.exists():
    temporal = destino.with_suffix('.descarga')  # Evita aceptar una descarga incompleta.
    urlretrieve(url, temporal)  # Requiere internet solamente al preparar.
    temporal.replace(destino)  # Publica el modelo cuando terminó.
print(f'Modelo disponible: {destino}')  # Confirma preparación.
