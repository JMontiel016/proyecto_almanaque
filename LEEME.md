# Zunpi 0.4

Dinosaurio Android controlado con saltos corporales. Juego arriba y cámara abajo. Flutter presenta el juego; Python detecta personas y saltos en una computadora. ESP32/OLED opcional muestra nombres y puntajes. Este paquete contiene código fuente, no un APK compilado.

Si ya tenés Zunpi, seguí **ACTUALIZAR.md**: conserva tu entorno, modelo, Android generado y ranking.

## Primera instalación

En la carpeta `Zunpi/servidor`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python descargar_modelo.py
python -m uvicorn servidor:app --host 0.0.0.0 --port 8001 --workers 1
```

Dejá esa terminal abierta. En otra terminal, desde `Zunpi`:

```bash
flutter doctor
flutter doctor --android-licenses
bash preparar_android.sh
bash probar_android_usb.sh AM4U9X4724G01019
```

Requiere Flutter/Dart >=3.6, Android SDK y Android API24 o superior. El script genera los archivos Android con tu versión de Flutter, aplica permisos/icono y analiza el proyecto. El script USB configura ADB reverse y ejecuta profile sin limpiar cada vez. Acepta el número de serie de otro teléfono como argumento.

## Conexión

- **USB:** mantené el cable conectado y el puente ADB activo. En inicio elegí USB y comprobá conexión. El servidor configurado es `http://127.0.0.1:8001`.
- **Wi-Fi:** PC y teléfonos en la misma red. Ejecutá `hostname -I` en la PC y configurá en inicio `http://IP_WIFI_DE_LA_PC:8001`. Desde el navegador del celular, `/salud` debe mostrar Zunpi versión 0.4.0. Las IP de Docker/VPN pueden no servir para el teléfono.
- El servidor corre en la PC, no en el ESP32 ni dentro del APK. La app instalada no precisa internet para jugar si el modelo y paquetes ya están disponibles.

## Partida

Ingresá tu nombre y tocá **Jugar**. La cámara nativa solicita HD; Python recibe JPEG pequeños orientados y devuelve articulaciones, no video. Mostrá cabeza y ambos pies, dejá espacio arriba para saltar y calibrá quieto hasta 12/12. Confirmá **Estoy listo**; el administrador toca **Jugar**.

Una vida por ronda. Saltá para esquivar los cactus; agacharte o levantar un solo pie no cuenta. Una colisión termina tu intento. Al terminar todos, confirmen para otra ronda. Puntos: 25/s de tiempo activo; cada 500 multiplica velocidad ×1,5 hasta ×4. Perder seguimiento pausa la ronda común.

El botón de cámaras cambia frontal/trasera y recalibra. Cada persona usa la cámara de su propio celular. La escena interpola estados de Python; el servidor decide colisiones y puntos.

## Invitaciones exclusivamente QR

**Crear sala e invitar por QR** reserva una sala y muestra un QR con el logo. Luego entrá a la sala. También podés invitar entre rondas desde la partida. La primera persona que conecta administra; el rol se transfiere si sale.

Los amigos ingresan su nombre y tocan **Escanear QR de un amigo**. No hay ingreso manual de sala. Máximo cuatro jugadores en una sala y doce conexiones en este prototipo. No se admiten jugadores durante una ronda.

El QR carga dirección y sala; requiere la app instalada y una red que llegue a la PC. Con anfitrión por USB, consulta la dirección LAN de la PC para compartirla. Si aparece una interfaz incorrecta, seleccioná otra dirección del listado o configurá Wi-Fi en inicio. La reserva vence en diez minutos si nadie entra.

## Ranking y logo

Ranking por nombre normalizado: Jaime y JAIME comparten mejor marca; ñ y acentos se conservan. Está compartido por clientes de **este servidor**, sin despliegue mundial. Elegí nombres distintos para distinguir personas. SQLite conserva `servidor/datos/ranking.sqlite3`; conservá esa carpeta al actualizar. `ZUNPI_DATOS` permite otra ruta. Migra registros anteriores sin borrar la tabla original.

El launcher y el centro del QR usan el icono geométrico Zunpi creado para el proyecto. Recursos e información CC0 en `aplicacion/assets/LICENCIA_ICONO.txt`. No se garantiza exclusividad de marca o nombre. No hay imágenes, fuentes o música comerciales incorporadas.

## Organización

| Archivo/carpeta | Función |
|---|---|
| aplicacion/lib/main.dart | Tema Material3 y orientación |
| aplicacion/lib/pantallas/inicio.dart | Conexión, nombre, invitaciones y ranking |
| aplicacion/lib/pantallas/invitacion.dart | QR con logo y consulta de dirección LAN |
| aplicacion/lib/pantallas/partida.dart | Cámara directa, lifecycle y controles |
| aplicacion/lib/servicios/conversor_camara.dart | JPEG reducido en isolate persistente |
| aplicacion/lib/servicios/conexion.dart | WebSocket, contrapresión y diagnóstico |
| aplicacion/lib/juego/escenario.dart | Lienzo animado e interpolación |
| servidor/seguimiento.py | Inferencia Python y articulaciones normalizadas |
| servidor/detector_salto.py | Calibración corporal y salto |
| servidor/servidor.py | API, sesiones, roles y motor común |
| servidor/buzon.py | Cola con último estado y acuses protegidos |
| servidor/motor.py | Física y una vida por ronda |
| servidor/almacenamiento.py | Ranking por nombre en SQLite |

Los nombres propios y comentarios están en español. Los métodos/archivos obligatorios de Flutter y APIs conservan los nombres de su framework. Se documentan bloques, fórmulas y decisiones para extenderlos.

## Verificar y compilar

```bash
python3 -m unittest discover -s servidor/pruebas -v
cd aplicacion
flutter pub get
flutter analyze
flutter test
flutter run --profile -d AM4U9X4724G01019
```

No hay SDK Flutter/Android ni cámara/modelo real en el entorno de entrega. Pasaron 33 pruebas Python simuladas; las pruebas Flutter incluidas y la verificación física siguen pendientes en tu equipo. No se promete una cantidad de FPS ni tiempos totales sin medición. La primera instalación/compilación y carga del modelo pueden tardar más que abrir el juego.

Para un APK de distribución local tras validar:

```bash
flutter build apk --release
```

La configuración de firma y publicación en Google Play requiere trabajo aparte. Guía física: `documentacion/VERIFICACION.md`. Contrato de mensajes: `documentacion/PROTOCOLO.md`.

## ESP32/OLED opcional

`esp32/pantalla_oled.ino` consulta `/oled/CODIGO` cada segundo. Su configuración técnica conserva un identificador interno de sala; los jugadores de Android entran exclusivamente por QR. No se modifica firmware en esta actualización.

Confirmá modelo de placa, GPIO libres y OLED antes de cablear. El sketch usa como ejemplo ESP32 clásico SDA21/SCL22, SSD1306 128×64/128×32, ArduinoJson7 y Adafruit GFX/SSD1306. ESP32-CAM puede tener esos GPIO ocupados; SH1106 requiere otro driver. Ajustá puerto a8001 y la IP actual. Cuatro nombres/puntos en128×64; paginación de dos en128×32. El ESP32 no analiza cámaras ni administra salas.

Referencias: https://pub.dev/packages/camera, https://pub.dev/documentation/image/latest/image y https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python.
