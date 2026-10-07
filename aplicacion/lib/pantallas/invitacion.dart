import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:http/http.dart' as http;

class Invitacion extends StatefulWidget {
  final String servidor, sala;
  const Invitacion({super.key, required this.servidor, required this.sala});
  @override
  State<Invitacion> createState() => _EstadoInvitacion();
}

class _EstadoInvitacion extends State<Invitacion> {
  final direccion = TextEditingController();
  String destino = '', aviso = '';
  List<String> opciones = [];
  bool buscando = true;

  bool esLocal(Uri uri) =>
      ['localhost', '127.0.0.1', '0.0.0.0', '::1'].contains(uri.host);

  @override
  void initState() {
    super.initState();
    preparar();
  }

  Future<void> preparar() async {
    try {
      final base = Uri.parse(widget.servidor);
      if (!esLocal(base)) {
        if (!mounted) return;
        setState(() {
          destino = base.toString();
          direccion.text = destino;
          buscando = false;
        });
        return;
      }
      final respuesta = await http.get(base.replace(path: '/red'))
          .timeout(const Duration(seconds: 5));
      if (respuesta.statusCode != 200) {
        throw StateError('El servidor no informó su dirección Wi-Fi.');
      }
      final datos = jsonDecode(respuesta.body) as Map<String, dynamic>;
      final ips = datos['direcciones'];
      if (ips is! List) throw StateError('Respuesta de red inválida.');
      final urls = <String>[];
      for (final ip in ips.whereType<String>()) {
        final uri = base.replace(host: ip.trim());
        if (uri.host.isNotEmpty && !esLocal(uri)) urls.add(uri.toString());
      }
      if (urls.isEmpty) throw StateError('No se encontró una dirección Wi-Fi.');
      if (!mounted) return;
      setState(() {
        opciones = urls.toSet().toList();
        destino = opciones.first;
        direccion.text = destino;
        buscando = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        buscando = false;
        aviso = 'Ingresá la dirección Wi-Fi de la computadora para mostrar el QR.';
      });
    }
  }

  void aplicar() {
    final texto = direccion.text.trim();
    final uri = Uri.tryParse(texto.contains('://') ? texto : 'http://$texto');
    if (uri == null || !['http', 'https'].contains(uri.scheme) ||
        uri.host.isEmpty || esLocal(uri) || uri.userInfo.isNotEmpty ||
        uri.hasQuery || uri.hasFragment ||
        uri.path.replaceAll('/', '').isNotEmpty) {
      setState(() => aviso = 'Usá la IP de la PC, por ejemplo http://192.168.1.50:8001.');
      return;
    }
    final base = uri.hasPort ? uri : uri.replace(port: 8001);
    setState(() {
      destino = base.replace(path: '').toString();
      direccion.text = destino;
      aviso = '';
    });
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Invitá a tu equipo'),
    content: SizedBox(
      width: 300,
      child: SingleChildScrollView(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Text('Escaneá este QR desde Zunpi', textAlign: TextAlign.center),
          const SizedBox(height: 16),
          if (buscando) const Padding(
            padding: EdgeInsets.all(24), child: CircularProgressIndicator()),
          if (destino.isNotEmpty) LayoutBuilder(builder: (context, limites) {
            final lado = limites.maxWidth.clamp(0.0, 280.0).toDouble();
            return Container(
              color: Colors.white,
              padding: const EdgeInsets.all(12),
              child: QrImageView(
                data: jsonEncode({'juego': 'Zunpi', 'version': 1,
                  'servidor': destino, 'sala': widget.sala}),
                version: QrVersions.auto,
                size: (lado - 24).clamp(0.0, 256.0).toDouble(),
                padding: const EdgeInsets.all(10),
                backgroundColor: Colors.white,
                errorCorrectionLevel: QrErrorCorrectLevel.M,
                eyeStyle: const QrEyeStyle(
                  eyeShape: QrEyeShape.square, color: Colors.black),
                dataModuleStyle: const QrDataModuleStyle(
                  dataModuleShape: QrDataModuleShape.square, color: Colors.black),
              ),
            );
          }),
          if (opciones.length > 1) DropdownButton<String>(
            value: opciones.contains(destino) ? destino : null,
            isExpanded: true,
            hint: const Text('Elegí la red de la PC'),
            items: opciones.map((url) => DropdownMenuItem(
              value: url, child: Text(Uri.parse(url).host))).toList(),
            onChanged: (url) {
              if (url != null) setState(() {
                destino = url; direccion.text = url; aviso = '';
              });
            },
          ),
          const SizedBox(height: 16),
          TextField(
            controller: direccion,
            keyboardType: TextInputType.url,
            autocorrect: false,
            decoration: const InputDecoration(
              labelText: 'Dirección Wi-Fi de la PC',
              hintText: 'http://192.168.1.50:8001'),
            onSubmitted: (_) => aplicar(),
          ),
          TextButton.icon(onPressed: aplicar,
            icon: const Icon(Icons.qr_code), label: const Text('Actualizar QR')),
          if (aviso.isNotEmpty) Text(aviso,
            style: const TextStyle(color: Colors.amber)),
          const SizedBox(height: 8),
          const Text('PC y celulares en la misma Wi-Fi.\n'
            'Tu amigo ingresa su nombre y toca “Escanear QR”.\n'
            'Probá /salud en el navegador de ambos celulares.',
            textAlign: TextAlign.center),
          if (destino.isNotEmpty) Padding(
            padding: const EdgeInsets.only(top: 10),
            child: SelectableText(destino, textAlign: TextAlign.center)),
        ]),
      ),
    ),
    actions: [TextButton(onPressed: () => Navigator.pop(context),
      child: const Text('Listo'))],
  );

  @override
  void dispose() {
    direccion.dispose();
    super.dispose();
  }
}
