#!/usr/bin/env bash
# Medición REAL en Android; no simula FPS, CPU ni memoria.
set -euo pipefail
PAQUETE="${1:-py.jmontiel.zunpi}"
SALIDA="${2:-mediciones_android}"
command -v adb >/dev/null || { echo 'Falta adb (android-tools-adb).'; exit 1; }
adb get-state | grep -q device || { echo 'Conectá un dispositivo Android con depuración USB.'; exit 1; }
mkdir -p "$SALIDA"
echo "Paquete: $PAQUETE"
echo "Mantené el juego abierto mientras se recopilan 10 muestras."
adb shell dumpsys gfxinfo "$PAQUETE" reset >/dev/null || true
for n in $(seq 1 10); do
  adb shell dumpsys meminfo "$PAQUETE" > "$SALIDA/memoria_$n.txt"
  adb shell top -b -n 1 -o PID,CPU,RES,NAME > "$SALIDA/cpu_$n.txt" || true
  sleep 3
done
adb shell dumpsys gfxinfo "$PAQUETE" > "$SALIDA/fotogramas.txt"
adb shell dumpsys batterystats > "$SALIDA/bateria.txt" || true
echo "Listo: $SALIDA. FPS y jank están en fotogramas.txt; uso de RAM en memoria_*.txt."
echo "Para medir FPS renderizados correctamente, ejecutá una partida real durante el muestreo."
