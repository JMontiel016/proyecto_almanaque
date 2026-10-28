# Montaje de conexiones ESP32 — Zunpi

Documento técnico para cablear el ESP32 con OLED, 3 botones y 3 LEDs.
Incluye el diagrama de pines, tabla de conexiones y los cambios de programa necesarios.

---

## Firmware

El ESP32 usa **MicroPython** (no Arduino IDE).

Archivos a copiar al ESP32 con `ampy` (Adafruit MicroPython Tool), `mpremote` o `rshell`:

| Archivo | Función |
|---|---|
| `ssd1306.py` | Driver I2C para el OLED SSD1306 |
| `urequests.py` | Cliente HTTP mínimo (GET/POST) si el firmware no lo incluye |
| `main.py` | Programa principal: Wi-Fi, botones, LEDs, consulta al servidor |

### Pasos para flashear

1. Instalar MicroPython en el ESP32 (firmware `micropython_esp32.bin` desde micropython.org)
2. Instalar una herramienta para subir archivos:
   ```bash
   pip install adafruit-ampy
   # o
   pip install mpremote
   ```
3. Subir los 3 archivos al ESP32:
   ```bash
   ampy --port COM3 put ssd1306.py
   ampy --port COM3 put urequests.py
   ampy --port COM3 put main.py
   ```
4. Editar `main.py` con tus credenciales Wi-Fi, IP del servidor y código de sala antes de subir.

---

## Componentes

| Componente | Cantidad |
|---|---|
| OLED 0.96" SSD1306 I2C | 1 |
| Pulsadores momentáneos | 3 |
| LEDs (rojo, verde, amarillo) | 3 |
| Resistencias 220Ω | 3 (una por LED) |
| Kit cables Dupont M-M | 5 |
| Kit cables Dupont M-F | 5 |
| Cable USB de datos | 1 |
| ESP32 (clásico, no ESP32-CAM) | 1 |

> **Importante:** Si usas un ESP32-CAM, los GPIO 21/22 pueden estar ocupados por la cámara.
> Este diagrama asume un ESP32 clásico.

---

## Lógica de funcionamiento

| Elemento | Función |
|---|---|
| OLED 0.96" | Muestra nombres y puntajes de la sala (consulta al servidor) |
| Botón momentáneo 1 | START / PAUSE (inicia o pausa la ronda) |
| Botón momentáneo 2 | RESET (vuelve al estado de espera) |
| Botón momentáneo 3 | MODE (reservado para uso futuro, sin función aún) |
| LED verde | Se enciende al iniciar el juego (estado `jugando` o `cuenta`) |
| LED amarillo | Se enciende al pausar el juego |
| LED rojo | Se enciende al resetear o ante un error de conexión |

---

## Diagrama de conexiones

```
                      ESP32
                +------------------+
                |                  |
  3.3V -------->| 3V3              |
  GND  -------->| GND              |
                |                  |
  (SDA) GPIO21 |<---- OLED SDA    |
  (SCL) GPIO22 |<---- OLED SCL    |
                |                  |
  BTN START --->| GPIO4  (pull-up) |
  BTN RESET --->| GPIO5  (pull-up) |
  BTN MODE ---->| GPIO18 (pull-up) |
                |                  |
  LED verde  -->| GPIO19 (220Ω)    |
  LED amarillo->| GPIO23 (220Ω)    |
  LED rojo   -->| GPIO25 (220Ω)    |
                |                  |
                +------------------+
```

---

## Detalle de conexiones

### OLED SSD1306 I2C (4 cables Dupont Hembra-Hembra)

| OLED | ESP32 |
|---|---|
| VCC | 3V3 |
| GND | GND |
| SDA | GPIO 21 |
| SCL | GPIO 22 |

### Botones momentáneos (3 pulsadores)

Los botones usan la resistencia pull-up interna del ESP32 (`INPUT_PULLUP`).
Al presionar, el pin se conecta a GND (LOW = presionado). No requieren resistencias externas.

| Botón | ESP32 | Conexión física |
|---|---|---|
| START/PAUSE | GPIO 4 | Un pin del botón a GPIO 4, el otro a GND |
| RESET | GPIO 5 | Un pin del botón a GPIO 5, el otro a GND |
| MODE | GPIO 18 | Un pin del botón a GPIO 18, el otro a GND |

