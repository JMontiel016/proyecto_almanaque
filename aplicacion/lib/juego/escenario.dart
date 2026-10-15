import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';

/// Escenario vectorial: sin texturas ni paquetes externos, adaptable a móviles.
class Escenario extends StatefulWidget {
  final Map<String, dynamic> estado;
  final String propio;
  const Escenario({super.key, required this.estado, required this.propio});
  @override
  State<Escenario> createState() => _EstadoEscenario();
}

class _EstadoEscenario extends State<Escenario> with SingleTickerProviderStateMixin {
  late final Ticker _ticker;
  final ValueNotifier<int> _fotogramas = ValueNotifier<int>(0);
  DateTime _recibido = DateTime.now();

  @override
  void initState() {
    super.initState();
    _ticker = createTicker((_) { _fotogramas.value++; });
    _actualizarTicker();
  }

  void _actualizarTicker() {
    final activo = widget.estado['estado'] == 'jugando' && widget.estado['pausada'] != true;
    if (activo && !_ticker.isActive) _ticker.start();
    if (!activo && _ticker.isActive) _ticker.stop();
  }

  @override
  void didUpdateWidget(covariant Escenario anterior) {
    super.didUpdateWidget(anterior);
    if (!identical(anterior.estado, widget.estado)) _recibido = DateTime.now();
    _actualizarTicker();
  }

  @override
  Widget build(BuildContext context) => ClipRRect(
    borderRadius: BorderRadius.circular(20),
    child: RepaintBoundary(
      child: CustomPaint(
        painter: _Paisaje(widget.estado, widget.propio, _recibido, _fotogramas),
        child: const SizedBox.expand(),
      ),
    ),
  );

  @override
  void dispose() {
    _ticker.dispose();
    _fotogramas.dispose();
    super.dispose();
  }
}

class _Paisaje extends CustomPainter {
  final Map<String, dynamic> estado;
  final String propio;
  final DateTime recibido;
  _Paisaje(this.estado, this.propio, this.recibido, Listenable animacion) : super(repaint: animacion);

  static const paleta = [Color(0xFF7DE5AC), Color(0xFF72CFFF), Color(0xFFFFC06A), Color(0xFFD9A3FF)];
  static const cielo1 = Color(0xFF102940);
  static const cielo2 = Color(0xFF28506C);
  static const tierra = Color(0xFF21394B);

  double _numero(dynamic valor, [double defecto = 0]) => valor is num ? valor.toDouble() : defecto;

  void _texto(Canvas c, String valor, Offset lugar, double tamano, Color color, {FontWeight peso = FontWeight.w600}) {
    final pintor = TextPainter(
      text: TextSpan(text: valor, style: TextStyle(fontSize: tamano, fontWeight: peso, color: color)),
      textDirection: TextDirection.ltr, maxLines: 1, ellipsis: '…',
    )..layout(maxWidth: 280);
    pintor.paint(c, lugar);
  }

  void _nube(Canvas c, double x, double y, double escala, double opacidad) {
    final p = Paint()..color = Colors.white.withValues(alpha: opacidad);
    c.drawOval(Rect.fromLTWH(x, y + 9 * escala, 72 * escala, 19 * escala), p);
    c.drawCircle(Offset(x + 21 * escala, y + 13 * escala), 15 * escala, p);
    c.drawCircle(Offset(x + 44 * escala, y + 8 * escala), 20 * escala, p);
  }

  void _montana(Canvas c, Size s, double baseY, double altura, Color color, double desplazamiento) {
    final p = Paint()..color = color;
    final camino = Path()..moveTo(0, s.height);
    for (var i = -1; i <= 5; i++) {
      final pico = i * s.width / 3 + desplazamiento;
      camino.lineTo(pico - s.width / 3, baseY);
      camino.lineTo(pico, baseY - altura);
      camino.lineTo(pico + s.width / 3, baseY);
    }
    camino..lineTo(s.width, s.height)..close();
    c.drawPath(camino, p);
  }

