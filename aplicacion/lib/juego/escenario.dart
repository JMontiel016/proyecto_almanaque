// Dibuja dinosaurios originales con formas; sin imágenes ni recursos externos.
import 'dart:math'; // Interpolación y escala.
import 'package:flutter/material.dart'; // Lienzo y colores.
import 'package:flutter/scheduler.dart'; // Animación al ritmo de la pantalla.

class Escenario extends StatefulWidget {
  final Map<String, dynamic> estado; // Instantánea autoritativa del servidor.
  final String propio; // Dinosaurio del jugador local.
  const Escenario({super.key, required this.estado, required this.propio});
  @override
  State<Escenario> createState() => _EstadoEscenario();
}
class _EstadoEscenario extends State<Escenario> with SingleTickerProviderStateMixin {
  late final Ticker reloj; // Redibuja sin pedir inferencia a la cámara.
  final pulsos = ValueNotifier<int>(0); // Solo repinta el lienzo, sin reconstruir widgets a 60 Hz.
  DateTime recibido = DateTime.now(); // Momento del último estado de red.
  @override
  void initState() {
    super.initState();
    reloj = createTicker((_) { if (mounted) pulsos.value += 1; });
    ajustarReloj(); // Animación visual independiente.
  }
  void ajustarReloj() {
    final animar = widget.estado['estado'] == 'jugando' && widget.estado['pausada'] != true;
    if (animar && !reloj.isActive) reloj.start();
    if (!animar && reloj.isActive) reloj.stop(); // Menú, espera y pausas no gastan cuadros.
  }
  @override
  void didUpdateWidget(covariant Escenario anterior) {
    super.didUpdateWidget(anterior);
    ajustarReloj();
    if (!identical(anterior.estado, widget.estado)) recibido = DateTime.now(); // No reinicia con respuestas de cámara.
  }
  @override
  Widget build(BuildContext context) => ClipRRect(borderRadius: BorderRadius.circular(22), child: CustomPaint(
    painter: _Dibujo(widget.estado, widget.propio, recibido, pulsos), // Predicción breve.
    child: const SizedBox.expand(), // Ocupa panel superior.
  ));
  @override
  void dispose() {
    reloj.dispose();
    pulsos.dispose(); // No sigue dibujando fuera de partida.
    super.dispose();
  }
}

