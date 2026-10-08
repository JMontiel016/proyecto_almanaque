import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';

/// Dibujo vectorial: se adapta a la pantalla sin sprites pixelados.
class Escenario extends StatefulWidget {
  final Map<String, dynamic> estado;
  final String propio;
  const Escenario({super.key, required this.estado, required this.propio});
  @override
  State<Escenario> createState() => _EstadoEscenario();
}

class _EstadoEscenario extends State<Escenario>
    with SingleTickerProviderStateMixin {
  late final Ticker reloj;
  final pulsos = ValueNotifier<int>(0);
  DateTime recibido = DateTime.now();

  @override
  void initState() {
    super.initState();
    reloj = createTicker((_) => pulsos.value++);
    ajustarReloj();
  }

  void ajustarReloj() {
    final activo = widget.estado['estado'] == 'jugando' &&
        widget.estado['pausada'] != true;
    if (activo && !reloj.isActive) reloj.start();
    if (!activo && reloj.isActive) reloj.stop();
  }

  @override
  void didUpdateWidget(covariant Escenario anterior) {
    super.didUpdateWidget(anterior);
    if (!identical(anterior.estado, widget.estado)) recibido = DateTime.now();
    ajustarReloj();
  }

  @override
  Widget build(BuildContext context) {
    final fase = widget.estado['estado'] as String? ?? 'espera';
    final pausa = widget.estado['pausada'] == true;
    String? titulo, detalle;
    IconData icono = Icons.accessibility_new_rounded;
    if (fase == 'terminada') {
      titulo = '¡Buen intento!';
      detalle = 'Tocá “Volver a jugar” para intentarlo otra vez.';
      icono = Icons.flag_rounded;
    } else if (pausa && ['cuenta', 'jugando'].contains(fase)) {
      titulo = 'Juego en pausa';
      detalle = widget.estado['pausa_manual'] == true
          ? 'Tocá el botón de continuar cuando estés listo.'
          : 'Volvé al cuadro: hombros y ambos pies visibles.';
      icono = Icons.pause_circle_outline_rounded;
    } else if (fase == 'cuenta') {
      titulo = '${((widget.estado['cuenta'] as num?) ?? 3).ceil()}';
      detalle = 'Preparado… ¡saltá y agachate!';
      icono = Icons.timer_outlined;
    } else if (fase == 'espera') {
      titulo = 'Tu cuerpo controla el juego';
      detalle = 'Calibrá de pie y quieto. Después tocá Jugar.';
    }
    return ClipRRect(
      borderRadius: BorderRadius.circular(22),
      child: Stack(fit: StackFit.expand, children: [
        CustomPaint(
            painter: _Paisaje(widget.estado, widget.propio, recibido, pulsos)),
        if (titulo != null)
          ColoredBox(
            color: const Color(0xFF0A1D25).withValues(alpha: .72),
            child: Center(
                child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Icon(icono, color: const Color(0xFFA7EF5B), size: 28),
                const SizedBox(height: 8),
                Text(titulo,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 21,
                        fontWeight: FontWeight.w800)),
                const SizedBox(height: 6),
                Text(detalle!,
                    textAlign: TextAlign.center,
                    style:
                        const TextStyle(color: Colors.white70, fontSize: 13)),
              ]),
            )),
          ),
      ]),
    );
  }

  @override
  void dispose() {
    reloj.dispose();
    pulsos.dispose();
    super.dispose();
  }
}

class _Paisaje extends CustomPainter {
  final Map<String, dynamic> estado;
  final String propio;
  final DateTime recibido;
  _Paisaje(this.estado, this.propio, this.recibido, Listenable pulsos)
      : super(repaint: pulsos);

  Paint tinta(Color color) => Paint()
    ..color = color
    ..isAntiAlias = true;

  void nube(Canvas c, double x, double y, double escala) {
    final p = tinta(Colors.white.withValues(alpha: .14));
    c.drawOval(Rect.fromLTWH(x, y, 52 * escala, 13 * escala), p);
    c.drawCircle(Offset(x + 18 * escala, y), 11 * escala, p);
    c.drawCircle(Offset(x + 32 * escala, y - 3 * escala), 14 * escala, p);
  }

