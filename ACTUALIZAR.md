# Zunpi 0.4 — cámara directa e invitaciones por QR

Esta actualización modifica el código que entregamos en v0.3. No se compiló aquí un APK ni se midió tu celular. Conserva el logo propio, ranking por nombre y detección exclusivamente Python.

## Actualización en tu computadora

Detené Flutter y Python con Ctrl+C en sus terminales. El ZIP contiene una carpeta `Zunpi`. Reemplaza fuentes; no incluye ni elimina tu `.venv`, modelo, base de datos o plataforma Android existente. Si modificaste fuentes por tu cuenta, guardá una copia antes de reemplazarlas.

```bash
unzip -o ~/Descargas/Zunpi_v04.zip -d ~/Escritorio/Robotica
```

Primera terminal:

```bash
cd ~/Escritorio/Robotica/Zunpi/servidor
source .venv/bin/activate
python -m uvicorn servidor:app --host 0.0.0.0 --port 8001 --workers 1
```

Otra terminal, con el celular conectado y desbloqueado:

```bash
cd ~/Escritorio/Robotica/Zunpi
bash probar_android_usb.sh
```

Si es tu primera instalación y no existe `aplicacion/android`, ejecutá antes `bash preparar_android.sh`. Si falta el modelo, ejecutá `python descargar_modelo.py` en la terminal con la venv activa.

El script USB comprueba el servidor 0.4, configura el puente ADB, instala el icono propio, descarga paquetes, analiza Dart y ejecuta en **profile**. No ejecuta `flutter clean` en cada prueba. La primera descarga/compilación sigue tardando más que abrir la app ya instalada.

Si excepcionalmente necesitás limpiar recursos compilados:

```bash
ZUNPI_LIMPIAR=1 bash probar_android_usb.sh
```

Para depurar con breakpoints, luego de preparar el puente USB:

```bash
cd aplicacion
flutter run -d AM4U9X4724G01019
```

Ese modo debug tiene sobrecosto; compará fluidez con profile.

## En el teléfono

1. Ingresá tu nombre.
2. Seleccioná **USB → Comprobar conexión**. La app usa `http://127.0.0.1:8001` gracias al puente ADB.
3. Tocá **Jugar**. Esperá a ver la cámara y el esqueleto. Apoyá el teléfono, mostrá cabeza y pies y quedate quieto hasta calibrar 12/12.
4. **Estoy listo → Jugar**. Todos los participantes deben calibrar y confirmar; la primera persona conectada administra.
5. El botón de cámaras arriba cambia entre frontal y trasera y vuelve a calibrar. La vista mantiene proporciones, sin estirar el cuerpo.

## Invitar sin escribir códigos

Desde inicio: **Crear sala e invitar por QR**. La sala se reserva antes de cargar cámara/modelo y el QR incluye el logo propio. Cerrá el QR y entrá a la sala. También podés invitar desde el botón QR en la partida entre rondas.

Tu amigo abre Zunpi, ingresa su nombre y toca **Escanear QR de un amigo**. El escaneo carga servidor y sala, y entra automáticamente si el nombre ya está ingresado. No hay campo de código ni alternativa manual.

Todos los celulares deben tener la app y acceder a la PC por la misma red. El QR no instala la app ni conecta a una Wi-Fi. Cuando el anfitrión usa USB, el modal consulta `/red` para incluir la IPv4 de la PC, no localhost. Si hay varias interfaces, podés elegir una en la lista del QR. Una VPN, Docker o un router con aislamiento pueden requerir seleccionar **Wi-Fi** en inicio y configurar allí la dirección correcta de la PC; verificá `/salud` desde el navegador del otro teléfono.

## Qué se optimizó

- Preview nativo HD: ya no toma y guarda fotos continuamente ni espera video de vuelta desde Python.
- Convierte solo cuadros admitidos a JPEG de hasta 480 px y calidad 70 en un isolate persistente. La detección corporal continúa en Python.
- Un cuadro en conversión y una inferencia pendiente como máximo; descarta cuadros excedentes. Adapta la frecuencia a la latencia.
- Python devuelve 33 coordenadas y estado, sin recodificar imagen HD/base64. Flutter dibuja el esqueleto encima de la cámara directa.
- La cola conserva acuses de cámara y reemplaza solamente estados antiguos del juego.
- El juego repinta el lienzo sin reconstruir widgets cada cuadro. Detiene animación en espera y pausa. Cámara y juego tienen límites de repintado independientes.
- Aperturas, cierre y cambio de sensor se serializan. El escáner se detiene antes de abrir la cámara del juego.
- Guardar/leer ranking ocurre fuera del hilo de red/física. Las escrituras pendientes terminan al apagar normalmente.
- Una imagen sin respuesta durante ocho segundos cierra la conexión con diagnóstico, en vez de acumular imágenes o esperar indefinidamente.
- Diseño Material 3 con pasos claros, acciones grandes, ranking por nombre y sin bibliotecas visuales adicionales.

HD es una resolución solicitada; el dispositivo decide la disponible. La cámara en vivo y la pose tienen frecuencias diferentes: el esqueleto puede ir detrás del video. La capacidad de la PC, iluminación, red y teléfono determinan los FPS; no se promete 60 FPS ni arranque completo en dos segundos sin medirlos.

## Validación

Pasaron 33 pruebas Python con transporte y modelo simulados: reglas, saltos, ranking, migración, icono Android, reserva/handshake, cola sin pérdida de acuses y respuestas de pose sin video. También se verificó sintaxis Python y Bash.

Incluye cuatro pruebas Flutter de conversión YUV, strides y rotación. **No se ejecutaron aquí**, porque no hay SDK Flutter/Android. Ejecutalas en tu equipo:

```bash
cd ~/Escritorio/Robotica/Zunpi/aplicacion
flutter pub get
flutter analyze
flutter test
```

La detección real, alineación del esqueleto frontal/trasero, lectura física del QR, consumo de memoria y FPS deben comprobarse con tu hardware. Seguí `documentacion/VERIFICACION.md`.
