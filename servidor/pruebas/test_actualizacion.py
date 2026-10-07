"""Instalación del icono Android."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
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
