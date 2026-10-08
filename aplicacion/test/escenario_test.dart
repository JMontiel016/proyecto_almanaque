import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:zunpi/juego/escenario.dart';

Map<String, dynamic> estado(String fase,
        {bool pausa = false, bool manual = false}) =>
    {
      'estado': fase,
      'pausada': pausa,
      'pausa_manual': manual,
      'cuenta': 2.2,
      'recorrido': 80.0,
      'velocidad': 1.0,
      'jugadores': [
        {
          'identificador': 'local',
          'nombre': 'Jugador',
          'vivo': true,
          'altura': 0.0,
          'impulso': 0.0,
          'agachado': false
        }
      ],
      'obstaculos': [
        {'tipo': 'suelo', 'x': 330.0, 'alto': 52, 'ancho': 26},
        {'tipo': 'aereo', 'x': 520.0, 'y': 38, 'alto': 24, 'ancho': 40},
      ],
    };

Widget pantalla(Map<String, dynamic> datos,
        {Key? captura, double ancho = 390, double alto = 240}) =>
    MaterialApp(
        home: Scaffold(
            body: Center(
                child: RepaintBoundary(
                    key: captura,
                    child: SizedBox(
                        width: ancho,
                        height: alto,
                        child: Escenario(estado: datos, propio: 'local'))))));

void main() {
  testWidgets('instrucciones de calibración visibles', (tester) async {
    await tester.pumpWidget(pantalla(estado('espera')));
    expect(find.text('Tu cuerpo controla el juego'), findsOneWidget);
    expect(find.textContaining('Calibrá de pie'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
  testWidgets('cuenta regresiva y fin de ronda comprensibles', (tester) async {
    await tester.pumpWidget(pantalla(estado('cuenta')));
    expect(find.text('3'), findsOneWidget);
    await tester.pumpWidget(pantalla(estado('terminada')));
    expect(find.text('¡Buen intento!'), findsOneWidget);
    expect(find.textContaining('Volver a jugar'), findsOneWidget);
  });
  testWidgets('pausa distingue botón y cuerpo perdido', (tester) async {
    await tester
        .pumpWidget(pantalla(estado('jugando', pausa: true, manual: true)));
    expect(find.textContaining('continuar'), findsOneWidget);
    await tester.pumpWidget(pantalla(estado('jugando', pausa: true)));
    expect(find.textContaining('ambos pies visibles'), findsOneWidget);
  });
  testWidgets('dibujo vectorial funciona en distintos tamaños', (tester) async {
    for (final tamano in [
      const Size(320, 180),
      const Size(390, 260),
      const Size(600, 320)
    ]) {
      await tester.pumpWidget(pantalla(estado('jugando'),
          ancho: tamano.width, alto: tamano.height));
      await tester.pump(const Duration(milliseconds: 16));
      expect(tester.takeException(), isNull);
    }
    await tester.pumpWidget(const SizedBox());
  });
  testWidgets('render del juego para inspección visual', (tester) async {
    final key = GlobalKey();
    await tester.pumpWidget(
        pantalla(estado('jugando'), captura: key, ancho: 390, alto: 260));
    await tester.pump(const Duration(milliseconds: 16));
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });
}
