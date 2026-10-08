// Conexión confirmada: salud, conexión y detector preparado antes de capturar.
import 'dart:async'; // Espera de inicialización con tiempo límite.
import 'dart:convert'; // Mensajes JSON pequeños.
import 'dart:io'; // WebSocket Android.
import 'package:flutter/foundation.dart'; // Estado observable y Uint8List.
import 'package:http/http.dart' as http; // Diagnóstico antes de abrir cámara.

class Conexion extends ChangeNotifier {
  WebSocket? canal; // Transporte activo.
  StreamSubscription<dynamic>? suscripcion; // Escucha única.
  Map<String, dynamic> estado = {}; // Juego autoritativo.
  final vision = ValueNotifier<Map<String, dynamic>>({}); // Pose: no reconstruye toda la pantalla.
  String identificador = ''; // Identificador local.
  String mensaje = 'Comprobando servidor Python…', error = ''; // Estado visible.
  bool cuerpoListo = false, ocupado = false, conectado = false, detectorListo = false; // Fases separadas.
  DateTime envio = DateTime.now(); // Último cuadro enviado.
  int demora = 0, calibracion = 0; // Diagnóstico visual.
  Timer? vigilancia; // Tiempo máximo de una imagen pendiente.
  bool cerrado = false; // Bloquea eventos tras cerrar.
  Completer<void>? preparacion; // Espera explícita a detector_listo.

  void avisar() {
    if (!cerrado) notifyListeners(); // Notifica solo a una pantalla viva.
  }
  void fallar(String detalle) {
    error = detalle; // Conserva error completo, no solo dos líneas.
    mensaje = detalle; // Estado principal también explica fallo.
    ocupado = false; // No deja cámara esperando para siempre.
    if (preparacion != null && !preparacion!.isCompleted) preparacion!.completeError(StateError(detalle)); // Desbloquea apertura.
    avisar();
  }

  Future<void> abrir(String servidor) async {
    preparacion = Completer<void>(); // Nuevo intento de conexión.
    final confirmado = preparacion!.future; // Instala espera antes de cualquier callback.
    unawaited(confirmado.catchError((Object _) {})); // Consume errores aun si la pantalla cierra durante preparación.
    try {
      final salud = await http.get(Uri.parse('$servidor/salud')).timeout(const Duration(seconds: 2)); // Confirma API correcta.
      if (salud.statusCode != 200) throw StateError('Ese puerto no es el servidor Zunpi (/salud: HTTP ${salud.statusCode}).');
      final datos = jsonDecode(salud.body) as Map<String,dynamic>; // Datos de versión/modelo.
      if (datos['juego'] != 'Zunpi') throw StateError('La dirección pertenece a otro servicio.');
      if (datos['version'] != '0.6.0') throw StateError('Actualizá y reiniciá el servidor Python con los versión individual 0.6.0.');
      if (datos['modelo'] != true) throw StateError('Falta modelo corporal: ejecutá python descargar_modelo.py en la computadora.');
      if (cerrado) return; // Usuario ya salió.
      mensaje = 'Servidor correcto. Conectando juego…';
      avisar();
      final direccion = Uri.parse(servidor); // Base validada.
      final destino = direccion.replace(scheme: direccion.scheme == 'https' ? 'wss' : 'ws', path: '/conexion', query: null); // Canal correcto.
      canal = await WebSocket.connect(destino.toString()).timeout(const Duration(seconds: 2)); // Handshake con límite.
      if (cerrado) { await canal?.close(); return; }
      vigilancia = Timer.periodic(const Duration(seconds: 1), (_) {
        if (!cerrado && ocupado && DateTime.now().difference(envio).inSeconds >= 8) {
          conectado = detectorListo = false;
          fallar('Python no respondió a la cámara en 8 s. Volvé al inicio y comprobá el servidor.');
          vigilancia?.cancel(); canal?.close(); // No libera el bloqueo para enviar imágenes duplicadas.
        }
      });
      canal!.pingInterval = const Duration(seconds: 10); // Detecta desconexión.
      suscripcion = canal!.listen((dynamic datos) {
        if (cerrado) return;
        try {
          final respuesta = Map<String,dynamic>.from(jsonDecode(datos as String) as Map); // Contrato de red.
          switch (respuesta['tipo']) {
            case 'bienvenida':
              identificador = respuesta['identificador'] as String; // Identidad confirmada.
              conectado = true;
              mensaje = 'Juego conectado. Preparando detector…';
              break;
            case 'preparando':
              mensaje = respuesta['mensaje'] as String;
              break;
            case 'detector_listo':
              detectorListo = true; // Captura habilitada recién aquí.
              mensaje = 'Detector conectado. Mostrá el cuerpo completo.';
              if (!preparacion!.isCompleted) preparacion!.complete();
              break;
            case 'estado':
              estado = respuesta; // Separa física de cámara.
              break;
            case 'vision':
              ocupado = false; // Siguiente cuadro.
              demora = DateTime.now().difference(envio).inMilliseconds;
              cuerpoListo = respuesta['listo'] == true;
              mensaje = respuesta['mensaje'] as String? ?? 'Esperando cuerpo';
              calibracion = (respuesta['calibracion'] as num?)?.toInt() ?? 0;
              vision.value = {...respuesta, 'demora': demora}; // Solo panel de cámara y texto.
              return;
            case 'error':
              fallar(respuesta['mensaje'] as String? ?? 'Falló el detector Python.');
              break;
          }
          avisar();
        } catch (problema) {
          fallar('Respuesta inválida del servidor: $problema'); // No queda cámara muda.
        }
      }, onError: (Object problema) {
        vigilancia?.cancel();
        conectado = detectorListo = false;
        fallar('Conexión perdida: $problema');
      }, onDone: () {
        vigilancia?.cancel();
        conectado = detectorListo = false;
        if (!cerrado) fallar(error.isNotEmpty ? error : 'Servidor desconectado. Volvé al inicio y reconectá.');
      });
      canal!.add(jsonEncode({'nombre':'Jugador'})); // Saludo después de escuchar.
      await confirmado.timeout(const Duration(seconds: 35)); // Detector nunca espera infinito.
    } catch (problema) {
      // No completa con error sin consumidor: los errores previos al WebSocket se propagan directamente.
      error = problema is TimeoutException ? (conectado ? 'El modelo Python tardó demasiado en prepararse. Revisá la terminal del servidor.' : 'No se pudo conectar. Revisá Wi-Fi/IP o el puente USB.') : 'No se pudo conectar: $problema';
      mensaje = error;
      conectado = detectorListo = false;
      vigilancia?.cancel();
      await canal?.close();
      avisar();
      rethrow;
    }
  }

  void enviarImagen(Uint8List bytes) {
    if (!conectado || !detectorListo || ocupado || identificador.isEmpty) return;
    ocupado = true; // Una sola inferencia pendiente.
    envio = DateTime.now();
    canal?.add(bytes); // Python recibe JPEG, no puntos ni saltos falsificados.
  }
  void accion(String nombre) {
    if (conectado && detectorListo) canal?.add(jsonEncode({'accion':nombre}));
  }
  @override
  void dispose() {
    cerrado = true;
    vigilancia?.cancel();
    suscripcion?.cancel();
    canal?.close();
    vision.dispose();
    super.dispose();
  }
}
