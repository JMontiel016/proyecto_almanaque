// Nombre, servidor, sala y ranking: un único punto de entrada.
import 'dart:convert'; // Lee invitación QR y ranking.
import 'dart:math'; // Genera identidad anónima del dispositivo.
import 'package:flutter/material.dart'; // Interfaz.
import 'package:shared_preferences/shared_preferences.dart'; // Preferencias locales.
import 'package:mobile_scanner/mobile_scanner.dart'; // Escáner de QR.
import 'package:http/http.dart' as http; // Consulta ranking global del servidor.
import 'invitacion.dart'; // Invitación desde inicio, antes de preparar cámara.
import 'partida.dart'; // Pantalla de juego.

class Inicio extends StatefulWidget {
  const Inicio({super.key}); // Pantalla inicial.
  @override
  State<Inicio> createState() => _EstadoInicio(); // Estado de formulario.
}

class _EstadoInicio extends State<Inicio> {
  final nombre = TextEditingController(); // Nombre editable.
  final servidor = TextEditingController(text: ''); // Ejemplo, reemplazar por IP real.
  String sala = ''; // Únicamente reserva propia o invitación QR, sin campo manual.
  bool usb = false, comprobando = false; // Modo de conexión y bloqueo del diagnóstico.
  String identidad = ''; // Identifica récord entre sesiones.
  String aviso = ''; // Validación y conexión.
  bool cargando = true; // Espera lectura de preferencias.

  @override
  void initState() {
    super.initState(); // Inicialización Flutter.
    cargar(); // Restaura nombre, dirección e identidad.
  }

  Future<void> cargar() async {
    final preferencias = await SharedPreferences.getInstance(); // Persistencia simple.
    identidad = preferencias.getString('identidad') ?? List.generate(32, (_) => Random.secure().nextInt(16).toRadixString(16)).join(); // 128 bits.
    await preferencias.setString('identidad', identidad); // Mantiene identidad del ranking.
    if (!mounted) return; // Evita usar pantalla cerrada.
    nombre.text = preferencias.getString('nombre') ?? ''; // Último nombre.
    servidor.text = preferencias.getString('servidor') ?? servidor.text; // Último servidor.
    usb = Uri.tryParse(servidor.text)?.host == '127.0.0.1';
    setState(() => cargando = false); // Habilita ingreso.
  }

  Future<void> entrar() async {
    if (cargando) return; // Una sola navegación a partida.
    final direccion = Uri.tryParse(servidor.text.trim()); // Valida antes de abrir cámara.
    if (nombre.text.trim().isEmpty || direccion == null || !['http', 'https'].contains(direccion.scheme) || direccion.host.isEmpty || direccion.path.replaceAll('/', '').isNotEmpty || direccion.hasQuery || direccion.hasFragment || direccion.userInfo.isNotEmpty) {
      setState(() => aviso = 'Ingresá tu nombre y la dirección http://IP_DE_TU_PC:8001'); // Mensaje útil.
      return;
    }
    setState(() => cargando = true); // Bloquea otra entrada antes del primer await.
    final preferencias = await SharedPreferences.getInstance(); // Guarda configuración.
    await preferencias.setString('nombre', nombre.text.trim()); // Nombre Unicode.
    await preferencias.setString('servidor', servidor.text.trim().replaceAll(RegExp(r'/$'), '')); // Sin barra final.
    if (!mounted) return; // Navegación segura.
    await Navigator.push(context, MaterialPageRoute<void>(builder: (_) => Partida(
      nombre: nombre.text.trim(), servidor: servidor.text.trim().replaceAll(RegExp(r'/$'), ''), identidad: identidad, codigo: sala,
    ))); // Sala primero; luego calibración.
    if (mounted) setState(() { cargando = false; sala = ''; }); // Una invitación usada no queda apuntando a una sala cerrada.
  }

  Future<void> comprobar() async {
    final reloj = Stopwatch()..start(); // Mide respuesta real; no promete tiempos no medidos.
    try {
      final base = servidor.text.trim().replaceAll(RegExp(r'/$'), '');
      final respuesta = await http.get(Uri.parse('$base/salud')).timeout(const Duration(seconds: 2));
      final datos = jsonDecode(respuesta.body) as Map<String,dynamic>;
      if (respuesta.statusCode != 200 || datos['juego'] != 'Zunpi') throw StateError('Servidor incorrecto.');
      if (!mounted) return;
      setState(() => aviso = 'Servidor ${datos['version']}: ${reloj.elapsedMilliseconds} ms. Modelo: ${datos['modelo'] == true ? 'disponible' : 'falta descargar'}.');
    } catch (error) {
      if (mounted) setState(() => aviso = 'No hay acceso al servidor. Para probar por USB ejecutá adb reverse tcp:8001 tcp:8001 y elegí Usar USB. Detalle: $error');
    }
  }

