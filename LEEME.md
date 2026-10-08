# Zunpi 0.6 · Saltá y agachate

Juego Android con Flutter: saltá los cactus y agachate ante las aves.
La cámara del celular envía JPEG de hasta 480 px a Python, que ejecuta
MediaPipe Pose Lite. No hay QR, salas, ranking ni conexión ESP32.

## Actualizar un proyecto anterior

Detener Python y Flutter con Ctrl+C. Extraer el ZIP en una carpeta aparte.
Desde la raíz del proyecto anterior:

```bash
python3 /RUTA/Zunpi_mejorado/instalar_actualizacion.py
```

El instalador crea respaldo y retira el archivo QR antiguo que puede quedar al
copiar carpetas encima. No borra el entorno Python, el modelo ni los datos locales.
No hace falta ejecutar preparar_android.sh si ya ejecutabas la versión anterior.
Reiniciar Python y ejecutar `bash probar_android_usb.sh` en otra terminal.
La versión nueva exige servidor 0.6.0 para que el botón Pausar funcione.

## Vista y controles

Dinosaurio, cactus y aves se dibujan como curvas vectoriales con suavizado,
sin sprites pixelados ni paquetes gráficos adicionales. La vista del mundo está
más cerca para ver mejor los obstáculos. La física y las colisiones siguen en Python.
No se cambió la frecuencia del servidor ni se aumentó el tamaño JPEG para detección.

- Cactus: saltá. Aves: agachate.
- Pausar/Continuar: detiene recorrido y puntaje. Con cuerpo perdido sigue pausado.
- Ajustar vista: cámara Fluida por defecto; Nítida para más detalle si el celular lo permite.
- Mostrar puntos: opcional para diagnóstico; sin cara, ocultos por defecto.
- Calibración: barra de 12 muestras, permanecé de pie y quieto.
- Cuenta regresiva y mensajes de pausa/fin visibles sobre el juego.

La vista Nítida aumenta el trabajo de cámara/copia en el celular; si hay trabas,
volver a Fluida. El procesador recibe JPEG de hasta 480 px en ambos modos.

## Preparar Python en Linux

Desde la raíz del proyecto:

```bash
python3 -m venv servidor/.venv
servidor/.venv/bin/pip install -r servidor/requirements.txt
```

El modelo Lite ya está incluido; si falta:

```bash
cd servidor
.venv/bin/python descargar_modelo.py
cd ..
```

Iniciar (un solo worker):

```bash
bash servidor/iniciar.sh
```

Si el puerto 8001 está ocupado, detené la instancia anterior con Ctrl+C.

## Celular Android

Instalar Flutter/Android SDK, activar depuración USB y autorizar el celular.
Si faltan los archivos Gradle generados: `bash preparar_android.sh`.

Con Python iniciado, en otra terminal:

```bash
bash probar_android_usb.sh
```

El script elige el único celular autorizado; con varios, pasar su ID como argumento.
Usa `flutter run --profile` para medir rendimiento sin el coste del modo debug.

Manual:

```bash
adb reverse tcp:8001 tcp:8001
cd aplicacion
flutter pub get
flutter analyze
flutter run --profile
```

En el inicio seleccionar USB y Abrir juego. Mantenerse de pie y quieto hasta
completar 12 muestras de calibración; luego tocar Jugar.
Para Wi-Fi, PC y celular en la misma red: usar `http://IP_DE_LA_PC:8001` y
comprobar `/salud` en el navegador del celular. Python escucha en `0.0.0.0`.

## Detección y rendimiento

Se usan hombros, caderas, rodillas y tobillos. No se exige ni dibuja la cara.
Pose Lite calcula internamente 33 puntos: no permite desactivar solo los faciales.
No hay FaceMesh ni un detector facial separado. Los índices faciales se envían
con confianza cero por compatibilidad del esqueleto.

VIDEO conserva seguimiento temporal de una única persona/cámara. No se generan
máscaras de segmentación. Cámara media, compresión fuera del hilo de interfaz y
una sola imagen pendiente: se descartan cuadros mientras Python está ocupado.
La vista de cámara es nativa, independiente de la frecuencia de inferencia.

Salto: suben cadera y ambos tobillos respecto de la calibración; no hay dobles
eventos en el aire. Agachado: baja la cadera con pies apoyados y se usa histéresis.
La cámara debe estar fija. Mala iluminación, cuerpo fuera del cuadro o calibrar
agachado pueden perjudicar la precisión. La escala no cambia durante el movimiento.
A partir de 100 puntos pueden aparecer aves; agacharse no evita los cactus.
El puntaje se conserva durante la partida y se reinicia al volver a jugar.

## Verificación

```bash
python3 -m unittest discover -s servidor/pruebas -v
cd aplicacion
flutter test
flutter analyze
```

Prueba manual: 10 saltos, 5 agachados, 5 pasos con un solo pie y 10 s quieto.
Revisar saltos perdidos, duplicados y falsos positivos. Probar una ronda de 5 minutos
por USB y Wi-Fi. No se garantiza el mismo rendimiento en cualquier dispositivo.

## Limpieza

Se quitó `venv/` del seguimiento de Git (unos 273 MB), el prototipo `camara.py`,
QR y scanner, salas, ranking, ESP32 y documentación obsoleta. Se conservan recursos
Android necesarios, el modelo y las pruebas. `.gitignore` impide agregar entornos
nuevos. El historial anterior de Git todavía contiene la venv; no se reescribió.
