// Consulta puntos de la sala y controla el juego con botones físicos.
// Botones: START/PAUSE (GPIO4), RESET (GPIO5), MODE (GPIO18).
// LEDs: verde (GPIO19), amarillo (GPIO23), rojo (GPIO25).
#include <WiFi.h> // Conexión Wi-Fi 2,4 GHz.
#include <HTTPClient.h> // API de lectura y control.
#include <ArduinoJson.h> // Instalar ArduinoJson 7 desde Library Manager.
#include <Adafruit_GFX.h> // Instalar Adafruit GFX Library.
#include <Adafruit_SSD1306.h> // Instalar Adafruit SSD1306.
#include <Wire.h> // Bus I2C.

// --- Configuración de red y sala ---
const char* RED = "TU_WIFI"; // Cambiar por tu red.
const char* CLAVE = "TU_CLAVE"; // No compartir este archivo con clave real.
const char* SERVIDOR = "http://192.168.1.10:8001"; // IP del servidor Python.
const char* SALA = "ABC123"; // Copiar código de la sala creado en la aplicación.

// --- Pines OLED I2C ---
const int PIN_SDA = 21; // EJEMPLO para ESP32 clásico: NO asumir válido en ESP32-CAM.
const int PIN_SCL = 22; // Confirmar pinout exacto antes de conectar OLED.
const int ALTO_OLED = 64; // Cambiar a 32 si tu OLED es 128x32.

// --- Pines de botones (entrada con pull-up interna) ---
const int PIN_BTN_START = 4;   // Botón START/PAUSE.
const int PIN_BTN_RESET = 5;   // Botón RESET.
const int PIN_BTN_MODE  = 18;  // Botón MODE (reservado, sin función aún).

// --- Pines de LEDs (salida digital) ---
const int PIN_LED_VERDE    = 19; // LED verde: juego activo.
const int PIN_LED_AMARILLO = 23; // LED amarillo: pausa.
const int PIN_LED_ROJO     = 25; // LED rojo: espera/terminada/error.

// --- Debounce de botones ---
const unsigned long DEBOUNCE_MS = 200; // Tiempo mínimo entre pulsaciones.
unsigned long ultimoBtnStart = 0;
unsigned long ultimoBtnReset = 0;
unsigned long ultimoBtnMode  = 0;

// --- Estado del juego leído del servidor ---
String estadoJuego = "sin sala"; // espera, cuenta, jugando, terminada, sin sala.
bool pausada = false; // Pausa manual o automática.

// --- Objetos y temporizadores ---
Adafruit_SSD1306 pantalla(128, ALTO_OLED, &Wire, -1); // Driver SSD1306, no SH1106.
unsigned long ultimaConsulta = 0; // Frecuencia sin delay bloqueante.
unsigned long reconexion = 0; // Intentos de Wi-Fi separados.

// --- Prototipos de funciones ---
void mensaje(const char* texto);
void consultarServidor();
void actualizarLEDs();
void manejarBotones();
void enviarComando(const char* ruta);
bool debounce(unsigned long* ultimo);