  void _dinosaurio(Canvas c, Color color, bool vivo, bool propioJugador, double paso) {
    final base = vivo ? color : const Color(0xFF82919A);
    final contorno = Paint()..color = const Color(0xFF112C39)..style = PaintingStyle.stroke..strokeWidth = 2.3;
    final cuerpo = Paint()..color = base;
    final brillo = Paint()..color = Colors.white.withValues(alpha: .22);

    // Silueta cartoon: cola, cuerpo, cuello y cabeza.
    final cola = Path()..moveTo(15, -31)..quadraticBezierTo(-12, -42, -29, -27)
      ..quadraticBezierTo(-8, -16, 17, -17)..close();
    c.drawPath(cola, cuerpo);
    c.drawPath(cola, contorno);
    final torso = RRect.fromRectAndRadius(const Rect.fromLTWH(3, -47, 41, 36), const Radius.circular(14));
    c.drawRRect(torso, cuerpo);
    c.drawRRect(torso, contorno);
    final cuello = RRect.fromRectAndRadius(const Rect.fromLTWH(29, -70, 19, 49), const Radius.circular(8));
    c.drawRRect(cuello, cuerpo);
    c.drawRRect(cuello, contorno);
    final cabeza = RRect.fromRectAndRadius(const Rect.fromLTWH(29, -78, 43, 27), const Radius.circular(12));
    c.drawRRect(cabeza, cuerpo);
    c.drawRRect(cabeza, contorno);
    c.drawOval(const Rect.fromLTWH(36, -75, 22, 10), brillo);
    // Espinas discretas; únicamente pintura vectorial.
    final espinas = Paint()..color = Color.lerp(base, const Color(0xFF104A56), .35)!;
    for (var i = 0; i < 3; i++) {
      final x = 7.0 + i * 12;
      c.drawPath(Path()..moveTo(x, -44)..lineTo(x + 6, -55)..lineTo(x + 12, -44)..close(), espinas);
    }
    for (final pata in [13.0, 33.0]) {
      final avance = pata == 13 ? paso : -paso;
      final pie = RRect.fromRectAndRadius(Rect.fromLTWH(pata, -15 + avance, 10, 18 - avance), const Radius.circular(4));
      c.drawRRect(pie, cuerpo);
      c.drawRRect(pie, contorno);
    }
    c.drawCircle(const Offset(61, -69), 3.3, Paint()..color = const Color(0xFF11202C));
    c.drawCircle(const Offset(62, -70), 1, Paint()..color = Colors.white);
    c.drawArc(const Rect.fromLTWH(55, -63, 12, 7), .2, 1.5, false, contorno);
    if (propioJugador) {
      c.drawCircle(const Offset(24, -32), 4, Paint()..color = Colors.white.withValues(alpha: .26));
    }
  }

  void _cactus(Canvas c, double x, double suelo, double ancho, double alto) {
    final planta = Paint()..color = const Color(0xFFFFBA73);
    final borde = Paint()..color = const Color(0xFF995F53)..style = PaintingStyle.stroke..strokeWidth = 2;
    final tallo = RRect.fromRectAndRadius(Rect.fromLTWH(x, suelo - alto, ancho, alto), const Radius.circular(7));
    c.drawRRect(tallo, planta);
    c.drawRRect(tallo, borde);
    final brazo = RRect.fromRectAndRadius(Rect.fromLTWH(x - ancho * .58, suelo - alto * .64, ancho * 2.1, alto * .15),
        const Radius.circular(5));
    c.drawRRect(brazo, planta);
  }

