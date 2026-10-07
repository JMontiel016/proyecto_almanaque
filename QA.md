# Verificación de la versión individual

- 40 pruebas Python aprobadas: calibración, salto, aterrizaje, agachado,
  histéresis, ruido, pies alternados, cara oculta, marcas temporales VIDEO,
  colisiones cactus/aves, conexión y rechazo de una segunda cámara.
- Compilación sintáctica Python y sintaxis de scripts Bash correctas.
- Dart: los 8 archivos de código/pruebas se pudieron analizar sintácticamente
  con `dart format --output=none`.
- `flutter analyze --no-pub`: sin problemas.
- `flutter test --no-pub`: 6 pruebas aprobadas, incluyendo conversión JPEG,
  rotación, stride, inicio individual sin QR y selección Wi-Fi.
- Dependencias resueltas y lockfile regenerado sin QR/scanner.
- SDK de validación: Flutter 3.47.6 / Dart 3.13.5.

Limitaciones: no se midieron FPS ni precisión con una persona real.
El modelo real no pudo cargarse aquí por falta de libGLESv2.so.2.
El análisis Flutter y sus pruebas pasaron; no se compiló un APK Android.
Revisar en el dispositivo la captura, la orientación y la detección en vivo.
No hay un APK compilado ni garantía de rendimiento para cualquier dispositivo.

El tamaño de archivos de la versión actual cae de unos 279 MB a unos 6 MB.
El historial Git aún contiene los archivos antiguos de venv; eliminarlo de
la rama no reduce por sí solo el tamaño de un clon con todo el historial.
Se recomienda `git clone --depth 1 --branch simplificar-juego-individual URL`
para probar esta versión sin descargar el historial anterior.
