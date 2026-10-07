#!/usr/bin/env bash
# Prepara archivos nativos con el SDK Flutter instalado por el usuario.
set -euo pipefail
# Usa la ubicación del script para soportar rutas con espacios.
raiz_zunpi="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# Comprueba que Flutter esté disponible antes de modificar la carpeta.
command -v flutter >/dev/null || { echo 'Instalá Flutter estable y Android SDK antes de continuar.'; exit 1; }
# Crea proyecto Android únicamente; lib existente se preserva explícitamente.
cd "$raiz_zunpi/aplicacion"
# Respalda código y dependencias para evitar que una plantilla reemplace el proyecto.
respaldo_zunpi="$(mktemp -d)"
# Garantiza limpieza del respaldo al terminar o fallar.
trap 'rm -rf -- "$respaldo_zunpi"' EXIT
# Guarda los archivos de autoría.
cp -R lib pubspec.yaml "$respaldo_zunpi/"
# Genera wrapper Gradle y archivos Android de la versión Flutter disponible.
flutter create --platforms=android --org py.jmontiel --project-name zunpi --no-pub .
# Restaura fuentes propias luego de generar plataforma.
cp -R "$respaldo_zunpi/lib/." lib/
# Restaura dependencias propias.
cp "$respaldo_zunpi/pubspec.yaml" pubspec.yaml
# Configura permisos y Android API 24 de forma reproducible.
python3 "$raiz_zunpi/configurar_android.py"
# Quita test de plantilla del contador, que no corresponde a este juego.
rm -f test/widget_test.dart
# Descarga paquetes en el equipo del usuario.
flutter pub get
# Comprueba semántica Dart con SDK real.
flutter analyze
# Informa paso siguiente sin instalar automáticamente en ningún dispositivo.
echo 'Preparado. Conectá Android por USB y ejecutá: cd aplicacion && flutter run'
