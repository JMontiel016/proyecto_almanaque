#!/usr/bin/env bash
# Instala actualización y conecta Android al Python de la PC por USB.
set -euo pipefail
raiz_zunpi="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
dispositivo_zunpi="${1:-AM4U9X4724G01019}"
adb_zunpi="$(command -v adb || true)"
if [[ -z "$adb_zunpi" ]]; then
  sdk_zunpi="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-$HOME/Android/Sdk}}"
  adb_zunpi="$sdk_zunpi/platform-tools/adb"
fi
if [[ ! -x "$adb_zunpi" ]]; then
  echo 'No se encontró adb. Usá el adb de platform-tools de tu Android SDK.'
  exit 1
fi
# Verifica Python local ANTES de reinstalar o abrir el juego.
python3 - <<'PY'
import json
from urllib.request import urlopen
try:
    with urlopen('http://127.0.0.1:8001/salud',timeout=2) as respuesta:
        datos=json.load(respuesta)
    if datos.get('juego')!='Zunpi' or datos.get('version')!='0.4.0':
        raise RuntimeError('Reiniciá el servidor Python con los archivos v0.4.')
    print('Servidor v0.4 disponible; modelo:',datos.get('modelo'))
except Exception as error:
    raise SystemExit(f'Primero iniciá Python en el puerto 8001. Detalle: {error}')
PY
# No desconecta otros dispositivos ni borra datos de Android.
"$adb_zunpi" -s "$dispositivo_zunpi" reverse tcp:8001 tcp:8001
# Fuerza recursos de launcher propios en la app existente.
cd "$raiz_zunpi"
python3 configurar_android.py
cd aplicacion
# Solo limpiar si se solicita: evita reconstruir todo cada vez.
if [[ "${ZUNPI_LIMPIAR:-0}" == "1" ]]; then flutter clean; fi
flutter pub get
flutter analyze
# Profile mide fluidez real sin el coste del modo debug. Para depurar usar flutter run.
echo 'En la aplicación tocá Usar USB y luego Comprobar. Dirección: http://127.0.0.1:8001'
flutter run --profile --no-pub -d "$dispositivo_zunpi"
