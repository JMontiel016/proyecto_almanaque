// Juego arriba; cámara nativa fluida y pose Python abajo.
import 'dart:async'; // Operaciones de cámara serializadas.
import 'dart:math'; // Frecuencia adaptable a la latencia.
import 'package:flutter/material.dart'; // Controles y lienzo.
import 'package:flutter/services.dart'; // Orientación vertical del sensor.
import 'package:camera/camera.dart'; // Preview y flujo de cuadros.
import 'invitacion.dart'; // Única forma de invitar: QR propio.
import '../servicios/conexion.dart'; // Red autoritativa Python.
import '../servicios/conversor_camara.dart'; // Compresión fuera de la interfaz.
import '../juego/escenario.dart'; // Animación independiente de cámara.

class Partida extends StatefulWidget {
  final String nombre, servidor, identidad, codigo;
  const Partida({super.key, required this.nombre, required this.servidor, required this.identidad, required this.codigo});
  @override
  State<Partida> createState() => _EstadoPartida();
}

class _EstadoPartida extends State<Partida> with WidgetsBindingObserver {
  final enlace = Conexion(); // Red de esta sala.
  final conversor = ConversorCamara(); // Un solo hilo para toda la sesión.
  CameraController? camara;
  List<CameraDescription> dispositivos = [];
  Future<void> operaciones = Future.value(); // Abrir, cerrar y cambiar nunca se superponen.
  bool visible = true, convirtiendo = false, cambiando = false, invitando = false;
  bool preparado = false; // No reabre por el diálogo de permisos durante la primera carga.
  int seleccion = 0, generacion = 0;
  DateTime ultimoCuadro = DateTime.fromMillisecondsSinceEpoch(0);
  String errorCamara = '';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    preparar();
  }

  Future<void> preparar() async {
    try {
      await enlace.abrir(widget.servidor, widget.nombre, widget.identidad, widget.codigo);
      if (!mounted) return;
      await conversor.iniciar();
      dispositivos = await availableCameras();
      if (dispositivos.isEmpty) throw StateError('No hay cámara disponible.');
      final frontal = dispositivos.indexWhere((c) => c.lensDirection == CameraLensDirection.front);
      seleccion = frontal < 0 ? 0 : frontal;
      if (!mounted) return;
      await programarCamara();
      preparado = true; // Permisos e inicialización inicial terminados.
      if (mounted && visible && camara == null) await programarCamara();
    } catch (error) {
      if (mounted) setState(() => errorCamara = 'No se pudo preparar: $error');
    }
  }

  Future<void> programarCamara() {
    final turno = ++generacion;
    operaciones = operaciones.then((_) async {
      final anterior = camara;
      camara = null; // Retira el preview antes de liberar la textura.
      if (mounted) setState(() {});
      if (anterior != null) {
        if (anterior.value.isStreamingImages) await anterior.stopImageStream();
        await anterior.dispose(); // Cierra antes de abrir otro sensor.
      }
      if (!mounted || !visible || turno != generacion || dispositivos.isEmpty) return;
      final controlador = CameraController(dispositivos[seleccion], ResolutionPreset.high,
        enableAudio: false, imageFormatGroup: ImageFormatGroup.yuv420); // Solicita HD real según hardware.
      try {
        await controlador.initialize();
        await controlador.lockCaptureOrientation(DeviceOrientation.portraitUp);
        if (!mounted || !visible || turno != generacion) { await controlador.dispose(); return; }
        camara = controlador;
        await controlador.startImageStream((cuadro) => recibirCuadro(cuadro, controlador, turno));
        if (mounted) setState(() => errorCamara = '');
      } catch (error) {
        if (identical(camara, controlador)) camara = null;
        await controlador.dispose();
        rethrow;
      }
    }).catchError((Object error) {
      if (mounted) setState(() => errorCamara = 'Cámara: $error. Revisá el permiso de cámara en Android.');
    });
    return operaciones;
  }

  Future<void> recibirCuadro(CameraImage cuadro, CameraController origen, int turno) async {
    if (!mounted || !visible || invitando || convirtiendo || enlace.ocupado ||
        !enlace.detectorListo || !enlace.conectado || !identical(camara, origen) || turno != generacion) { return; }
    final ahora = DateTime.now();
    final intervalo = max(110, (enlace.demora * 1.1).round()).clamp(110, 400); // Máximo ~9/s; se adapta al servidor.
    if (ahora.difference(ultimoCuadro).inMilliseconds < intervalo) return;
    ultimoCuadro = ahora;
    convirtiendo = true; // Un cuadro en conversión y como máximo uno en red.
    try {
      final bytes = await conversor.convertir(cuadro, origen.description.sensorOrientation,
        origen.description.lensDirection == CameraLensDirection.front); // Android vertical bloqueado.
      if (mounted && visible && turno == generacion && !invitando) enlace.enviarImagen(bytes);
    } catch (error) {
      if (mounted && turno == generacion) setState(() => errorCamara = '$error');
    } finally {
      convirtiendo = false;
    }
  }

  Future<void> cambiarCamara() async {
    if (cambiando || dispositivos.length < 2) return;
    setState(() => cambiando = true);
    seleccion = (seleccion + 1) % dispositivos.length;
    enlace.accion('calibrar'); // La distancia corporal puede cambiar entre sensores.
    enlace.vision.value = {}; // No deja un esqueleto de la cámara anterior.
    await programarCamara();
    if (mounted) setState(() => cambiando = false);
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState estado) {
    if (estado == AppLifecycleState.inactive || estado == AppLifecycleState.paused) {
      visible = false;
      programarCamara(); // Cierre en la misma cola que cualquier apertura pendiente.
    } else if (estado == AppLifecycleState.resumed) {
      visible = true;
      if (preparado && enlace.conectado) programarCamara();
    }
  }

  Future<void> compartir() async {
    invitando = true; // Preview continúa; no gasta inferencia detrás del QR.
    await showDialog<void>(context: context, builder: (_) => Invitacion(servidor: widget.servidor, sala: enlace.sala));
    invitando = false;
  }

  Widget panelCamara() => ValueListenableBuilder<Map<String, dynamic>>(
    valueListenable: enlace.vision,
    builder: (_, pose, __) => Column(children: [
      Expanded(child: RepaintBoundary(child: ClipRRect(borderRadius: BorderRadius.circular(20), child: ColoredBox(
        color: Colors.black,
        child: camara?.value.isInitialized == true ? LayoutBuilder(builder: (_, limites) {
          final proporcion = 1 / camara!.value.aspectRatio; // Sensor vertical sin estirar ni cortar pies.
          final ancho = min(limites.maxWidth, limites.maxHeight * proporcion);
          return Center(child: SizedBox(width: ancho, height: ancho / proporcion, child: Stack(fit: StackFit.expand, children: [
            CameraPreview(camara!), // Textura nativa: no depende del tiempo de respuesta Python.
            IgnorePointer(child: CustomPaint(painter: Esqueleto(pose['puntos'] as List? ?? []))),
          ])));
        }) : Center(child: Padding(padding: const EdgeInsets.all(20), child: Text(
          errorCamara.isEmpty ? enlace.mensaje : errorCamara, textAlign: TextAlign.center))),
      )))),
      const SizedBox(height: 6),
      Text(pose['mensaje'] as String? ?? enlace.mensaje, maxLines: 2, overflow: TextOverflow.ellipsis,
        textAlign: TextAlign.center, style: TextStyle(color: pose['listo'] == true ? const Color(0xFFA7EF5B) : Colors.amber)),
      Text('Vista HD · Python ${pose['demora'] ?? 0} ms · Calibración ${pose['calibracion'] ?? 0}/12',
        style: const TextStyle(fontSize: 11, color: Colors.white54)),
    ]),
  );

  @override
  Widget build(BuildContext context) => AnimatedBuilder(animation: enlace, builder: (_, __) {
    final jugadores = enlace.estado['jugadores'] as List? ?? [];
    Map? propio;
    for (final jugador in jugadores) { if (jugador['identificador'] == enlace.identificador) propio = jugador as Map; }
    final administrador = enlace.identificador.isNotEmpty && enlace.administrador == enlace.identificador;
    final espera = ['espera', 'terminada'].contains(enlace.estado['estado']);
    return Scaffold(
      appBar: AppBar(title: const Text('Zunpi'), actions: [
        if (administrador) IconButton(onPressed: espera ? compartir : null, icon: const Icon(Icons.qr_code_2), tooltip: 'Invitar por QR entre rondas'),
        IconButton(onPressed: cambiando || dispositivos.length < 2 ? null : cambiarCamara,
          icon: const Icon(Icons.cameraswitch_outlined), tooltip: 'Cambiar cámara frontal / trasera'),
      ]),
      body: SafeArea(child: Padding(padding: const EdgeInsets.fromLTRB(14, 0, 14, 10), child: Column(children: [
        Row(children: [Expanded(child: Text(widget.nombre, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700))),
          Text('${propio?['puntos'] ?? 0}', style: const TextStyle(fontSize: 32, fontWeight: FontWeight.w900, color: Color(0xFFA7EF5B))),
          const Text(' pts', style: TextStyle(color: Colors.white60))]),
        const SizedBox(height: 8),
        Expanded(flex: 4, child: RepaintBoundary(child: Escenario(estado: enlace.estado, propio: enlace.identificador))),
        SizedBox(height: 32, child: ListView(scrollDirection: Axis.horizontal, children: jugadores.map<Widget>((j) => Padding(
          padding: const EdgeInsets.only(right: 18), child: Center(child: Text('${j['nombre']} · ${j['puntos']}')))).toList())),
        Expanded(flex: 6, child: panelCamara()),
        if (errorCamara.isNotEmpty || enlace.error.isNotEmpty) Padding(padding: const EdgeInsets.symmetric(vertical: 4),
          child: Text(errorCamara.isNotEmpty ? errorCamara : enlace.error, maxLines: 3, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Colors.amber))),
        if (enlace.ocupado && DateTime.now().difference(enlace.envio).inSeconds > 5)
          const Text('Python no responde. Volvé al inicio y comprobá el servidor.', style: TextStyle(color: Colors.amber)),
        const SizedBox(height: 8),
        ValueListenableBuilder<Map<String, dynamic>>(valueListenable: enlace.vision, builder: (_, pose, __) => Row(children: [
          Expanded(child: FilledButton(onPressed: espera && enlace.conectado && (pose['listo'] == true || propio?['listo'] == true)
            ? () => enlace.accion('listo') : null, child: Text(propio?['listo'] == true ? 'Listo ✓' : 'Estoy listo'))),
          const SizedBox(width: 8),
          if (administrador) Expanded(child: FilledButton.tonal(onPressed: espera && jugadores.isNotEmpty &&
            jugadores.every((j) => j['listo'] == true && j['rastreado'] == true) ? () => enlace.accion('iniciar') : null, child: const Text('Jugar'))),
          IconButton(onPressed: enlace.detectorListo ? () => enlace.accion('calibrar') : null,
            icon: const Icon(Icons.accessibility_new), tooltip: 'Volver a calibrar'),
        ])),
      ]))),
    );
  });

  @override
  void dispose() {
    visible = false;
    generacion++;
    WidgetsBinding.instance.removeObserver(this);
    conversor.cerrar();
    enlace.dispose();
    // Espera la operación ya iniciada: no cierra el hardware durante initialize.
    unawaited(operaciones.then((_) async {
      final anterior = camara; camara = null;
      if (anterior != null) {
        if (anterior.value.isStreamingImages) await anterior.stopImageStream();
        await anterior.dispose();
      }
    }).catchError((Object _) {}));
    super.dispose();
  }
}

class Esqueleto extends CustomPainter {
  final List puntos; // Coordenadas normalizadas inferidas por Python.
  Esqueleto(this.puntos);
  static const uniones = [[11,12],[11,13],[13,15],[12,14],[14,16],[11,23],[12,24],
    [23,24],[23,25],[25,27],[24,26],[26,28],[27,31],[28,32]];
  @override
  void paint(Canvas canvas, Size size) {
    if (puntos.length != 33) return;
    Offset posicion(int i) => Offset((puntos[i][0] as num).toDouble() * size.width, (puntos[i][1] as num).toDouble() * size.height);
    final trazo = Paint()..color = const Color(0xFFA7EF5B)..strokeWidth = 2.5;
    for (final par in uniones) {
      if ((puntos[par[0]][2] as num) > .45 && (puntos[par[1]][2] as num) > .45) canvas.drawLine(posicion(par[0]), posicion(par[1]), trazo);
    }
    trazo.color = const Color(0xFFFFC66B);
    for (var i = 0; i < puntos.length; i++) { if ((puntos[i][2] as num) > .45) canvas.drawCircle(posicion(i), 3, trazo); }
  }
  @override
  bool shouldRepaint(covariant Esqueleto anterior) => !identical(puntos, anterior.puntos);
}
