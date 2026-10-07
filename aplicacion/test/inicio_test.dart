import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:zunpi/pantallas/inicio.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  testWidgets('inicio individual sin QR ni salas', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: Inicio()));
    await tester.pumpAndSettle();
    expect(find.text('Abrir juego'), findsOneWidget);
    expect(find.textContaining('Crear sala'), findsNothing);
    expect(find.byIcon(Icons.qr_code_2), findsNothing);
    expect(find.byIcon(Icons.qr_code_scanner), findsNothing);
    final campo = tester.widget<TextField>(find.byType(TextField));
    expect(campo.readOnly, isTrue);
    expect(campo.controller!.text, 'http://127.0.0.1:8001');
  });

  testWidgets('Wi-Fi permite ingresar la dirección de la PC', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: Inicio()));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Wi-Fi'));
    await tester.pumpAndSettle();
    expect(tester.widget<TextField>(find.byType(TextField)).readOnly, isFalse);
    await tester.enterText(find.byType(TextField), 'http://192.168.1.50:8001');
    expect(
      tester.widget<TextField>(find.byType(TextField)).controller!.text,
      'http://192.168.1.50:8001',
    );
  });
}