### LEDs (3 LEDs con resistencia de 220Ω cada uno)

| LED | ESP32 | Resistencia | Conexión |
|---|---|---|---|
| Verde | GPIO 19 | 220Ω | Entre GPIO 19 y ánodo (+) del LED |
| Amarillo | GPIO 23 | 220Ω | Entre GPIO 23 y ánodo (+) del LED |
| Rojo | GPIO 25 | 220Ω | Entre GPIO 25 y ánodo (+) del LED |

El cátodo (-) de cada LED va directo a GND.

---

## Uso de cables Dupont

| Tipo | Cantidad usada | Destino |
|---|---|---|
| M-F | 4 | OLED: VCC, GND, SDA, SCL |
| M-F | 1 | Sobrante o puente de GND |
| M-M | 3 | Lado GND de cada botón |
| M-M | 2 | Conexiones restantes en protoboard (LEDs/resistencias) |

---

## Por qué estos pines

| Pin | Función | Razón |
|---|---|---|
| GPIO 21/22 | I2C OLED | I2C dedicado del ESP32 clásico, ya usado en el sketch actual |
| GPIO 4, 5, 18 | Botones | Pines seguros para entrada digital, sin conflicto con boot/flash |
| GPIO 19, 23, 25 | LEDs | Pines seguros para salida digital |
| GPIO 0, 2, 12, 15 | Evitados | Intervienen en el boot del ESP32 (no usar) |
| GPIO 34-39 | Evitados | Solo entrada, no sirven para LEDs |

---

## Estado de implementación (MicroPython)

El firmware del ESP32 está escrito en **MicroPython** y ya incluye toda la funcionalidad:

- Consulta el endpoint `/oled/{codigo}` del servidor para mostrar nombres y puntajes en la OLED.
- Lee 3 botones físicos (START/PAUSE, RESET, MODE) con debounce.
- Controla 3 LEDs (verde, amarillo, rojo) según el estado del juego.
- Envía comandos HTTP POST al servidor al presionar START/PAUSE y RESET.

### Archivos del firmware ESP32

| Archivo | Función |
|---|---|
| `esp32/main.py` | Programa principal: Wi-Fi, botones, LEDs, consulta al servidor, dibujo en OLED |
| `esp32/ssd1306.py` | Driver I2C para el OLED SSD1306 (128x64) |
| `esp32/urequests.py` | Cliente HTTP mínimo (GET/POST) si el firmware no lo incluye |

### Endpoints del servidor utilizados por el ESP32

El servidor Python ya tiene los endpoints HTTP que el ESP32 necesita:

| Endpoint | Función |
|---|---|
| `GET /oled/{codigo}` | Consulta estado y puntajes de la sala |
| `POST /control/{codigo}/iniciar` | Inicia la ronda |
| `POST /control/{codigo}/pausar` | Pausa o reanuda manualmente |
| `POST /control/{codigo}/reset` | Vuelve a estado `espera` |

### Mapeo de estados a LEDs

| Estado del juego | LED encendido |
|---|---|
| `jugando` o `cuenta` | Verde |
| Pausa (manual o por pérdida de seguimiento) | Amarillo |
| `espera`, `terminada` o error de conexión | Rojo |

---

## Notas

- El ESP32 no analiza cámaras ni administra salas. Solo consulta el estado del juego
  y envía comandos de control.
- El botón MODE no tiene función asignada aún. Se reserva el pin GPIO 18 para
  implementarlo en el futuro sin recablear.
- Confirmá el modelo de placa ESP32 y los GPIO libres antes de cablear.
- Si usas un ESP32-CAM, los GPIO 21/22 pueden estar ocupados por la cámara;
  verifica el pinout exacto de tu placa.
- Dirección I2C habitual del SSD1306: `0x3C`. Confírmala si la OLED no responde.
- El firmware usa MicroPython. No requiere instalar librerías de Arduino.
  Solo necesita el driver `ssd1306.py` y `urequests.py` copiados al ESP32.
- El sketch anterior en Arduino C++ (`pantalla_oled.ino`) queda como referencia.
