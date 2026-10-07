// Conversión sin dispositivo: evita regresiones de strides, espejo y rotación.
import 'dart:isolate';
import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as imagen;
import 'package:zunpi/servicios/conversor_camara.dart';

Map cuadro({int giro = 0, bool espejo = false, bool oscuro = false}) {
  const ancho = 16, alto = 8;
  // Filas con relleno; el plano U/V tiene pixel stride 2 como muchos Android.
  final y = Uint8List(20 * alto)..fillRange(0, 20 * alto, oscuro ? 16 : 235);
  final u = Uint8List(20 * (alto ~/ 2))..fillRange(0, 20 * (alto ~/ 2), 128);
  final v = Uint8List.fromList(u);
  return {'ancho': ancho, 'alto': alto, 'rotacion': giro, 'espejo': espejo, 'formato': 'yuv420',
    'planos': [{'datos': TransferableTypedData.fromList([y]), 'fila': 20, 'pixel': 1},
      {'datos': TransferableTypedData.fromList([u]), 'fila': 20, 'pixel': 2},
      {'datos': TransferableTypedData.fromList([v]), 'fila': 20, 'pixel': 2}]};
}

void main() {
  test('JPEG blanco respeta padding y stride de crominancia', () {
    final foto = imagen.decodeJpg(codificarCuadro(cuadro()))!;
    expect(foto.width, 16); expect(foto.height, 8);
    expect(foto.getPixel(15, 7).r, greaterThan(245));
    expect(foto.getPixel(15, 7).g, greaterThan(245));
  });
  test('luminancia negra conserva el rango YUV', () {
    final foto = imagen.decodeJpg(codificarCuadro(cuadro(oscuro: true)))!;
    expect(foto.getPixel(0, 0).r, lessThan(10));
  });
  test('rotación frontal o trasera entrega JPEG vertical', () {
    for (final giro in [90, 270]) {
      final foto = imagen.decodeJpg(codificarCuadro(cuadro(giro: giro, espejo: giro == 270)))!;
      expect(foto.width, 8); expect(foto.height, 16);
    }
  });
  test('formato desconocido devuelve error en vez de esperar indefinidamente', () {
    final datos = cuadro()..['formato'] = 'unknown';
    expect(() => codificarCuadro(datos), throwsStateError);
  });
}
