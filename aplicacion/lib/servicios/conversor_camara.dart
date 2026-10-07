// Reduce y comprime cuadros en un isolate persistente: la interfaz nunca procesa píxeles.
import 'dart:async'; // Una respuesta pendiente por cuadro.
import 'dart:isolate'; // Hilo Dart dedicado y transferencia de buffers.
import 'dart:math'; // Tamaño reducido proporcional.
import 'dart:typed_data'; // Datos de cámara y JPEG.
import 'package:camera/camera.dart'; // Planos de imagen Android.
import 'package:image/image.dart' as imagen; // Codificación JPEG; no detecta personas.

class ConversorCamara {
  Isolate? _trabajador; // Se crea una sola vez por pantalla.
  SendPort? _entrada; // Puerto del hilo de píxeles.
  final _salida = ReceivePort(); // Resultados, sin acceso a widgets.
  StreamSubscription<dynamic>? _escucha; // Escucha de resultados.
  Completer<Uint8List>? _pendiente; // Como máximo un cuadro en conversión.
  bool _cerrado = false; // Impide trabajo tras salir.

  Future<void> iniciar() async {
    final listo = Completer<void>(); // Confirmación de arranque.
    _escucha = _salida.listen((dynamic respuesta) {
      if (respuesta is SendPort) {
        _entrada = respuesta;
        listo.complete();
      } else {
        final pendiente = _pendiente;
        _pendiente = null;
        if (pendiente == null || pendiente.isCompleted) return;
        if (respuesta is TransferableTypedData) {
          pendiente.complete(respuesta.materialize().asUint8List());
        } else {
          pendiente.completeError(StateError('$respuesta'));
        }
      }
    });
    _trabajador = await Isolate.spawn(_convertir, _salida.sendPort); // Reutiliza hilo durante toda la sesión.
    if (_cerrado) { _trabajador?.kill(priority: Isolate.immediate); return; }
    await listo.future.timeout(const Duration(seconds: 3));
  }

  Future<Uint8List> convertir(CameraImage cuadro, int rotacion, bool espejo) {
    if (_cerrado || _entrada == null || _pendiente != null) throw StateError('Conversor ocupado o cerrado.');
    _pendiente = Completer<Uint8List>();
    final espera = _pendiente!.future;
    _entrada!.send({
      'ancho': cuadro.width, 'alto': cuadro.height, 'rotacion': rotacion, 'espejo': espejo,
      'formato': cuadro.format.group.name,
      'planos': cuadro.planes.map((p) => {
        'datos': TransferableTypedData.fromList([p.bytes]), // Copia antes de que Android reutilice el cuadro.
        'fila': p.bytesPerRow, 'pixel': p.bytesPerPixel ?? 1,
      }).toList(),
    });
    return espera; // Backpressure: nunca crea una cola de imágenes.
  }

  void cerrar() {
    _cerrado = true;
    _trabajador?.kill(priority: Isolate.immediate);
    _escucha?.cancel();
    _salida.close();
    if (_pendiente != null && !_pendiente!.isCompleted) _pendiente!.completeError(StateError('Cámara cerrada.'));
    _pendiente = null;
  }
}

void _convertir(SendPort respuesta) {
  final entrada = ReceivePort(); // Bucle exclusivo para cuadros admitidos.
  respuesta.send(entrada.sendPort);
  entrada.listen((dynamic valor) {
    try {
      respuesta.send(TransferableTypedData.fromList([codificarCuadro(valor as Map)]));
    } catch (error) {
      respuesta.send('No se pudo convertir la cámara: $error'); // Resuelve siempre el cuadro pendiente.
    }
  });
}

// Función pura comprobable sin abrir hardware; recibe planos ya copiados.
Uint8List codificarCuadro(Map datos) {
  final ancho = datos['ancho'] as int, alto = datos['alto'] as int;
  final planos = (datos['planos'] as List).cast<Map>();
  final buffers = planos.map((p) => (p['datos'] as TransferableTypedData).materialize().asUint8List()).toList();
  final escala = min(1.0, 480 / max(ancho, alto)); // HD queda en preview; Python recibe hasta 480 px.
  final w = max(1, (ancho * escala).round()), h = max(1, (alto * escala).round());
  var foto = imagen.Image(width: w, height: h); // Solo crea el tamaño de inferencia.
  final formato = datos['formato'] as String;
  if (formato != 'yuv420' && formato != 'bgra8888' && formato != 'nv21') throw StateError('Formato de cámara no soportado: $formato');
  if (formato == 'yuv420' && planos.length != 3) throw StateError('Se esperan tres planos YUV420.');
  for (var y = 0; y < h; y++) {
    final sy = min(alto - 1, (y / escala).floor());
    for (var x = 0; x < w; x++) {
      final sx = min(ancho - 1, (x / escala).floor());
      if (formato == 'bgra8888') {
        final i = sy * (planos[0]['fila'] as int) + sx * 4;
        foto.setPixelRgb(x, y, buffers[0][i + 2], buffers[0][i + 1], buffers[0][i]);
      } else {
        final int u, v, luminancia;
        if (formato == 'nv21') {
          final i = ancho * alto + (sy ~/ 2) * ancho + (sx ~/ 2) * 2;
          luminancia = buffers[0][sy * ancho + sx];
          v = buffers[0][i] - 128; u = buffers[0][i + 1] - 128;
        } else {
          luminancia = buffers[0][sy * (planos[0]['fila'] as int) + sx * (planos[0]['pixel'] as int)];
          u = buffers[1][(sy ~/ 2) * (planos[1]['fila'] as int) + (sx ~/ 2) * (planos[1]['pixel'] as int)] - 128;
          v = buffers[2][(sy ~/ 2) * (planos[2]['fila'] as int) + (sx ~/ 2) * (planos[2]['pixel'] as int)] - 128;
        }
        final l = max(0, luminancia - 16) * 1.164; // YUV de rango limitado Android.
        foto.setPixelRgb(x, y, (l + 1.596 * v).round().clamp(0, 255),
          (l - .392 * u - .813 * v).round().clamp(0, 255), (l + 2.017 * u).round().clamp(0, 255));
      }
    }
  }
  final giro = datos['rotacion'] as int;
  if (giro != 0) foto = imagen.copyRotate(foto, angle: giro); // Sensor a vertical, sin EXIF ambiguo.
  if (datos['espejo'] == true) foto = imagen.flipHorizontal(foto); // Solo la frontal usa espejo.
  return imagen.encodeJpg(foto, quality: 70);
}
