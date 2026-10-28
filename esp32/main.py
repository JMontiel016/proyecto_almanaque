# main.py - Control del juego Zunpi desde ESP32 con MicroPython
# Pantalla OLED SSD1306 128x64 por I2C (SDA=21, SCL=22)
# Botones: START/PAUSE (GPIO4), RESET (GPIO5), MODE (GPIO18)
# LEDs: verde (GPIO19), amarillo (GPIO23), rojo (GPIO25)
# Consulta el estado del servidor y muestra puntajes en la OLED.
#
# Se ejecuta automaticamente al encender el ESP32 (despues de boot.py).

import machine
import network
import json
import time

# Importar urequests: intentar modulo del firmware, luego archivo local
try:
    import urequests
except ImportError:
    import requests as urequests

from ssd1306 import SSD1306_I2C

# --- Configuracion de red y sala ---
# RED = "null"  # Red Wi-Fi (anterior, 5 GHz - ESP32 no soporta 5 GHz)
# CLAVE = "motomoto"  # Clave Wi-Fi anterior
# SERVIDOR = "http://192.168.100.5:8001"  # IP del servidor Python anterior
RED = "Brosco La Verdad"  # Red Wi-Fi actual (2.4 GHz)
CLAVE = "Brosco2025"  # Clave Wi-Fi actual
SERVIDOR = "http://192.168.166.190:8001"  # IP del servidor Python actual
SALA = "ABC123"  # Codigo de la sala creado en la aplicacion

# --- Pines OLED I2C ---
PIN_SDA = 21
PIN_SCL = 22
ALTO_OLED = 64  # Cambiar a 32 si tu OLED es 128x32

# --- Pines de botones (entrada con pull-up interna) ---
PIN_BTN_START = 4  # Boton START/PAUSE
PIN_BTN_RESET = 5  # Boton RESET
PIN_BTN_MODE = 18  # Boton MODE (reservado, sin funcion aun)

# --- Pines de LEDs (salida digital) ---
PIN_LED_VERDE = 19  # LED verde: juego activo
PIN_LED_AMARILLO = 23  # LED amarillo: pausa
PIN_LED_ROJO = 25  # LED rojo: espera/terminada/error

# --- Debounce de botones ---
DEBOUNCE_MS = 200  # Tiempo minimo entre pulsaciones (ms)

# --- Estado global del juego ---
estado_juego = "sin sala"  # espera, cuenta, jugando, terminada, sin sala
pausada = False  # Pausa manual o automatica
ultima_consulta = 0  # Timestamp de la ultima consulta al servidor
ultimo_btn_start = 0  # Timestamp del ultimo boton START
ultimo_btn_reset = 0  # Timestamp del ultimo boton RESET
ultimo_btn_mode = 0  # Timestamp del ultimo boton MODE
reconexion = 0  # Timestamp del ultimo intento de reconexion Wi-Fi

# --- Objetos de hardware ---
i2c = None
oled = None
btn_start = None
btn_reset = None
btn_mode = None
led_verde = None
led_amarillo = None
led_rojo = None
wlan = None


def init_hardware():
    """Inicializa botones, LEDs y pantalla OLED."""
    global i2c, oled, btn_start, btn_reset, btn_mode
    global led_verde, led_amarillo, led_rojo

    # Botones con pull-up interna (LOW = presionado)
    btn_start = machine.Pin(PIN_BTN_START, machine.Pin.IN, machine.Pin.PULL_UP)
    btn_reset = machine.Pin(PIN_BTN_RESET, machine.Pin.IN, machine.Pin.PULL_UP)
    btn_mode = machine.Pin(PIN_BTN_MODE, machine.Pin.IN, machine.Pin.PULL_UP)

    # LEDs como salida digital
    led_verde = machine.Pin(PIN_LED_VERDE, machine.Pin.OUT)
    led_amarillo = machine.Pin(PIN_LED_AMARILLO, machine.Pin.OUT)
    led_rojo = machine.Pin(PIN_LED_ROJO, machine.Pin.OUT)
    led_verde.off()
    led_amarillo.off()
    led_rojo.off()

    # OLED SSD1306 por I2C
    i2c = machine.I2C(0, scl=machine.Pin(PIN_SCL), sda=machine.Pin(PIN_SDA), freq=100000)
    try:
        oled = SSD1306_I2C(128, ALTO_OLED, i2c, addr=0x3C)
    except Exception as e:
        print("OLED no encontrada: verificar driver, pines y direccion")
        print("Error: {}".format(e))
        led_rojo.on()  # LED rojo indica error de hardware
        while True:
            time.sleep(1)  # Sin pantalla no continua


def conectar_wifi():
    """Activa el WLAN y conecta a la red configurada."""
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(RED, CLAVE)
        mostrar_mensaje("Conectando Wi-Fi")


def mostrar_mensaje(texto):
    """Muestra un mensaje corto en la OLED."""
    oled.fill(0)
    oled.text("Zunpi", 0, 0)
    oled.text(texto, 0, 8)
    oled.show()


def debounce_ok(ultimo):
    """Retorna (True, ahora) si paso el tiempo minimo de debounce."""
    ahora = time.ticks_ms()
    if time.ticks_diff(ahora, ultimo) < DEBOUNCE_MS:
        return False, ultimo
    return True, ahora


