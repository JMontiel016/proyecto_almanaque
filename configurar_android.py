"""Configura permiso de cámara, red local y nombre visible en Android."""
from pathlib import Path  # Rutas relativas al paquete.
import shutil  # Copia iconos originales listos para Android.
import re  # Modifica valores de Gradle sin depender de números de línea.
import xml.etree.ElementTree as ET  # Manifest válido, sin duplicar permisos.

raiz = Path(__file__).parent / 'aplicacion' / 'android'  # Proyecto generado por Flutter.
android = 'http://schemas.android.com/apk/res/android'  # Namespace oficial.
ET.register_namespace('android', android)  # Mantiene prefijo convencional.
ruta = raiz / 'app/src/main/AndroidManifest.xml'  # Manifest usado para release y debug.
arbol = ET.parse(ruta)  # Lee plantilla nativa.
manifest = arbol.getroot()  # Elemento raíz.
for permiso in ['android.permission.CAMERA', 'android.permission.INTERNET', 'android.permission.ACCESS_NETWORK_STATE']:
    if not any(n.get(f'{{{android}}}name') == permiso for n in manifest.findall('uses-permission')):
        ET.SubElement(manifest, 'uses-permission', {f'{{{android}}}name': permiso})  # Idempotente.
aplicacion = manifest.find('application')  # App generada.
aplicacion.set(f'{{{android}}}icon', '@mipmap/ic_launcher')  # Fuerza nuestro launcher en el manifest.
aplicacion.attrib.pop(f'{{{android}}}roundIcon',None)  # No permite un icono redondo de plantilla.
aplicacion.set(f'{{{android}}}label', 'Zunpi')  # Nombre visible corto.
aplicacion.set(f'{{{android}}}usesCleartextTraffic', 'true')  # HTTP/WS local; producción debe usar TLS.
arbol.write(ruta, encoding='utf-8', xml_declaration=True)  # Guarda XML bien formado.
for archivo in [raiz/'app/build.gradle.kts', raiz/'app/build.gradle']:
    if archivo.exists():
        texto = archivo.read_text()  # Gradle Kotlin o Groovy.
        texto = re.sub(r'minSdk\s*=\s*flutter.minSdkVersion', 'minSdk = maxOf(24, flutter.minSdkVersion)', texto)  # Kotlin.
        texto = re.sub(r'minSdkVersion\s+flutter.minSdkVersion', 'minSdkVersion Math.max(24, flutter.minSdkVersion)', texto)  # Groovy.
        archivo.write_text(texto)  # API 24 o mínimo superior del SDK.
print('Android configurado: cámara, Wi-Fi y nombre Zunpi.')  # Confirmación.

# Reemplaza icono Flutter en todos los tamaños y en Android adaptativo.
recursos = Path(__file__).parent / "recursos_android"
destino = raiz / "app/src/main/res"
shutil.copytree(recursos, destino, dirs_exist_ok=True)
print("Icono Zunpi instalado en Android.")
