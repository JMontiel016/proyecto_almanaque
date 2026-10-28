# ssd1306.py - Driver MicroPython para pantalla OLED SSD1306 (I2C)
# Basado en el driver oficial de MicroPython.
# Funciones disponibles:
#   oled.fill(col)             - limpiar/llenar pantalla (0=negro, 1=blanco)
#   oled.text(string, x, y, col=1) - dibujar texto (8x8 pixeles, sin tildes)
#   oled.pixel(x, y, col)      - dibujar un pixel
#   oled.line(x1, y1, x2, y2, col)  - dibujar linea
#   oled.rect(x, y, w, h, col)     - rectangulo sin relleno
#   oled.fill_rect(x, y, w, h, col) - rectangulo relleno
#   oled.scroll(dx, dy)       - desplazar contenido
#   oled.show()                - actualizar pantalla con el buffer
#   oled.contrast(valor)       - ajustar contraste (0-255)
#   oled.invert(invert)        - invertir colores (True/False)
#   oled.poweroff()            - apagar pantalla
#   oled.poweron()             - encender pantalla

from micropython import const
import framebuf

# Registros del SSD1306
SET_CONTRAST = const(0x81)
SET_ENTIRE_ON = const(0xA4)
SET_NORM_INV = const(0xA6)
SET_DISP = const(0xAE)
SET_MEM_ADDR = const(0x20)
SET_COL_ADDR = const(0x21)
SET_PAGE_ADDR = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP = const(0xA0)
SET_MUX_RATIO = const(0xA8)
SET_COM_OUT_DIR = const(0xC0)
SET_DISP_OFFSET = const(0xD3)
SET_COM_PIN_CFG = const(0xDA)
SET_DISP_CLK_DIV = const(0xD5)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_CHARGE_PUMP = const(0x8D)


class SSD1306(framebuf.FrameBuffer):
    """Clase base para SSD1306 (no instanciar directamente)."""

    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        """Secuencia de inicializacion del SSD1306."""
        for cmd in (
            SET_DISP,            # Pantalla apagada
            SET_MEM_ADDR, 0x00,  # Direccionamiento horizontal
            SET_DISP_START_LINE,  # Linea de inicio 0
            SET_SEG_REMAP | 0x01,  # Columna 127 mapeada a SEG0
            SET_MUX_RATIO, self.height - 1,  # Ratio MUX
            SET_COM_OUT_DIR | 0x08,  # Direccion COM remapeada
            SET_DISP_OFFSET, 0x00,  # Offset 0
            SET_COM_PIN_CFG,
            0x02 if self.height == 32 else 0x12,  # Configuracion pines COM
            SET_DISP_CLK_DIV, 0x80,  # Divisor de reloj
            SET_PRECHARGE,
            0x22 if self.external_vcc else 0xF1,  # Periodo pre-carga
            SET_VCOM_DESEL, 0x30,  # Nivel VCOMH
            SET_CONTRAST, 0xFF,  # Contraste maximo
            SET_ENTIRE_ON,       # Pantalla desde RAM
            SET_NORM_INV,        # Display normal (no invertido)
            SET_CHARGE_PUMP,
            0x10 if self.external_vcc else 0x14,  # Bomba de carga
            SET_DISP | 0x01,     # Pantalla encendida
        ):
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(SET_DISP)

    def poweron(self):
        self.write_cmd(SET_DISP | 0x01)

    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def show(self):
        """Envia el buffer a la pantalla."""
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            x0 = 32
            x1 = 95
        elif self.width == 96:
            x0 = 16
            x1 = 111
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_buf(self.buffer)


class SSD1306_I2C(SSD1306):
    """Driver SSD1306 por bus I2C."""

    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.write_list = [b"\x40", None]  # Co=0, D/C#=1
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.temp[0] = 0x80  # Co=1, D/C#=0
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_buf(self, buf):
        self.write_list[1] = buf
        self.i2c.writevto(self.addr, self.write_list)