def manejar_botones():
    """Lee los 3 botones fisicos y envia comandos HTTP si se presionan."""
    global estado_juego, ultimo_btn_start, ultimo_btn_reset, ultimo_btn_mode

    # Boton START/PAUSE: alterna entre iniciar y pausar segun el estado
    if btn_start.value() == 0:
        ok, nuevo = debounce_ok(ultimo_btn_start)
        if ok:
            ultimo_btn_start = nuevo
            if estado_juego in ("espera", "terminada"):
                enviar_comando("/control/{}/iniciar".format(SALA))
            elif estado_juego in ("cuenta", "jugando"):
                enviar_comando("/control/{}/pausar".format(SALA))

    # Boton RESET: vuelve a estado de espera
    if btn_reset.value() == 0:
        ok, nuevo = debounce_ok(ultimo_btn_reset)
        if ok:
            ultimo_btn_reset = nuevo
            enviar_comando("/control/{}/reset".format(SALA))

    # Boton MODE: reservado para uso futuro, sin funcion asignada
    if btn_mode.value() == 0:
        ok, nuevo = debounce_ok(ultimo_btn_mode)
        if ok:
            ultimo_btn_mode = nuevo
            print("Boton MODE presionado (sin funcion asignada)")


def enviar_comando(ruta):
    """Envia un comando HTTP POST al servidor."""
    url = SERVIDOR + ruta
    try:
        resp = urequests.post(url, timeout=2)
        print("Comando {} -> HTTP {}".format(ruta, resp.status_code))
        resp.close()
    except Exception as e:
        print("Error al enviar comando {}: {}".format(ruta, e))


def consultar_servidor():
    """Consulta el estado y puntajes del servidor cada 1 segundo."""
    global estado_juego, pausada, ultima_consulta

    ahora = time.ticks_ms()
    if time.ticks_diff(ahora, ultima_consulta) < 1000:
        return  # Una consulta por segundo
    ultima_consulta = ahora

    url = "{}/oled/{}".format(SERVIDOR, SALA)
    try:
        resp = urequests.get(url, timeout=1.5)
        if resp.status_code != 200:
            mostrar_mensaje("Servidor sin respuesta")
            estado_juego = "sin sala"
            resp.close()
            return

        datos = resp.json()
        resp.close()

        estado_juego = datos.get("estado", "sin sala")
        pausada = datos.get("pausada", False)

        # Dibujar puntajes en la OLED
        oled.fill(0)
        oled.text("Zunpi - puntos", 0, 0)

        jugadores = datos.get("jugadores", [])
        cantidad = len(jugadores)
        por_pagina = 4 if ALTO_OLED >= 64 else 2
        paginas = max(1, (cantidad + por_pagina - 1) // por_pagina)
        pagina = (ahora // 4000) % paginas

        y = 8
        inicio = pagina * por_pagina
        fin = min(cantidad, (pagina + 1) * por_pagina)
        for i in range(inicio, fin):
            nombre = jugadores[i].get("nombre", "Jugador")
            # Truncar nombre a 10 caracteres ASCII (sin tildes)
            corto = ""
            for c in nombre:
                if ord(c) < 128 and len(corto) < 10:
                    corto += c
            if not corto:
                corto = "Jugador"
            puntos = jugadores[i].get("puntos", 0)
            linea = "{} {} {}".format(i + 1, corto, puntos)
            oled.text(linea, 0, y)
            y += 8

        if cantidad == 0:
            oled.text("Sin jugadores", 0, 8)

        oled.show()

    except Exception as e:
        print("Error al consultar servidor: {}".format(e))
        mostrar_mensaje("Servidor sin respuesta")
        estado_juego = "sin sala"


def actualizar_leds():
    """Enciende el LED correspondiente segun el estado del juego."""
    led_verde.off()
    led_amarillo.off()
    led_rojo.off()

    if estado_juego in ("sin sala", "espera", "terminada"):
        led_rojo.on()  # Rojo: sin sala, espera o terminada
    elif estado_juego == "pausada" or pausada:
        led_amarillo.on()  # Amarillo: pausa (manual o automatica)
    elif estado_juego in ("cuenta", "jugando"):
        led_verde.on()  # Verde: juego activo
    else:
        led_rojo.on()  # Rojo: estado desconocido o error


def main():
    """Bucle principal: Wi-Fi, botones, consulta servidor, LEDs."""
    global reconexion

    init_hardware()
    conectar_wifi()

    while True:
        # Sin Wi-Fi no se puede consultar ni controlar el juego
        if not wlan.isconnected():
            ahora = time.ticks_ms()
            if time.ticks_diff(ahora, reconexion) > 10000:
                reconexion = ahora
                wlan.connect(RED, CLAVE)
                mostrar_mensaje("Sin Wi-Fi")
            estado_juego = "sin sala"
            actualizar_leds()
            time.sleep_ms(50)
            continue

        manejar_botones()  # Lee botones y envia comandos HTTP
        consultar_servidor()  # Consulta estado y puntajes
        actualizar_leds()  # Enciende LED segun el estado
        time.sleep_ms(50)


if __name__ == "__main__":
    main()