  void dinosaurio(Canvas c, double paso, bool agachado, bool vivo) {
    final verde = vivo ? const Color(0xFFA7EF5B) : const Color(0xFF97A8AD);
    final cuerpo = Path();
    if (agachado) {
      cuerpo.moveTo(-14, -13);
      cuerpo.cubicTo(2, -12, 0, -29, 20, -27);
      cuerpo.cubicTo(29, -26, 34, -31, 43, -30);
      cuerpo.cubicTo(61, -29, 59, -15, 44, -14);
      cuerpo.lineTo(32, -8);
      cuerpo.lineTo(8, -8);
      cuerpo.close();
    } else {
      cuerpo.moveTo(-15, -40);
      cuerpo.cubicTo(0, -37, 2, -31, 7, -36);
      cuerpo.cubicTo(10, -41, 18, -39, 24, -41);
      cuerpo.lineTo(26, -57);
      cuerpo.cubicTo(28, -70, 51, -69, 56, -60);
      cuerpo.cubicTo(61, -48, 52, -43, 37, -44);
      cuerpo.cubicTo(39, -29, 35, -13, 23, -10);
      cuerpo.cubicTo(11, -8, 6, -18, 5, -24);
      cuerpo.close();
    }
    c.drawPath(cuerpo, tinta(verde));
    final patas = tinta(verde)
      ..strokeWidth = 7
      ..strokeCap = StrokeCap.round;
    for (var i = 0; i < 2; i++) {
      final x = 12.0 + i * 15;
      final movimiento = agachado ? 0.0 : (i == 0 ? paso : -paso);
      c.drawLine(Offset(x, -13), Offset(x + movimiento, -3), patas);
      c.drawLine(Offset(x + movimiento, -3), Offset(x + movimiento + 6, -3),
          patas..strokeWidth = 5);
      patas.strokeWidth = 7;
    }
    final ojo = Offset(46, agachado ? -24 : -58);
    c.drawCircle(ojo, 3.7, tinta(Colors.white));
    c.drawCircle(ojo + const Offset(1, 0), 1.8, tinta(const Color(0xFF163328)));
    c.drawLine(
        Offset(43, agachado ? -17 : -49),
        Offset(53, agachado ? -17 : -49),
        tinta(const Color(0xFF42743C))
          ..strokeWidth = 1.5
          ..strokeCap = StrokeCap.round);
    if (!agachado) {
      c.drawLine(
          const Offset(30, -30),
          const Offset(40, -27),
          tinta(verde)
            ..strokeWidth = 4
            ..strokeCap = StrokeCap.round);
    }
  }

