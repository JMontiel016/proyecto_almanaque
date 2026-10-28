# Zunpi — Instrucciones de inicio

Guía paso a paso para iniciar el sistema completo cada vez que quieras jugar.
Adaptado para Windows.

---

## Resumen del sistema

Zunpi tiene 3 componentes que funcionan juntos:

| Componente | Dónde corre | Función |
|---|---|---|
| **Servidor Python** | Esta PC (puerto 8001) | Lógica del juego, detección corporal con MediaPipe, WebSocket, ranking |
| **App Flutter** | Teléfono Android | Cámara, interfaz del juego, envía frames JPEG al servidor |
| **ESP32 + OLED** | Hardware físico | Muestra puntajes en pantalla OLED, botones físicos de control, LEDs de estado |

**Orden de inicio obligatorio:** Servidor Python primero → App Flutter después → ESP32 opcional.

---

## Requisitos previos (verificar una sola vez)

### En la PC

```powershell
# Verificar Flutter
flutter --version
# Debe mostrar Flutter 3.47.x o superior

# Verificar Python
python --version
# Debe mostrar Python 3.12.x o superior

# Verificar Android SDK
flutter doctor
# Debe marcar [√] en Flutter, Android toolchain y Connected device
```

### En el teléfono

- Depuración USB activada (Ajustes → Opciones de desarrollador)
- App Zunpi instalada (verificar que aparece en el launcher)

### En el ESP32 (si se usa)

- MicroPython flasheado
- Archivos `main.py`, `ssd1306.py`, `urequests.py` subidos
- `main.py` configurado con Wi-Fi, IP del servidor y código de sala correctos

---

## Paso 1 — Iniciar el servidor Python

Abrir una terminal (PowerShell o CMD) y ejecutar:

```powershell
cd C:\Users\imira\OneDrive\Desktop\proyecto_robotica\proyecto_almanaque\servidor

# Activar el entorno virtual
.\.venv\Scripts\Activate.ps1

# Iniciar el servidor
python -m uvicorn servidor:app --host 0.0.0.0 --port 8001 --workers 1
```

Dejar esta terminal abierta durante toda la sesión de juego.

### Verificar que el servidor responde

Abrir en el navegador: `http://localhost:8001/salud`

Debe mostrar algo como:
```json
{
  "estado": "disponible",
  "juego": "Zunpi",
  "version": "0.4.0",
  "detector_precargado": true,
  "modelo": true
}
```

Si `modelo` es `false`, ejecutar (con la venv activa):
```powershell
python descargar_modelo.py
```

### Obtener la IP de la PC (para modo Wi-Fi)

```powershell
ipconfig
# Buscar la línea "IPv4" de la tarjeta de red conectada al Wi-Fi
# Ejemplo: 192.168.1.10
```

Anotar esa IP; la necesitarán los teléfonos en modo Wi-Fi.

---

## Paso 2 — Conectar el teléfono y abrir la app

### Opción A: Conexión por USB (recomendado, menor latencia)

1. Conectar el teléfono por cable USB, desbloqueado, con depuración USB activada.
2. Verificar que ADB lo reconoce:
   ```powershell
   adb devices
   # Debe mostrar el dispositivo como "device"
   ```
3. Configurar el puente ADB (redirige el puerto de la PC al teléfono):
   ```powershell
   adb reverse tcp:8001 tcp:8001
   ```
4. En la app, seleccionar **USB** y tocar **Comprobar conexión**.
   - La app usará `http://127.0.0.1:8001` automáticamente.
   - Debe mostrar latencia y versión 0.4.0.

### Opción B: Conexión por Wi-Fi

1. Asegurarse de que la PC y el teléfono estén en la misma red Wi-Fi.
2. En la app, seleccionar **Wi-Fi**.
3. Escribir la dirección: `http://IP_DE_LA_PC:8001`
   (ejemplo: `http://192.168.1.10:8001`)
4. Tocar **Comprobar conexión**.

### Si la app no está instalada en el teléfono

```powershell
cd C:\Users\imira\OneDrive\Desktop\proyecto_robotica\proyecto_almanaque\aplicacion

# Resolver dependencias
flutter pub get

# Instalar y ejecutar en el teléfono conectado (modo debug)
flutter run -d <ID_DEL_DISPOSITIVO>

# Para ver el ID del dispositivo:
adb devices
```

La primera compilación tarda varios minutos. Las siguientes son más rápidas.

---

## Paso 3 — Jugar

1. Ingresar nombre en la app.
2. Tocar **Jugar** (o crear sala con **Crear sala e invitar por QR** si hay más jugadores).
3. La cámara se abre. Apoyar el teléfono y mostrar cabeza + ambos pies.
4. Calibrar quedándose quieto hasta completar 12/12 muestras.
5. Tocar **Estoy listo**.
6. El administrador (primer jugador conectado) toca **Jugar** para iniciar la ronda.
7. Saltar para esquivar cactus. Una colisión = una vida perdida.
8. Al terminar todos, confirmar para otra ronda.

### Invitar amigos

- **Anfitrión:** tocar **Crear sala e invitar por QR** desde inicio. Se muestra un QR.
- **Invitado:** abrir la app, ingresar nombre, tocar **Escanear QR de un amigo**.
- Máximo 4 jugadores por sala. El QR carga la dirección y la sala automáticamente.

