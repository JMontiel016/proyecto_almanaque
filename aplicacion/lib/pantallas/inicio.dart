import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;

import 'partida.dart';

class Inicio extends StatefulWidget {
  const Inicio({super.key});
  @override
  State<Inicio> createState() => _EstadoInicio();
}

class _EstadoInicio extends State<Inicio> {
  final servidor = TextEditingController(text: 'http://127.0.0.1:8001');
  bool usb = true, ocupado = true;
  String aviso = '';

  @override
  void initState() {
    super.initState();
    cargar();
  }

  Future<void> cargar() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      if (!mounted) return;
      servidor.text = prefs.getString('servidor') ?? servidor.text;
      usb = Uri.tryParse(servidor.text)?.host == '127.0.0.1';
    } catch (error) {
      if (mounted) aviso = 'No se pudo recuperar la configuración: $error';
    } finally {
      if (mounted) setState(() => ocupado = false);
    }
  }

  Future<void> conectar(bool jugar) async {
    setState(() {
      ocupado = true;
      aviso = '';
    });
    try {
      final uri = Uri.tryParse(servidor.text.trim());
      if (uri == null ||
          !['http', 'https'].contains(uri.scheme) ||
          uri.host.isEmpty ||
          uri.userInfo.isNotEmpty ||
          uri.hasQuery ||
          uri.hasFragment ||
          uri.path.replaceAll('/', '').isNotEmpty) {
        throw StateError('Ingresá http://IP_DE_LA_PC:8001');
      }
      final base = uri.replace(path: '').toString();
      final respuesta = await http
          .get(Uri.parse('$base/salud'))
          .timeout(const Duration(seconds: 5));
      if (respuesta.statusCode != 200) {
        throw StateError('El servidor no respondió correctamente.');
      }
      final datos = jsonDecode(respuesta.body) as Map<String, dynamic>;
      if (datos['juego'] != 'Zunpi' || datos['version'] != '0.5.0') {
        throw StateError('Reiniciá Python con la versión individual 0.5.0.');
      }
      if (datos['modelo'] != true) {
        throw StateError('Ejecutá descargar_modelo.py en la carpeta servidor.');
      }
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('servidor', base);
      if (!mounted) return;
      if (jugar) {
        await Navigator.push(
          context,
          MaterialPageRoute<void>(builder: (_) => Partida(servidor: base)),
        );
      } else {
        setState(() => aviso = 'Servidor conectado. Ya podés jugar.');
      }
    } catch (error) {
      if (mounted) setState(() => aviso = '$error');
    } finally {
      if (mounted) setState(() => ocupado = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Zunpi')),
    body: SafeArea(
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 520),
          child: ListView(
            shrinkWrap: true,
            padding: const EdgeInsets.all(24),
            children: [
              const Text(
                'Saltá y agachate',
                style: TextStyle(fontSize: 30, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 12),
              const Text(
                'Saltá los cactus y agachate para evitar las aves. Apoyá el celular y dejá visibles tus hombros y ambos pies.',
              ),
              const SizedBox(height: 24),
              SegmentedButton<bool>(
                segments: const [
                  ButtonSegment(
                    value: true,
                    label: Text('USB'),
                    icon: Icon(Icons.usb),
                  ),
                  ButtonSegment(
                    value: false,
                    label: Text('Wi-Fi'),
                    icon: Icon(Icons.wifi),
                  ),
                ],
                selected: {usb},
                onSelectionChanged: ocupado
                    ? null
                    : (valor) => setState(() {
                        usb = valor.first;
                        servidor.text = usb ? 'http://127.0.0.1:8001' : '';
                        aviso = '';
                      }),
              ),
              const SizedBox(height: 16),
              Text(
                usb ? 'En la PC ejecutá: adb reverse tcp:8001 tcp:8001' : 'PC y celular en la misma Wi-Fi. Ingresá la IPv4 de la PC con el puerto 8001.',
              ),
              const SizedBox(height: 16),
              TextField(
                controller: servidor,
                readOnly: usb || ocupado,
                keyboardType: TextInputType.url,
                autocorrect: false,
                decoration: const InputDecoration(
                  labelText: 'Servidor Python',
                  hintText: 'http://192.168.1.50:8001',
                ),
              ),
              const SizedBox(height: 12),
              if (aviso.isNotEmpty)
                Text(aviso, style: const TextStyle(color: Colors.amber)),
              TextButton(
                onPressed: ocupado ? null : () => conectar(false),
                child: const Text('Comprobar conexión'),
              ),
              FilledButton(
                onPressed: ocupado ? null : () => conectar(true),
                child: Text(ocupado ? 'Conectando…' : 'Abrir juego'),
              ),
            ],
          ),
        ),
      ),
    ),
  );

  @override
  void dispose() {
    servidor.dispose();
    super.dispose();
  }
}
