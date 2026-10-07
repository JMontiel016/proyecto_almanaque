// Entrada exigida por Flutter; las pantallas y variables propias están en español.
import 'package:flutter/material.dart'; // Widgets de interfaz.
import 'package:flutter/services.dart'; // Orientación del dispositivo.
import 'pantallas/inicio.dart'; // Inicio del sistema.

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized(); // Inicializa plugins antes de usarlos.
  await SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]); // Juego sobre cámara.
  runApp(const Zunpi()); // Inicia la aplicación.
}

class Zunpi extends StatelessWidget {
  const Zunpi({super.key}); // Constructor inmutable.
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'Zunpi', // Nombre corto del juego.
    debugShowCheckedModeBanner: false, // Interfaz limpia.
    theme: ThemeData(
      brightness: Brightness.dark, // Fondo oscuro con contraste.
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFFA7EF5B), brightness: Brightness.dark), // Acento verde.
      scaffoldBackgroundColor: const Color(0xFF10171E), // Fondo principal.
      useMaterial3: true, // Controles modernos.
      inputDecorationTheme: InputDecorationTheme(filled: true, fillColor: const Color(0xFF17222C),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(14))),
      filledButtonTheme: FilledButtonThemeData(style: FilledButton.styleFrom(minimumSize: const Size(0, 50),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)))),
      outlinedButtonTheme: OutlinedButtonThemeData(style: OutlinedButton.styleFrom(minimumSize: const Size(0, 50),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)))), // Formularios claros.
    ),
    home: const Inicio(), // Primera pantalla.
  );
}