class _Dibujo extends CustomPainter {
  final Map<String, dynamic> estado; // Estado común.
  final String propio; // Prioriza visibilidad local.
  final DateTime recibido; // Momento del estado recibido.
  _Dibujo(this.estado, this.propio, this.recibido, Listenable pulsos) : super(repaint: pulsos);
  static const colores = [Color(0xFFA7EF5B), Color(0xFF69C7FF), Color(0xFFFFC66B), Color(0xFFE9A0FF)]; // Un color por jugador.
  void texto(Canvas canvas, String valor, Offset lugar, double tamano, Color color) {
    final pintor = TextPainter(text: TextSpan(text: valor, style: TextStyle(color: color, fontSize: tamano, fontWeight: FontWeight.w600)), textDirection: TextDirection.ltr); // Texto Unicode.
    pintor.layout(); // Mide antes de dibujar.
    pintor.paint(canvas, lugar); // Etiqueta.
  }
  @override
  void paint(Canvas canvas, Size size) {
    final demora = min(.12, DateTime.now().difference(recibido).inMilliseconds / 1000); // Interpolación en repintado.
    canvas.drawRect(Offset.zero & size, Paint()..color = const Color(0xFF1B2935)); // Cielo oscuro.
    final escala = size.width / 1000; // Mundo lógico igual para todos los celulares.
    final suelo = size.height - 40; // Línea de tierra.
    final activo = estado['estado'] == 'jugando' && estado['pausada'] != true; // Congela interpolación al pausar.
    final velocidad = (estado['velocidad'] as num?)?.toDouble() ?? 1; // Multiplicador de Python.
    final extra = activo ? demora * 220 * velocidad : 0.0; // Suaviza obstáculos.
    final recorrido = ((estado['recorrido'] as num?)?.toDouble() ?? 0) + extra; // Terreno animado.
    final pintura = Paint()..color = const Color(0xFF6E8595); // Línea de horizonte.
    canvas.drawLine(Offset(0, suelo), Offset(size.width, suelo), pintura..strokeWidth = 2); // Suelo.
    for (var i = 0; i < 14; i++) {
      final x = ((i * 90 - recorrido) % 1100) * escala; // Piedras decorativas.
      canvas.drawLine(Offset(x, suelo + 15), Offset(x + 8, suelo + 15), pintura); // Sensación de avance.
    }
    final obstaculos = estado['obstaculos'] as List? ?? []; // Cactus sincronizados.
    for (final obstaculo in obstaculos) {
      final x = ((obstaculo['x'] as num).toDouble() - extra) * escala; // Posición suavizada.
      final alto = (obstaculo['alto'] as num).toDouble() * escala; // Altura física.
      final ancho = (obstaculo['ancho'] as num).toDouble() * escala; // Ancho físico.
      final cactus = Paint()..color = const Color(0xFFFFC66B); // Obstáculos contrastantes.
      canvas.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(x, suelo-alto, ancho, alto), const Radius.circular(3)), cactus); // Tallo.
      canvas.drawRect(Rect.fromLTWH(x-ancho*.6, suelo-alto*.65, ancho*2.2, alto*.15), cactus); // Brazos del cactus.
    }
    final jugadores = List<Map<String, dynamic>>.from((estado['jugadores'] as List? ?? []).map((j) => Map<String, dynamic>.from(j as Map))); // Tipos explícitos.
    final orden = [...jugadores.where((j) => j['identificador'] != propio), ...jugadores.where((j) => j['identificador'] == propio)]; // Propio se dibuja al final.
    for (final jugador in orden) {
      final indice = jugadores.indexWhere((j) => j['identificador'] == jugador['identificador']); // Color estable según ingreso.
      final vivo = jugador['vivo'] == true; // Estado de una vida.
      var altura = (jugador['altura'] as num).toDouble(); // Última altura del servidor.
      if (activo && vivo && altura > 0) altura = max(0, altura + (jugador['impulso'] as num).toDouble()*demora - 750*demora*demora); // Predicción de física.
      final color = colores[indice % colores.length].withValues(alpha: jugador['identificador'] == propio ? 1 : .55); // Rivales translúcidos.
      canvas.save(); // Coordenadas del mundo.
      canvas.translate(120*escala, suelo-altura*escala); // Misma posición física de todos.
      canvas.scale(escala); // Dinosaurio adapta su tamaño.
      final dino = Paint()..color = vivo ? color : Colors.grey; // Muerto queda gris.
      canvas.drawRRect(RRect.fromRectAndRadius(const Rect.fromLTWH(4,-45,30,28), const Radius.circular(5)), dino); // Cuerpo.
      canvas.drawRect(const Rect.fromLTWH(25,-65,30,26), dino); // Cabeza.
      canvas.drawRect(const Rect.fromLTWH(22,-48,15,25), dino); // Cuello.
      canvas.drawPath(Path()..moveTo(8,-34)..lineTo(-15,-43)..lineTo(8,-18)..close(), dino); // Cola.
      final paso = activo && altura == 0 ? sin(recorrido / 18)*5 : 0.0; // Patas al correr.
      canvas.drawRect(Rect.fromLTWH(8,-20,8,20+paso), dino); // Pata izquierda.
      canvas.drawRect(Rect.fromLTWH(25,-20,8,20-paso), dino); // Pata derecha.
      canvas.drawRect(const Rect.fromLTWH(43,-60,5,5), Paint()..color = const Color(0xFF102018)); // Ojo.
      canvas.restore(); // Vuelve al panel.
      texto(canvas, jugador['nombre'] as String, Offset(10, 34 + indice*20), 12, vivo ? color : Colors.grey); // Nombres de rivales.
    }
    texto(canvas, 'RONDA LOCAL', const Offset(12, 12), 12, Colors.white70); // Cabecera de escenario.
    if (estado['estado'] == 'cuenta') texto(canvas, '${(estado['cuenta'] as num).ceil()}', Offset(size.width*.48, size.height*.35), 48, Colors.white); // Cuenta común.
    if (estado['estado'] == 'espera' || estado.isEmpty) texto(canvas, 'Prepará tu cámara', Offset(size.width*.28, size.height*.5), 16, Colors.white70); // Espera.
    if (estado['pausada'] == true && estado['estado'] == 'jugando') texto(canvas, 'Pausa: falta un cuerpo visible', Offset(12, suelo-70), 14, Colors.amber); // Congelación explícita.
    if (estado['estado'] == 'terminada') texto(canvas, 'Ronda terminada', Offset(size.width*.28, size.height*.45), 20, Colors.white); // Una vida.
  }
  @override
  bool shouldRepaint(covariant _Dibujo oldDelegate) => !identical(estado, oldDelegate.estado) || propio != oldDelegate.propio; // El ticker cambia la interpolación.
}