  Future<void> crearSala() async {
    if (nombre.text.trim().isEmpty) {
      setState(() => aviso = 'Ingresá tu nombre antes de invitar.');
      return;
    }
    setState(() => cargando = true); // Evita reservas duplicadas por varios toques.
    try {
      final base = servidor.text.trim().replaceAll(RegExp(r'/$'), '');
      final respuesta = await http.post(Uri.parse('$base/salas'), headers: {'Content-Type':'application/json'}, body: jsonEncode({'nombre':nombre.text.trim()})).timeout(const Duration(seconds: 2));
      if (respuesta.statusCode != 200) throw StateError('Reiniciá servidor v0.4: HTTP ${respuesta.statusCode}.');
      final datos = jsonDecode(respuesta.body) as Map<String,dynamic>;
      if (datos['error'] != null) throw StateError(datos['error'] as String);
      if (datos['version'] != '0.4.0' || datos['sala'] is! String) throw StateError('Respuesta de sala inválida.');
      if (!mounted) return;
      setState(() { sala = datos['sala'] as String; aviso = 'Sala lista. Invitá por QR y luego tocá Jugar.'; });
      await showDialog<void>(context: context, builder: (_) => Invitacion(servidor:base,sala:sala));
    } catch (error) {
      if (mounted) setState(() => aviso = 'No se pudo crear sala: $error. Comprobá servidor o probá por USB.');
    } finally {
      if (mounted) setState(() => cargando = false);
    }
  }

  Future<void> escanear() async {
    final texto = await Navigator.push<String>(context, MaterialPageRoute(builder: (_) => const Escaner())); // Cámara solo del escáner.
    if (texto == null || !mounted) return; // Cancelación normal.
    try {
      final datos = jsonDecode(texto) as Map<String, dynamic>; // QR propio del juego.
      if (datos['juego'] != 'Zunpi' || datos['servidor'] is! String || datos['sala'] is! String) throw const FormatException(); // No acepta otro QR.
      final destino = Uri.tryParse(datos['servidor'] as String);
      if (destino == null || !['http', 'https'].contains(destino.scheme) || destino.host.isEmpty || destino.userInfo.isNotEmpty || destino.hasQuery || destino.hasFragment || destino.path.replaceAll('/', '').isNotEmpty || !RegExp(r'^[A-F0-9]{6}$').hasMatch(datos['sala'] as String)) throw const FormatException();
      setState(() {
        servidor.text = datos['servidor'] as String; // Dirección compartida.
        sala = datos['sala'] as String; // Sala obtenida exclusivamente del QR.
        usb = false;
        aviso = 'Invitación cargada. Ingresá tu nombre y entrá.'; // No conecta sin confirmar.
      });
      if (nombre.text.trim().isNotEmpty) await entrar(); // Nombre ingresado: entra sin copiar códigos.
    } catch (_) {
      setState(() => aviso = 'Ese QR no es una invitación de Zunpi.'); // Entrada inválida.
    }
  }

