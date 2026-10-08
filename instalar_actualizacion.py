"""Ejecutar desde el proyecto anterior: python3 /ruta/nueva/instalar_actualizacion.py"""
from pathlib import Path
from datetime import datetime
import shutil
import sys

origen=Path(__file__).resolve().parent
destino=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path.cwd().resolve()
archivos=[
 'aplicacion/lib/main.dart','aplicacion/lib/pantallas/inicio.dart',
 'aplicacion/lib/pantallas/partida.dart','aplicacion/lib/juego/escenario.dart',
 'aplicacion/lib/servicios/conexion.dart','aplicacion/lib/servicios/conversor_camara.dart',
 'aplicacion/pubspec.yaml','aplicacion/pubspec.lock','aplicacion/analysis_options.yaml',
 'servidor/motor.py','servidor/servidor.py','servidor/detector_salto.py',
 'servidor/seguimiento.py','servidor/buzon.py','servidor/requirements.txt',
 'servidor/iniciar.sh','probar_android_usb.sh','LEEME.md','QA.md',
 'aplicacion/test/inicio_test.dart','aplicacion/test/escenario_test.dart',
 'aplicacion/test/conversor_camara_test.dart',
 'servidor/pruebas/test_reglas.py','servidor/pruebas/test_movimientos.py',
 'servidor/pruebas/test_conexion.py','servidor/pruebas/test_actualizacion.py',
 'servidor/pruebas/test_fluidez.py',
]
retirar=['aplicacion/lib/pantallas/invitacion.dart','servidor/almacenamiento.py']
try:
 if origen==destino:
  raise RuntimeError('Ya estás en la versión nueva. No hace falta instalar: seguí LEEME.md.')
 if not (destino/'aplicacion/pubspec.yaml').is_file() or not (destino/'servidor/iniciar.sh').is_file():
  raise RuntimeError('Ejecutá desde la raíz del proyecto Zunpi anterior.')
 for nombre in archivos:
  if not (origen/nombre).is_file():raise RuntimeError(f'Paquete incompleto: falta {nombre}')
 respaldo=destino/'respaldos'/('visual_060_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
 afectados=archivos+retirar
 existentes={n for n in afectados if (destino/n).is_file()}
 for nombre in existentes:
  p=respaldo/nombre;p.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(destino/nombre,p)
 escritos=[]
 try:
  for nombre in archivos:
   p=destino/nombre;p.parent.mkdir(parents=True,exist_ok=True)
   escritos.append(nombre);shutil.copy2(origen/nombre,p)
  for nombre in retirar:
   p=destino/nombre
   if p.is_file():escritos.append(nombre);p.unlink()
 except Exception:
  for nombre in escritos:
   p=destino/nombre
   if nombre in existentes:shutil.copy2(respaldo/nombre,p)
   elif p.is_file():p.unlink()
  raise
 print('Actualización 0.6.0 instalada. Respaldo:',respaldo)
 print('Reiniciá Python y Flutter. No se modificaron tu venv, modelo ni datos.')
except Exception as error:
 print('ERROR:',error,file=sys.stderr);sys.exit(1)
