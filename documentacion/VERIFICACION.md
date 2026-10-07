# Verificación en Android real

## Pruebas disponibles

Pasaron33 pruebas Python sin dependencias externas, usando simulaciones para modelo/transporte. No certifican inferencia real ni FPS:

```bash
python3 -m unittest discover -s servidor/pruebas -v
```

Con Flutter instalado:

```bash
cd aplicacion
flutter pub get
flutter analyze
flutter test
```

Incluye cuatro pruebas Dart del JPEG YUV: filas con relleno, chroma pixel stride2, luminancia y giro vertical. Quedaron pendientes aquí por ausencia de SDK.

## Prueba física

1. Reiniciá Python0.4 en8001. Comprobá salud e instalá por `probar_android_usb.sh` en profile. No pulses Ctrl+C mientras resuelve paquetes/compila.
2. Ingresá nombre y comprobá USB. Debe mostrar latencia y versión0.4.0. Dejá de usar la IP antigua si cambió tu Wi-Fi.
3. Abrí Jugar. El video debe moverse aun cuando la inferencia esté lenta. Verificá cabeza/pies con buena luz y completá12 muestras quieto.
4. Mirá alineación de esqueleto en frontal y trasera. Probá20 cambios de cámara: nunca deben quedar dos sensores abiertos ni pedir permiso repetidamente. Comprobá orientación vertical y espejo frontal.
5. Estoy listo/Jugar. Saltar debe disparar una vez, levantar un pie/agacharse no; aterrizar permite otro salto. Una colisión termina una vida y deja reiniciar al terminar todos.
6. Creá una sala desde inicio, sin abrir la cámara. Debe mostrar QR con logo. Otro celular ingresa nombre y escanea; no escribe dirección/sala. Probá lectura con brillo bajo y desde distintas distancias.
7. Repetí invitación con anfitrión USB y amigo Wi-Fi: la IP del QR debe ser la LAN de la PC. Abrí `/salud` en el navegador del amigo. Si hay VPN/Docker, seleccioná la interfaz correcta.
8. Ingresá hasta4 teléfonos, confirmá todos y verificá mismo recorrido. Si uno pierde el cuerpo, pausa común. Si sale el administrador, transfiere rol. No permite entrar durante la ronda.
9. Minimizá/volvé cinco veces. Para ausencias mayores25s puede cerrarse la sesión; la app informa reconexión desde inicio. El cambio de sensor debe recalibrar.
10. Cortá el servidor en mitad del juego. Debe mostrar desconexión; no llenar memoria ni bloquear la navegación. Una inferencia sin respuesta cierra como máximo tras8s, más el intervalo del vigilante.
11. Revisá ranking tras morir y reiniciar servidor: conserva mejor marca por nombre. Revisá launcher: usa logoZunpi.

## Medición de fluidez

Usá profile; debug incluye sobrecosto. Observá Performance/Memory de Flutter DevTools y consumo CPU/RAM Python mientras jugás10min. Medí con1 y4 jugadores: cuadros de UI lentos, memoria después de ciclos de cámara, latencia Python y saltos omitidos. La vista HD es nativa; el esqueleto se actualiza a la frecuencia de inferencia.

Objetivo de referencia para pantalla60Hz: la mayoría de cuadros de interfaz dentro de16,7ms, sin crecimiento continuo de memoria. Es un objetivo de prueba, no un resultado obtenido. Separá el tiempo de instalar/compilar, conectar HTTP, cargar modelo y calibrar. Ningún tiempo total/FPS se certificó con tu teléfono en este entorno.

Si falla, compartí texto exacto de `flutter analyze`/`flutter run`, terminal Python y la latencia visible, indicando frontal o trasera y USB/Wi-Fi.