  Future<void> verRanking() async {
    try {
      final respuesta = await http.get(Uri.parse('${servidor.text.trim().replaceAll(RegExp(r'/$'), '')}/ranking')).timeout(const Duration(seconds: 2)); // Fuente compartida.
      if (respuesta.statusCode != 200) throw Exception('HTTP ${respuesta.statusCode}'); // No confunde error con vacío.
      final filas = jsonDecode(respuesta.body) as List; // Ranking persistente.
      if (!mounted) return; // Contexto válido.
      await showModalBottomSheet<void>(context: context, isScrollControlled: true, builder: (_) => SafeArea(child: SizedBox(
        height: MediaQuery.sizeOf(context).height * .65,
        child: Column(children: [const Padding(padding: EdgeInsets.all(20), child: Text('Ranking global', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold))),
          Expanded(child: filas.isEmpty ? const Center(child: Text('Todavía no hay récords. ¡Jugá tu primera ronda!')) : ListView.builder(itemCount: filas.length, itemBuilder: (_, i) => ListTile(
            leading: CircleAvatar(child: Text('${i + 1}')), title: Text(filas[i]['nombre'] as String), trailing: Text('${filas[i]['puntos']} pts'),
          ))),
        ]),
      ))); // Ranking accesible sin entrar a una sala.
    } catch (error) {
      if (mounted) setState(() => aviso = 'No se pudo cargar el ranking. Revisá el servidor: $error'); // Fallo visible.
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(body: SafeArea(child: Center(child: ConstrainedBox(
    constraints: const BoxConstraints(maxWidth: 520),
    child: ListView(padding: const EdgeInsets.fromLTRB(22, 24, 22, 20), children: [
      Row(children: [ClipRRect(borderRadius: BorderRadius.circular(20), child: Image.asset('assets/icono.png', width: 64, height: 64, cacheWidth: 128, cacheHeight: 128)),
        const SizedBox(width: 16), const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('Zunpi', style: TextStyle(fontSize: 36, fontWeight: FontWeight.w900)), Text('Tu cuerpo. Tu salto. Tu récord.', style: TextStyle(color: Colors.white60)),
        ])]),
      const SizedBox(height: 28),
      const Text('Listo para saltar', style: TextStyle(fontSize: 27, fontWeight: FontWeight.w800)),
      const SizedBox(height: 8),
      const Text('Juego arriba, cámara abajo. Apoyá el celular y dejá visibles tu cabeza y ambos pies.', style: TextStyle(color: Colors.white70)),
      const SizedBox(height: 20),
      TextField(controller: nombre, maxLength: 18, textCapitalization: TextCapitalization.words,
        decoration: const InputDecoration(labelText: 'Tu nombre en el ranking', prefixIcon: Icon(Icons.person_outline))),
      Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('1 · Conectate a la computadora', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
        const SizedBox(height: 12),
        SegmentedButton<bool>(segments: const [ButtonSegment(value: false, label: Text('Wi-Fi'), icon: Icon(Icons.wifi)),
          ButtonSegment(value: true, label: Text('USB'), icon: Icon(Icons.usb))], selected: {usb}, onSelectionChanged: (seleccion) => setState(() {
            usb = seleccion.first; sala = '';
            servidor.text = usb ? 'http://127.0.0.1:8001' : '';
            aviso = '';
          })),
        const SizedBox(height: 12),
        Text(usb ? 'Conectá el cable y ejecutá probar_android_usb.sh en la PC. Luego comprobá la conexión.'
          : 'Conectá la PC y los celulares a la misma Wi-Fi. Usá la IPv4 que muestra hostname -I en la PC.', style: const TextStyle(color: Colors.white70)),
        const SizedBox(height: 12),
        TextField(controller: servidor, readOnly: usb, keyboardType: TextInputType.url,
          onChanged: (_) => sala = '', decoration: const InputDecoration(labelText: 'Dirección de la computadora', hintText: 'http://IP_DE_LA_PC:8001')),
        const SizedBox(height: 8),
        TextButton.icon(onPressed: comprobando ? null : () async {
          setState(() => comprobando = true); await comprobar(); if (mounted) setState(() => comprobando = false);
        }, icon: const Icon(Icons.network_check), label: Text(comprobando ? 'Comprobando…' : 'Comprobar conexión')),
      ]))),
      if (aviso.isNotEmpty) Padding(padding: const EdgeInsets.symmetric(vertical: 12), child: Text(aviso, style: const TextStyle(color: Colors.amber))),
      const SizedBox(height: 16),
      const Text('2 · Elegí cómo jugar', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
      const SizedBox(height: 12),
      FilledButton.icon(onPressed: cargando ? null : entrar, icon: const Icon(Icons.play_arrow_rounded),
        label: Text(sala.isEmpty ? 'Jugar' : 'Entrar a la sala')),
      const SizedBox(height: 8),
      OutlinedButton.icon(onPressed: cargando ? null : crearSala, icon: const Icon(Icons.qr_code_2), label: const Text('Crear sala e invitar por QR')),
      const SizedBox(height: 8),
      OutlinedButton.icon(onPressed: cargando ? null : escanear, icon: const Icon(Icons.qr_code_scanner), label: const Text('Escanear QR de un amigo')),
      if (sala.isNotEmpty) TextButton(onPressed: () => setState(() { sala = ''; aviso = ''; }), child: const Text('Salir de esta invitación')),
      TextButton.icon(onPressed: cargando ? null : verRanking, icon: const Icon(Icons.leaderboard_outlined), label: const Text('Ranking por nombre')),
      const Padding(padding: EdgeInsets.only(top: 10), child: Text('1 a 4 jugadores · Una vida · Cámara frontal o trasera', textAlign: TextAlign.center, style: TextStyle(fontSize: 12, color: Colors.white54))),
    ]),
  ))));

  @override
  void dispose() {
    nombre.dispose(); // Libera formulario.
    servidor.dispose(); // Libera dirección.
    super.dispose();
  }
}

class Escaner extends StatefulWidget {
  const Escaner({super.key}); // Pantalla independiente para evitar dos cámaras abiertas.
  @override
  State<Escaner> createState() => _EstadoEscaner();
}
class _EstadoEscaner extends State<Escaner> {
  bool leido = false; // Evita navegar varias veces con el mismo QR.
  final controlador = MobileScannerController(detectionSpeed: DetectionSpeed.noDuplicates, formats: [BarcodeFormat.qrCode]); // Control de cámara del escáner.
  @override
  Widget build(BuildContext context) => Scaffold(appBar: AppBar(title: const Text('Escanear invitación')), body: Stack(fit: StackFit.expand, children: [MobileScanner(
    controller: controlador, // Cámara liberada al salir.
    onDetect: (captura) async {
      if (leido || captura.barcodes.isEmpty) return; // Una invitación por apertura.
      final valor = captura.barcodes.first.rawValue; // Contenido del QR.
      if (valor != null) {
        leido = true; // Bloquea eventos repetidos.
        await controlador.stop(); // Libera el sensor antes de abrir la cámara del juego.
        if (context.mounted) { Navigator.pop(context, valor); } // Devuelve al formulario.
      }
    },
  ), const Positioned(left: 20, right: 20, bottom: 30, child: Card(child: Padding(padding: EdgeInsets.all(16), child: Text('Apuntá al QR de Zunpi que muestra tu amigo.', textAlign: TextAlign.center))))]));
  @override
  void dispose() {
    controlador.dispose(); // Libera cámara antes de iniciar juego.
    super.dispose();
  }
}