  @override
  void paint(Canvas canvas, Size size) {
    if (size.isEmpty) return;
    final suelo = size.height - 35;
    final escala = size.width / 1000;
    final activo = estado['estado'] == 'jugando' && estado['pausada'] != true;
    final dt = math.max(0.0, math.min(.12, DateTime.now().difference(recibido).inMilliseconds / 1000));
    final velocidad = _numero(estado['velocidad'], 1);
    final extra = activo ? dt * 220 * velocidad : 0.0;
    final recorrido = _numero(estado['recorrido']) + extra;

    canvas.drawRect(Offset.zero & size, Paint()..shader = const LinearGradient(
      begin: Alignment.topCenter, end: Alignment.bottomCenter, colors: [cielo1, cielo2],
    ).createShader(Offset.zero & size));
    canvas.drawCircle(Offset(size.width * .79, size.height * .22), 29,
        Paint()..color = const Color(0xFFFFDC9C).withValues(alpha: .9));
    final desplazamiento = -(recorrido * .025 * escala) % (size.width / 3);
    _montana(canvas, size, suelo - 22, size.height * .22, const Color(0xFF365D70), desplazamiento);
    _montana(canvas, size, suelo - 3, size.height * .13, const Color(0xFF28495C), desplazamiento * 1.5);
    _nube(canvas, size.width * .12 - (recorrido * .009 * escala) % size.width, 30, .72, .17);
    _nube(canvas, size.width * .62 - (recorrido * .012 * escala) % size.width, 60, .52, .12);

    canvas.drawRect(Rect.fromLTWH(0, suelo, size.width, size.height - suelo), Paint()..color = tierra);
    canvas.drawLine(Offset(0, suelo), Offset(size.width, suelo),
        Paint()..color = const Color(0xFF85D4A1)..strokeWidth = 3);
    final piedras = Paint()..color = const Color(0xFF56717A);
    for (var i = 0; i < 16; i++) {
      final x = (((i * 83 - recorrido * .55) % 1400) * escala);
      canvas.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(x, suelo + 13, 12 * escala, 3),
          const Radius.circular(2)), piedras);
    }

    for (final item in estado['obstaculos'] as List? ?? []) {
      if (item is! Map) continue;
      final x = (_numero(item['x']) - extra) * escala;
      final ancho = _numero(item['ancho'], 20) * escala;
      final alto = _numero(item['alto'], 60) * escala;
      if (x < -100 || x > size.width + 100) continue;
      _cactus(canvas, x, suelo, ancho, alto);
    }

    final jugadores = (estado['jugadores'] as List? ?? []).whereType<Map>().toList();
    final orden = [...jugadores.where((j) => j['identificador'] != propio),
      ...jugadores.where((j) => j['identificador'] == propio)];
    for (final jugador in orden) {
      final indice = jugadores.indexOf(jugador);
      final vivo = jugador['vivo'] == true;
      var altura = _numero(jugador['altura']);
      if (activo && vivo && altura > 0) {
        altura = math.max(0, altura + _numero(jugador['impulso']) * dt - 750 * dt * dt);
      }
      final local = jugador['identificador'] == propio;
      final color = paleta[indice % paleta.length].withValues(alpha: local ? 1 : .70);
      canvas.save();
      canvas.translate(120 * escala, suelo - altura * escala);
      canvas.scale(escala);
      final paso = activo && altura == 0 ? math.sin(recorrido / 18) * 4 : 0.0;
      _dinosaurio(canvas, color, vivo, local, paso);
      canvas.restore();
      _texto(canvas, '${jugador['nombre'] ?? 'Jugador'}', Offset(11, 34 + indice * 19), 12,
          vivo ? color : Colors.white54);
    }

    _texto(canvas, 'ZUNPI RUN', const Offset(12, 9), 12, Colors.white70, peso: FontWeight.bold);
    final fase = estado['estado'];
    if (fase == 'cuenta') {
      _texto(canvas, '${_numero(estado['cuenta']).ceil()}',
          Offset(size.width * .47, size.height * .31), 47, Colors.white);
    }
    if (fase == 'espera' || estado.isEmpty) {
      _texto(canvas, 'Prepará tu cámara',
          Offset(size.width * .24, size.height * .52), 16, Colors.white);
    }
    if (estado['pausada'] == true && fase == 'jugando') {
      _texto(canvas, 'Pausa: falta un cuerpo visible',
          Offset(12, suelo - 100), 13, Colors.amber);
    }
    if (fase == 'terminada') {
      _texto(canvas, 'Ronda terminada',
          Offset(size.width * .25, size.height * .42), 20, Colors.white);
    }
  }

  @override
  bool shouldRepaint(covariant _Paisaje anterior) =>
      !identical(estado, anterior.estado) || propio != anterior.propio || recibido != anterior.recibido;
}