  @override
  void paint(Canvas c, Size size) {
    final rect = Offset.zero & size;
    c.drawRect(
        rect,
        Paint()
          ..shader = const LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFF153A50), Color(0xFF3C716E)],
          ).createShader(rect));
    final activo = estado['estado'] == 'jugando' && estado['pausada'] != true;
    final demora = min(.15,
        max(0.0, DateTime.now().difference(recibido).inMilliseconds / 1000));
    final velocidad = (estado['velocidad'] as num?)?.toDouble() ?? 1;
    final extra = activo ? demora * 220 * velocidad : 0.0;
    final recorrido = ((estado['recorrido'] as num?)?.toDouble() ?? 0) + extra;
    // Acercar la vista agranda personajes; las colisiones siguen en coordenadas Python.
    final escala = size.width / 600;
    final suelo = size.height - 30;
    c.drawCircle(Offset(size.width * .82, size.height * .2), 20,
        tinta(const Color(0xFFFFE3A1)));
    for (var i = 0; i < 3; i++) {
      nube(c, ((i * 230 - recorrido * .12) % 760 - 70) * escala,
          size.height * (.18 + i * .07), max(.7, escala));
    }
    for (var capa = 0; capa < 2; capa++) {
      final colina = Path()..moveTo(0, suelo);
      for (var x = 0.0; x <= size.width + 8; x += 8) {
        final y = suelo -
            26 -
            capa * 16 -
            sin((x + recorrido * .06 * (capa + 1)) / 95) * (12 + capa * 8);
        colina.lineTo(x, y);
      }
      colina.lineTo(size.width, suelo);
      colina.close();
      c.drawPath(colina,
          tinta(capa == 0 ? const Color(0xFF28565D) : const Color(0xFF326665)));
    }
    c.drawRect(Rect.fromLTWH(0, suelo, size.width, 30),
        tinta(const Color(0xFF193F3D)));
    c.drawLine(Offset(0, suelo), Offset(size.width, suelo),
        tinta(const Color(0xFFB2D8AA))..strokeWidth = 2);
    for (var i = 0; i < 12; i++) {
      final x = ((i * 60 - recorrido) % 720) * escala;
      c.drawLine(Offset(x, suelo + 12), Offset(x + 5, suelo + 12),
          tinta(const Color(0xFF659184))..strokeWidth = 2);
    }
    for (final o in estado['obstaculos'] as List? ?? []) {
      final x = ((o['x'] as num).toDouble() - extra) * escala;
      if (x > size.width + 50 || x < -80) continue;
      final alto = (o['alto'] as num).toDouble() * escala;
      final ancho = (o['ancho'] as num).toDouble() * escala;
      if (o['tipo'] == 'aereo') {
        final y =
            suelo - ((o['y'] as num?)?.toDouble() ?? 38) * escala - alto / 2;
        final centro = Offset(x + ancho / 2, y);
        final p = tinta(const Color(0xFFFFCF7F));
        c.drawOval(
            Rect.fromCenter(center: centro, width: ancho, height: alto * .8),
            p);
        final ala = Path()
          ..moveTo(centro.dx, centro.dy)
          ..quadraticBezierTo(
              centro.dx - ancho * .3,
              y - alto * (.6 + sin(recorrido / 16) * .3),
              centro.dx - ancho * .5,
              y - alto * .9)
          ..lineTo(centro.dx + ancho * .15, y + alto * .1)
          ..close();
        c.drawPath(ala, tinta(const Color(0xFFE9A953)));
        final pico = Path()
          ..moveTo(x, y)
          ..lineTo(x - ancho * .25, y + 2)
          ..lineTo(x + 2, y + 6)
          ..close();
        c.drawPath(pico, tinta(const Color(0xFFFFF0C6)));
        c.drawCircle(Offset(x + ancho * .2, y - alto * .15), 1.8,
            tinta(const Color(0xFF34322F)));
      } else {
        final p = tinta(const Color(0xFFFFC66B));
        c.drawRRect(
            RRect.fromRectAndRadius(Rect.fromLTWH(x, suelo - alto, ancho, alto),
                Radius.circular(ancho * .4)),
            p);
        final rama = p
          ..strokeWidth = max(3.0, ancho * .3)
          ..strokeCap = StrokeCap.round;
        c.drawPath(
            Path()
              ..moveTo(x + ancho * .25, suelo - alto * .4)
              ..lineTo(x - ancho * .35, suelo - alto * .4)
              ..lineTo(x - ancho * .35, suelo - alto * .7),
            rama..style = PaintingStyle.stroke);
        c.drawPath(
            Path()
              ..moveTo(x + ancho * .75, suelo - alto * .6)
              ..lineTo(x + ancho * 1.3, suelo - alto * .6)
              ..lineTo(x + ancho * 1.3, suelo - alto * .85),
            rama);
      }
    }
    final jugadores = estado['jugadores'] as List? ?? [];
    Map? jugador;
    for (final j in jugadores) {
      if (j['identificador'] == propio) jugador = j as Map;
    }
    var altura = ((jugador?['altura'] as num?) ?? 0).toDouble();
    final vivo = jugador?['vivo'] != false;
    if (activo && vivo && altura > 0) {
      altura = max(
          0,
          altura +
              ((jugador?['impulso'] as num?) ?? 0) * demora -
              750 * demora * demora);
    }
    c.drawOval(
        Rect.fromCenter(
            center: Offset(142 * escala, suelo + 3),
            width: 45 * escala,
            height: 7 * escala),
        tinta(Colors.black.withValues(alpha: .2)));
    c.save();
    c.translate(120 * escala, suelo - altura * escala);
    c.scale(escala);
    dinosaurio(c, activo && altura == 0 ? sin(recorrido / 15) * 4 : 0,
        jugador?['agachado'] == true && altura == 0, vivo);
    c.restore();
  }

  @override
  bool shouldRepaint(covariant _Paisaje anterior) =>
      !identical(estado, anterior.estado) || propio != anterior.propio;
}