void setup() {
  Serial.begin(115200); // Diagnóstico USB.

  // Configurar pines de botones con pull-up interna.
  pinMode(PIN_BTN_START, INPUT_PULLUP);
  pinMode(PIN_BTN_RESET, INPUT_PULLUP);
  pinMode(PIN_BTN_MODE,  INPUT_PULLUP);

  // Configurar pines de LEDs como salida.
  pinMode(PIN_LED_VERDE,    OUTPUT);
  pinMode(PIN_LED_AMARILLO, OUTPUT);
  pinMode(PIN_LED_ROJO,     OUTPUT);

  // Apagar todos los LEDs al iniciar.
  digitalWrite(PIN_LED_VERDE,    LOW);
  digitalWrite(PIN_LED_AMARILLO, LOW);
  digitalWrite(PIN_LED_ROJO,     LOW);

  // Inicializar OLED.
  Wire.begin(PIN_SDA, PIN_SCL); // Usar solo luego de verificar pines de TU placa.
  if (!pantalla.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { // Dirección I2C habitual; confirmar.
    Serial.println("OLED no encontrada; verificar driver, pines y direccion");
    digitalWrite(PIN_LED_ROJO, HIGH); // LED rojo indica error de hardware.
    while (true) delay(1000); // Sin pantalla no continúa.
  }
  pantalla.setTextColor(SSD1306_WHITE); // Panel monocromático.
  pantalla.setTextSize(1); // Nombres y números compactos.

  // Conectar Wi-Fi.
  WiFi.mode(WIFI_STA); // Se une a la misma red que servidor/celulares.
  WiFi.begin(RED, CLAVE); // Conexión no bloqueante.
  mensaje("Conectando Wi-Fi"); // Feedback inmediato.
}

void loop() {
  // Sin Wi-Fi no se puede consultar ni controlar el juego.
  if (WiFi.status() != WL_CONNECTED) {
    if (millis() - reconexion > 10000) {
      reconexion = millis(); // Intervalo de reconexión.
      WiFi.reconnect(); // Reintenta sin cambiar credenciales.
      mensaje("Sin Wi-Fi");
    }
    estadoJuego = "sin sala";
    actualizarLEDs(); // Enciende LED rojo.
    return;
  }

  manejarBotones(); // Lee botones y envía comandos HTTP si se presionan.
  consultarServidor(); // Consulta estado y puntajes del servidor.
  actualizarLEDs(); // Enciende LED según el estado del juego.
}

// --- Debounce: retorna true si pasó el tiempo mínimo desde la última pulsación ---
bool debounce(unsigned long* ultimo) {
  unsigned long ahora = millis();
  if (ahora - *ultimo < DEBOUNCE_MS) return false;
  *ultimo = ahora;
  return true;
}

// --- Maneja los 3 botones físicos ---
void manejarBotones() {
  // Botón START/PAUSE: alterna entre iniciar y pausar según el estado.
  if (digitalRead(PIN_BTN_START) == LOW && debounce(&ultimoBtnStart)) {
    if (estadoJuego == "espera" || estadoJuego == "terminada") {
      enviarComando("/control/" + String(SALA) + "/iniciar");
    } else if (estadoJuego == "cuenta" || estadoJuego == "jugando") {
      enviarComando("/control/" + String(SALA) + "/pausar");
    }
  }

  // Botón RESET: vuelve a estado de espera.
  if (digitalRead(PIN_BTN_RESET) == LOW && debounce(&ultimoBtnReset)) {
    enviarComando("/control/" + String(SALA) + "/reset");
  }

  // Botón MODE: reservado para uso futuro. No envía comandos aún.
  if (digitalRead(PIN_BTN_MODE) == LOW && debounce(&ultimoBtnMode)) {
    Serial.println("Boton MODE presionado (sin funcion asignada)");
    // Aquí se agregará la funcionalidad de MODE en el futuro.
  }
}

// --- Envía un comando HTTP POST al servidor ---
void enviarComando(const String& ruta) {
  HTTPClient http;
  http.setTimeout(2000); // No bloquea durante muchos segundos.
  String url = String(SERVIDOR) + ruta;
  http.begin(url);
  int codigo = http.POST(""); // POST sin cuerpo; el servidor lee el código de la URL.
  if (codigo > 0) {
    String respuesta = http.getString();
    Serial.printf("Comando %s -> HTTP %d: %s\n", ruta.c_str(), codigo, respuesta.c_str());
  } else {
    Serial.printf("Error al enviar comando %s: %s\n", ruta.c_str(), http.errorToString(codigo).c_str());
  }
  http.end();
}

// --- Consulta el estado y puntajes del servidor cada 1 segundo ---
void consultarServidor() {
  if (millis() - ultimaConsulta < 1000) return; // Una consulta por segundo.
  ultimaConsulta = millis();

  HTTPClient consulta;
  consulta.setTimeout(1500); // No bloquea durante muchos segundos.
  consulta.begin(String(SERVIDOR) + "/oled/" + SALA); // Ruta pública de la sala.
  int codigo = consulta.GET(); // Solo lectura; no altera juego.
  if (codigo != 200) {
    mensaje("Servidor sin respuesta");
    estadoJuego = "sin sala";
    consulta.end();
    return;
  }

  JsonDocument datos;
  auto error = deserializeJson(datos, consulta.getString());
  consulta.end();
  if (error) {
    mensaje("Respuesta invalida");
    estadoJuego = "sin sala";
    return;
  }

  // Guardar estado del juego para control de LEDs.
  estadoJuego = datos["estado"] | "sin sala";
  pausada = datos["pausada"] | false; // Pausa manual o automática reportada por el servidor.

  // Dibujar puntajes en la OLED.
  pantalla.clearDisplay();
  pantalla.setCursor(0, 0);
  pantalla.println("Zunpi - puntos");

  JsonArray jugadores = datos["jugadores"].as<JsonArray>();
  int porPagina = ALTO_OLED >= 64 ? 4 : 2;
  int cantidad = jugadores.size();
  int paginas = max(1, (cantidad + porPagina - 1) / porPagina);
  int pagina = (millis() / 4000) % paginas;

  for (int i = pagina * porPagina; i < min(cantidad, (pagina + 1) * porPagina); i++) {
    const char* nombre = jugadores[i]["nombre"] | "Jugador";
    String corto;
    for (int k = 0; nombre[k] && corto.length() < 10; k++) {
      if ((unsigned char)nombre[k] < 128) corto += nombre[k];
    }
    if (corto.isEmpty()) corto = "Jugador";
    pantalla.print(i + 1);
    pantalla.print(" ");
    pantalla.print(corto);
    pantalla.print(" ");
    pantalla.println(jugadores[i]["puntos"].as<int>());
  }

  if (!cantidad) pantalla.println("Sin jugadores");
  pantalla.display();
}

// --- Enciende el LED correspondiente según el estado del juego ---
void actualizarLEDs() {
  // Apagar todos primero.
  digitalWrite(PIN_LED_VERDE,    LOW);
  digitalWrite(PIN_LED_AMARILLO, LOW);
  digitalWrite(PIN_LED_ROJO,     LOW);

  if (estadoJuego == "sin sala" || estadoJuego == "espera" || estadoJuego == "terminada") {
    digitalWrite(PIN_LED_ROJO, HIGH); // Rojo: sin sala, espera o terminada.
  } else if (estadoJuego == "pausada" || pausada) {
    digitalWrite(PIN_LED_AMARILLO, HIGH); // Amarillo: pausa (manual o automática).
  } else if (estadoJuego == "cuenta" || estadoJuego == "jugando") {
    digitalWrite(PIN_LED_VERDE, HIGH); // Verde: juego activo.
  } else {
    digitalWrite(PIN_LED_ROJO, HIGH); // Rojo: estado desconocido o error.
  }
}

// --- Muestra un mensaje corto en la OLED ---
void mensaje(const char* texto) {
  pantalla.clearDisplay();
  pantalla.setCursor(0, 0);
  pantalla.println("Zunpi");
  pantalla.println(texto);
  pantalla.display();
}
