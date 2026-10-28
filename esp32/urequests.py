# urequests.py - Cliente HTTP minimo para MicroPython
# Soporta GET y POST sobre HTTP (no HTTPS).
# Pensado para reemplazar al modulo urequests si no esta incluido en el firmware.

import socket


class Response:
    """Respuesta HTTP simple con .text, .json(), .status_code y .close()."""

    def __init__(self, status_code, body, headers):
        self.status_code = status_code
        self.text = body.decode("utf-8", "ignore") if isinstance(body, bytes) else str(body)
        self.headers = headers

    def json(self):
        import json
        return json.loads(self.text)

    def close(self):
        pass


def _dechunk(data):
    """Decodifica cuerpo con transfer-encoding: chunked."""
    result = bytearray()
    i = 0
    while i < len(data):
        j = data.find(b"\r\n", i)
        if j < 0:
            break
        size_str = data[i:j].split(b";")[0].strip()
        try:
            size = int(size_str, 16)
        except ValueError:
            break
        if size == 0:
            break
        i = j + 2
        result += data[i : i + size]
        i += size + 2
    return bytes(result)


def _request(method, url, data=None, timeout=5):
    """Ejecuta una peticion HTTP y devuelve un objeto Response."""
    # Quitar protocolo
    if url.startswith("http://"):
        url = url[7:]
    elif url.startswith("https://"):
        raise ValueError("HTTPS no soportado")

    # Separar host:puerto y ruta
    if "/" in url:
        host_port, path = url.split("/", 1)
        path = "/" + path
    else:
        host_port = url
        path = "/"

    # Parsear host y puerto
    if ":" in host_port:
        host, port_s = host_port.rsplit(":", 1)
        port = int(port_s)
    else:
        host = host_port
        port = 80

    # Construir peticion
    req = "{} {} HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n".format(
        method, path, host_port
    )
    if data is not None:
        if isinstance(data, str):
            data = data.encode("utf-8")
        req += "Content-Length: {}\r\n".format(len(data))
    req += "\r\n"

    # Conectar y enviar
    sock = socket.socket()
    sock.settimeout(timeout)
    try:
        addr = socket.getaddrinfo(host, port)[0][-1]
        sock.connect(addr)
        sock.send(req.encode("utf-8"))
        if data is not None:
            sock.send(data)

        # Leer respuesta completa
        response = b""
        while True:
            chunk = sock.recv(1024)
            if not chunk:
                break
            response += chunk
    finally:
        sock.close()

    # Separar cabeceras y cuerpo
    sep = b"\r\n\r\n"
    idx = response.find(sep)
    if idx < 0:
        sep = b"\n\n"
        idx = response.find(sep)
    if idx < 0:
        raise ValueError("Respuesta HTTP invalida")

    headers_raw = response[:idx].decode("utf-8", "ignore")
    body = response[idx + len(sep) :]

    # Decodificar chunked si corresponde
    if "chunked" in headers_raw.lower():
        body = _dechunk(body)

    # Extraer codigo de estado
    status_line = headers_raw.split("\r\n")[0]
    status_code = int(status_line.split(" ")[1])

    return Response(status_code, body, headers_raw)


def get(url, **kw):
    """HTTP GET. kw['timeout'] en segundos (default 5)."""
    return _request("GET", url, timeout=kw.get("timeout", 5))


def post(url, data="", **kw):
    """HTTP POST. kw['timeout'] en segundos (default 5)."""
    return _request("POST", url, data=data, timeout=kw.get("timeout", 5))
