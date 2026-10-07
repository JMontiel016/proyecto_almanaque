# Protocolo Zunpi 0.4

Un proceso/worker Python conserva salas en memoria. Flutter v0.4 requiere salud versión0.4.0. El servidor precarga MediaPipe en un hilo de fondo; salud y reservas no esperan ese modelo.

## HTTP

- GET `/salud` y `/`: juego, versión, existencia del modelo y precarga terminada.
- GET `/red`: `direcciones`, lista de IPv4 de la PC. Prioriza interfaz de ruta y excluye loopback. Es ayuda para USB, no comprobación de acceso desde otros teléfonos.
- POST `/salas`, JSON `nombre`: reserva temporal, devuelve identificador interno `sala` y versión. No abre cámara/modelo; vence600s si nadie entra.
- GET `/ranking`: mejor puntaje por nombre normalizado, máximo50.
- GET `/oled/{codigo}`: nombres, puntos y estado; consulta técnica del ESP32.

## WebSocket `/conexion`

1. Flutter envía JSON `nombre`, identidad privada persistida y `sala`. Una sala vacía crea; un valor obtenido por QR/reserva se une. No existe campo manual en la app.
2. Python envía `bienvenida`: identificador público, sala y administrador. Entrega esos datos antes de cargar el modelo para habilitar invitaciones.
3. `preparando` informa carga. `detector_listo` habilita cámara. Fallos iniciales envían `error` y cierran.
4. Flutter muestra preview nativo y convierte cuadros seleccionados fuera del hilo UI. Envía JPEG binario, sin cabecera propia, hasta480px en el lado mayor/calidad70. Respeta stride de planos Android y convierte sensor a vertical; frontal reflejada, trasera sin espejo. Python no aplica otro espejo.
5. Python devuelve `vision`: `puntos` es una lista de33 triples `[x,y,visibilidad]` normalizados; `cuerpo`, `listo`, `salto`, `mensaje`, `calibracion`, `ancho`, `alto`. Sin JPEG/base64 de retorno. `puntos=[]` limpia el esqueleto cuando no hay persona. Los saltos se aplican en Python, no se aceptan eventos falsificados desde Dart.
6. Flutter admite una conversión y una imagen pendiente como máximo. Mínimo110ms entre cuadros; intervalo adaptativo según latencia hasta400ms. Python limita a10 inferencias/s por cámara. Una imagen sin respuesta durante8s cierra con diagnóstico.
7. Comandos JSON `accion`: `listo`, `iniciar`, `calibrar`. Servidor valida administrador, jugadores confirmados y seguimiento. Al cambiar cámara se recalibra.
8. Python publica `estado` a10Hz, física30Hz. Flutter interpola hasta120ms y anima solo el lienzo durante juego activo. El renderer no calcula colisiones ni puntos.

## Cola y aislamiento

`Buzon` guarda un último estado reemplazable y hasta16 mensajes de control/visión en orden. Reemplazar estado nunca pierde un acuse de cámara. El escritor prioriza controles. Cada cámara espera el acuse antes de enviar otra imagen, por lo que en uso normal no acumula respuestas.

La inferencia usa un modelo compartido y cerrojo; cada jugador conserva calibración independiente. Inferencias se serializan y pueden reducir frecuencia con varios jugadores. Lecturas/escrituras SQLite se llevan a hilos; las escrituras terminan al apagar normalmente.

Abrir/cerrar/cambiar cámara son operaciones serializadas. Se libera el escáner antes de entrar. Minimizar cierra el sensor; volver lo reabre si la conexión sigue activa. Si el servidor desconectó por inactividad25s, volvé al inicio y conectá de nuevo. Abrir QR mantiene preview pero suspende inferencia; solo se invita entre rondas desde la partida.

## QR

JSON `juego:Zunpi`, `version:1`, `servidor` y sala interna. CorrecciónH y logo central pequeño. El escáner acepta solamente ese contrato y direcciones HTTP(S) base, sin credenciales/rutas/query/fragmento. El QR no administra Wi-Fi ni instala la app. El primer conectado administra.

## Ajustes

Resolución preview: `ResolutionPreset.high`; su resolución efectiva depende del sensor. Tamaño JPEG480/calidad70: `conversor_camara.dart`. Intervalo/latencia: `partida.dart`. Detector, umbrales y calibración: Python. Si aumentás resolución o frecuencia, medí CPU, red y FPS antes de adoptarlo. Preview y pose no tienen la misma frecuencia; el esqueleto puede verse demorado.
