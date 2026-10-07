// Consulta puntos de la sala; la cámara del ESP32 no interviene en este prototipo.
#include <WiFi.h> // Conexión Wi-Fi 2,4 GHz.
#include <HTTPClient.h> // API de solo lectura.
#include <ArduinoJson.h> // Instalar ArduinoJson 7 desde Library Manager.
#include <Adafruit_GFX.h> // Instalar Adafruit GFX Library.
#include <Adafruit_SSD1306.h> // Instalar Adafruit SSD1306.
#include <Wire.h> // Bus I2C.

const char* RED = "TU_WIFI"; // Cambiar por tu red.
const char* CLAVE = "TU_CLAVE"; // No compartir este archivo con clave real.
const char* SERVIDOR = "http://192.168.1.10:8000"; // IP del servidor Python.
const char* SALA = "ABC123"; // Copiar código de la sala creado en la aplicación.
const int PIN_SDA = 21; // EJEMPLO para ESP32 clásico: NO asumir válido en ESP32-CAM.
const int PIN_SCL = 22; // Confirmar pinout exacto antes de conectar OLED.
const int ALTO_OLED = 64; // Cambiar a 32 si tu OLED es 128x32.
Adafruit_SSD1306 pantalla(128, ALTO_OLED, &Wire, -1); // Driver SSD1306, no SH1106.
unsigned long ultimaConsulta = 0; // Frecuencia sin delay bloqueante.
unsigned long reconexion = 0; // Intentos de Wi-Fi separados.

void mensaje(const char* texto) {
  pantalla.clearDisplay(); // Limpia panel anterior.
  pantalla.setCursor(0, 0); // Esquina superior.
  pantalla.println("Zunpi"); // Nombre corto.
  pantalla.println(texto); // Estado de red/sala.
  pantalla.display(); // Actualiza OLED.
}

void setup() {
  Serial.begin(115200); // Diagnóstico USB.
  Wire.begin(PIN_SDA, PIN_SCL); // Usar solo luego de verificar pines de TU placa.
  if (!pantalla.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { // Dirección I2C habitual; confirmar.
    Serial.println("OLED no encontrada; verificar driver, pines y direccion"); // Diagnóstico.
    while (true) delay(1000); // Sin pantalla no continúa.
  }
  pantalla.setTextColor(SSD1306_WHITE); // Panel monocromático.
  pantalla.setTextSize(1); // Nombres y números compactos.
  WiFi.mode(WIFI_STA); // Se une a la misma red que servidor/celulares.
  WiFi.begin(RED, CLAVE); // Conexión no bloqueante.
  mensaje("Conectando Wi-Fi"); // Feedback inmediato.
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) { // No consulta sin Wi-Fi.
    if (millis() - reconexion > 10000) {
      reconexion = millis(); // Intervalo de reconexión.
      WiFi.reconnect(); // Reintenta sin cambiar credenciales.
      mensaje("Sin Wi-Fi"); // No muestra puntajes obsoletos como actuales.
    }
    return;
  }
  if (millis() - ultimaConsulta < 1000) return; // Una consulta por segundo.
  ultimaConsulta = millis(); // Marca actualización.
  HTTPClient consulta; // Cliente temporal.
  consulta.setTimeout(1500); // No bloquea durante muchos segundos.
  consulta.begin(String(SERVIDOR) + "/oled/" + SALA); // Ruta pública de la sala.
  int codigo = consulta.GET(); // Solo lectura; no altera juego.
  if (codigo != 200) { // Trata errores de red y HTTP.
    mensaje("Servidor sin respuesta");
    consulta.end(); // Libera conexión.
    return;
  }
  JsonDocument datos; // ArduinoJson 7.
  auto error = deserializeJson(datos, consulta.getString()); // Lee ranking de ronda.
  consulta.end(); // Libera HTTP antes de dibujar.
  if (error) { mensaje("Respuesta invalida"); return; } // No dibuja datos corruptos.
  pantalla.clearDisplay(); // Nueva página.
  pantalla.setCursor(0, 0); // Título.
  pantalla.println("Zunpi - puntos"); // Encabezado.
  JsonArray jugadores = datos["jugadores"].as<JsonArray>(); // Ordenados por Python.
  int porPagina = ALTO_OLED >= 64 ? 4 : 2; // 128x64 admite cuatro; 128x32 pagina dos.
  int cantidad = jugadores.size(); // Máximo cuatro.
  int paginas = max(1, (cantidad + porPagina - 1) / porPagina); // Evita dividir entre cero.
  int pagina = (millis() / 4000) % paginas; // Alterna cada cuatro segundos.
  for (int i = pagina * porPagina; i < min(cantidad, (pagina + 1) * porPagina); i++) {
    const char* nombre = jugadores[i]["nombre"] | "Jugador"; // Nombre recibido.
    String corto; // OLED GFX básica no renderiza Unicode completo.
    for (int k = 0; nombre[k] && corto.length() < 10; k++) {
      if ((unsigned char)nombre[k] < 128) corto += nombre[k]; // Conserva ASCII sin cortar UTF-8.
    }
    if (corto.isEmpty()) corto = "Jugador"; // Fallback para nombre sin ASCII.
    pantalla.print(i + 1); // Puesto.
    pantalla.print(" ");
    pantalla.print(corto); // Nombre corto, original completo se ve en Android.
    pantalla.print(" ");
    pantalla.println(jugadores[i]["puntos"].as<int>()); // Puntaje de ronda.
  }
  if (!cantidad) pantalla.println("Sin jugadores"); // Sala no disponible.
  pantalla.display(); // Un único refresco completo.
}