---

## Paso 4 (opcional) — ESP32 + OLED

El ESP32 se enciende y ejecuta `main.py` automáticamente. Solo funciona si:

1. El servidor Python ya está corriendo en la PC.
2. El ESP32 tiene configurados los siguientes valores en `main.py`:

```python
RED = "TU_WIFI"           # Nombre de tu red Wi-Fi
CLAVE = "TU_CLAVE"        # Clave del Wi-Fi
SERVIDOR = "http://192.168.1.10:8001"  # IP de la PC + puerto 8001
SALA = "ABC123"           # Código de sala (se obtiene al crear la sala en la app)
```

3. Al encender, el ESP32:
   - Conecta al Wi-Fi (muestra "Conectando Wi-Fi" en OLED)
   - Consulta al servidor cada segundo el estado de la sala
   - Muestra puntajes en la OLED, paginando cada 4 segundos
   - LED verde: juego activo | amarillo: pausa | rojo: espera/error

### Botones físicos del ESP32

| Botón | Función |
|---|---|
| START/PAUSE | Inicia la ronda o alterna pausa manual |
| RESET | Vuelve la sala a estado de espera |
| MODE | Reservado (sin función aún) |

---

## Cierre del sistema

1. Cerrar la app en el teléfono (salir con botón atrás o cerrar sesión).
2. Detener el servidor Python con `Ctrl+C` en la terminal.
3. Apagar el ESP32 (desconectar USB o fuente).

---

## Solución de problemas

### El servidor no inicia

```
Error: Address already in use
```
Ya hay otro proceso usando el puerto 8001. Cerrarlo:
```powershell
# Buscar qué proceso usa el puerto 8001
netstat -ano | findstr :8001
# Terminar el proceso por su PID
taskkill /PID <PID> /F
```

### La app no conecta por USB

- Verificar que el cable sea de datos (no solo carga).
- Ejecutar `adb reverse tcp:8001 tcp:8001` nuevamente.
- Comprobar `adb devices` muestra el teléfono como `device` (no `unauthorized`).
- Si aparece `unauthorized`, aceptar el diálogo de depuración en el teléfono.

### La app no conecta por Wi-Fi

- PC y teléfono en la misma red Wi-Fi (no una red de invitados).
- Verificar firewall de Windows no bloquea el puerto 8001.
- Comprobar desde el navegador del teléfono: `http://IP_DE_LA_PC:8001/salud`.
- Si hay VPN o Docker activos, pueden interferir; desactivarlos o usar USB.

### El ESP32 no muestra puntajes

- Verificar que el código de sala en `main.py` coincida con la sala creada en la app.
- Verificar que el ESP32 y la PC estén en la misma red Wi-Fi.
- El LED rojo encendido indica error de conexión o sala inexistente.

### El modelo no carga (detector_precargado: false)

```powershell
cd C:\Users\imira\OneDrive\Desktop\proyecto_robotica\proyecto_almanaque\servidor
.\.venv\Scripts\Activate.ps1
python descargar_modelo.py
```

Requiere conexión a internet para descargar el modelo de MediaPipe.

### Flutter no reconoce el dispositivo

```powershell
adb kill-server
adb start-server
adb devices
```

Si sigue sin aparecer, reinstalar drivers USB del teléfono o probar otro cable/puerto.

---

## Comandos de referencia rápida

| Acción | Comando |
|---|---|
| Activar venv | `.\.venv\Scripts\Activate.ps1` |
| Iniciar servidor | `python -m uvicorn servidor:app --host 0.0.0.0 --port 8001 --workers 1` |
| Verificar servidor | Navegador: `http://localhost:8001/salud` |
| Ver dispositivos ADB | `adb devices` |
| Puente USB | `adb reverse tcp:8001 tcp:8001` |
| Instalar app | `flutter run -d <ID>` |
| Ejecutar pruebas Python | `python -m pytest servidor/pruebas -v` |
| Ejecutar pruebas Flutter | `flutter test` |
| Analizar código Flutter | `flutter analyze` |
| Ver IP de la PC | `ipconfig` |

---

## Rutas del proyecto

```
proyecto_almanaque/
├── aplicacion/          # App Flutter (Android)
│   ├── lib/             # Código Dart
│   ├── android/         # Configuración Android generada
│   └── pubspec.yaml     # Dependencias Flutter
├── servidor/            # Servidor Python (FastAPI)
│   ├── servidor.py      # API principal
│   ├── motor.py         # Lógica del juego
│   ├── seguimiento.py   # Detección corporal MediaPipe
│   ├── detector_salto.py# Reconocimiento de saltos
│   ├── almacenamiento.py# Ranking SQLite
│   ├── modelos/         # Modelo de pose (descargar_modelo.py)
│   ├── pruebas/         # Tests pytest
│   ├── .venv/           # Entorno virtual Python
│   └── requirements.txt # Dependencias Python
├── esp32/               # Firmware MicroPython
│   ├── main.py          # Programa principal ESP32
│   ├── ssd1306.py       # Driver OLED
│   └── urequests.py     # Cliente HTTP
├── documentacion/       # Guías técnicas
└── INSTRUCCIONES.md     # Este archivo
```
