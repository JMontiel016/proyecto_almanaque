"""Casos de ranking por nombre, migración e instalación del icono Android."""
import hashlib
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import almacenamiento

class PruebasNombres(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.anterior = almacenamiento.RUTA
        almacenamiento.RUTA = Path(self.temporal.name)
    def tearDown(self):
        almacenamiento.RUTA = self.anterior
        self.temporal.cleanup()
    def test_mismo_nombre_otro_celular_comparte_record(self):
        almacenamiento.registrar('celular1','Jaime',500)
        almacenamiento.registrar('celular2','  JAIME ',700)
        self.assertEqual(almacenamiento.ranking(),[{'nombre':'JAIME','puntos':700}])
    def test_unicode_y_espacios(self):
        almacenamiento.registrar('1','Ana   Ñandú',600)
        almacenamiento.registrar('2','ana ñandú',200)
        self.assertEqual(len(almacenamiento.ranking()),1)
        self.assertEqual(almacenamiento.ranking()[0]['puntos'],600)
    def test_migracion_conserva_mejor_puntaje(self):
        base=sqlite3.connect(almacenamiento.RUTA/'ranking.sqlite3')
        base.execute('CREATE TABLE ranking(identificador TEXT,nombre TEXT,puntos INTEGER)')
        base.executemany('INSERT INTO ranking VALUES(?,?,?)',[('a','Jaime',300),('b','jaime',800)])
        base.commit();base.close()
        self.assertEqual(almacenamiento.ranking(),[{'nombre':'jaime','puntos':800}])
        self.assertEqual(almacenamiento.ranking(),[{'nombre':'jaime','puntos':800}])
    def test_nombre_distinto_no_se_mezcla(self):
        almacenamiento.registrar('a','Ana',100)
        almacenamiento.registrar('a','Jaime',200)
        self.assertEqual(len(almacenamiento.ranking()),2)

class PruebaIcono(unittest.TestCase):
    def test_manifest_y_png_usan_icono_propio(self):
        proyecto = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as carpeta:
            raiz=Path(carpeta)
            shutil.copy(proyecto/'configurar_android.py',raiz)
            shutil.copytree(proyecto/'recursos_android',raiz/'recursos_android')
            android=raiz/'aplicacion/android/app'
            (android/'src/main').mkdir(parents=True)
            manifest=android/'src/main/AndroidManifest.xml'
            manifest.write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android"><application android:icon="@mipmap/flutter" android:roundIcon="@mipmap/flutter_round"/></manifest>')
            (android/'build.gradle.kts').write_text('minSdk = flutter.minSdkVersion')
            subprocess.run([sys.executable,str(raiz/'configurar_android.py')],check=True,capture_output=True)
            app=ET.parse(manifest).getroot().find('application')
            namespace='{http://schemas.android.com/apk/res/android}'
            self.assertEqual(app.get(namespace+'icon'),'@mipmap/ic_launcher')
            self.assertIsNone(app.get(namespace+'roundIcon'))
            fuente=proyecto/'recursos_android/mipmap-xxxhdpi/ic_launcher.png'
            destino=android/'src/main/res/mipmap-xxxhdpi/ic_launcher.png'
            self.assertEqual(hashlib.sha256(fuente.read_bytes()).digest(),hashlib.sha256(destino.read_bytes()).digest())

if __name__=='__main__': unittest.main()
