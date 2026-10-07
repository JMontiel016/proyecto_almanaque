"""Salas, cámara y ranking: ejecutar un solo worker para conservar salas en memoria."""
import asyncio  # Coordina rondas y conexiones sin bloquear la red.
from contextlib import asynccontextmanager  # Inicio y cierre del motor.
import json  # Mensajes de control.
import secrets  # Identificadores de conexión imposibles de predecir.
from pathlib import Path  # Modelo y diagnóstico portable.
import logging  # Errores con traceback en la terminal del servidor.
import time  # Vigencia del seguimiento.
import socket  # Identifica la interfaz LAN sin enviar paquetes.
import ipaddress  # Excluye loopback y direcciones no IPv4.
from fastapi import FastAPI, WebSocket, WebSocketDisconnect  # API HTTP/WebSocket.
from buzon import Buzon  # Separa el último estado de las respuestas de cámara.
from motor import Jugador, Sala  # Reglas independientes de la red.
from almacenamiento import ranking, registrar  # Ranking durable.

salas = {}  # Salas efímeras; se eliminan al quedar vacías.
guardados = set()  # Escrituras pendientes: se completan al apagar normalmente.
detector_precargado = False  # Estado real de carga del modelo.

def crear_detector():
    from seguimiento import Seguimiento  # Importación pesada dentro del hilo, no bloquea salud/salas.
    return Seguimiento()

async def precargar():
    global detector_precargado
    try:
        preparado = await asyncio.to_thread(crear_detector)  # Una precarga compartida en segundo plano.
        detector_precargado = True
        preparado.cerrar()
    except Exception:
        logging.exception("No se pudo precargar el modelo: revisar instalación/modelo")

conexiones = {}  # Identificador público -> canal de salida acotado.

async def publicar(identificador, mensaje):
    cola = conexiones.get(identificador)  # Solo jugadores conectados.
    if cola is not None:
        cola.publicar(mensaje)  # Acuse de cámara protegido; estado anterior reemplazado.

async def guardar_resultado(identidad, nombre, puntos):
    try:
        await asyncio.to_thread(registrar, identidad, nombre, puntos)
    except Exception:
        logging.exception("No se pudo guardar el récord")

async def motor_global():
    anterior, difundir = time.monotonic(), 0.0  # Relojes de física y red separados.
    while True:
        await asyncio.sleep(1/30)  # Física a 30 pasos por segundo.
        ahora = time.monotonic()  # Hora monotónica.
        dt, anterior = ahora-anterior, ahora  # Paso real.
        for sala in list(salas.values()):
            if not sala.jugadores and getattr(sala,'vence',ahora+1) < ahora:
                salas.pop(sala.codigo,None)  # Reservas sin jugadores caducan a los diez minutos.
                continue
            for jugador in sala.avanzar(dt, ahora):
                if not jugador.guardado:
                    escritura = asyncio.create_task(guardar_resultado(jugador.identificador_privado, jugador.nombre, jugador.puntos))  # SQLite fuera del hilo de física.
                    guardados.add(escritura)
                    escritura.add_done_callback(guardados.discard)
                    jugador.guardado = True  # No duplica la escritura.
            if ahora - difundir >= .1:
                estado = sala.publico()  # Envía 10 estados/s; Flutter interpola.
                for identificador in list(sala.jugadores):
                    await publicar(identificador, estado)  # Cámara no bloquea estado.
        if ahora - difundir >= .1:
            difundir = ahora  # Reinicia frecuencia común.

@asynccontextmanager
async def ciclo(app):
    tarea = asyncio.create_task(motor_global())  # Una tarea para todas las salas.
    calentamiento = asyncio.create_task(precargar())  # HTTP responde sin esperar a MediaPipe.
    yield  # Sirve solicitudes.
    calentamiento.cancel()
    try:
        await calentamiento
    except asyncio.CancelledError:
        pass
    tarea.cancel()  # Detiene física al apagar.
    try:
        await tarea
    except asyncio.CancelledError:
        pass  # Cierre normal.

    if guardados:
        await asyncio.gather(*list(guardados), return_exceptions=True)  # Conserva resultados al detener con Ctrl+C.

app = FastAPI(title='Zunpi', lifespan=ciclo)  # Documentación en /docs.

@app.get('/salud')
async def salud():
    return {'estado':'disponible','juego':'Zunpi','version':'0.4.0', 'detector_precargado':detector_precargado, 'modelo':(Path(__file__).parent/'modelos/pose_landmarker_lite.task').is_file()}  # Diagnóstico de conexión.

@app.get('/')
async def inicio():
    return await salud()  # Abrir el navegador ya no devuelve 404.

def direcciones_red():
    direcciones = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as ruta:
            ruta.connect(('192.0.2.1', 9))  # Solo consulta la ruta local; no send/sendto.
            direcciones.append(ruta.getsockname()[0])
    except OSError:
        pass
    try:
        direcciones.extend(socket.gethostbyname_ex(socket.gethostname())[2])
    except OSError:
        pass
    return list(dict.fromkeys(ip for ip in direcciones
        if ipaddress.ip_address(ip).version == 4 and not ipaddress.ip_address(ip).is_loopback
        and not ipaddress.ip_address(ip).is_unspecified))

@app.get('/red')
async def red():
    return {'direcciones': await asyncio.to_thread(direcciones_red)}  # DNS fuera del bucle del juego.

@app.post('/salas')
async def reservar_sala(datos: dict):
    nombre = str(datos.get('nombre','')).strip()  # Reserva sin encender la cámara.
    if not 1 <= len(nombre) <= 18:
        return {'error':'Ingresá tu nombre antes de crear la sala.'}
    if len(salas) >= 6:
        return {'error':'Máximo de salas alcanzado. Esperá o cerrá una sala.'}
    codigo = secrets.token_hex(3).upper()
    while codigo in salas:
        codigo = secrets.token_hex(3).upper()
    sala = Sala(codigo,'')  # Primer conectado administrará, igual que en modo directo.
    sala.vence = time.monotonic()+600  # Diez minutos para ingresar antes de caducar.
    salas[codigo] = sala
    return {'sala':codigo,'juego':'Zunpi','version':'0.4.0'}  # El QR ya es válido antes de la inferencia.

@app.get('/ranking')
async def obtener_ranking():
    return await asyncio.to_thread(ranking)  # SQLite no bloquea cámara ni ticker.

@app.get('/oled/{codigo}')
async def obtener_oled(codigo: str):
    sala = salas.get(codigo.upper())  # Consulta de solo lectura para ESP32.
    if not sala:
        return {'estado':'sin sala','jugadores':[]}  # OLED no necesita iniciar sesión.
    jugadores = sorted(sala.jugadores.values(), key=lambda j:j.puntos, reverse=True)  # Orden por puntos.
    return {'estado':sala.estado,'jugadores':[{'nombre':j.nombre,'puntos':j.puntos} for j in jugadores]}

@app.websocket('/conexion')
async def conectar(websocket: WebSocket):
    await websocket.accept()  # Acepta handshake.
    sala, jugador, detector, tarea_salida = None, None, None, None  # Recursos por cliente.
    cola = Buzon()  # Evita memoria ilimitada por cliente lento.
    async def enviar():
        while True:
            await websocket.send_json(await cola.get())  # Único escritor WebSocket.
    try:
        saludo = await asyncio.wait_for(websocket.receive_json(), 15)  # No deja conexiones vacías.
        nombre = str(saludo.get('nombre','')).strip()  # Nombre ingresado en app.
        identidad = str(saludo.get('identidad',''))  # Identificador persistido en el celular.
        if not 1 <= len(nombre) <= 18 or not 20 <= len(identidad) <= 100:
            raise ValueError('Nombre de 1 a 18 caracteres e identidad válida requeridos.')
        if len(conexiones) >= 12:
            raise ValueError('Servidor completo: máximo 12 cámaras en este prototipo.')
        codigo = str(saludo.get('sala','')).strip().upper()  # Vacío crea una sala.
        identificador = secrets.token_hex(8)  # Identidad pública de esta conexión.
        if codigo:
            sala = salas.get(codigo)  # Unirse no crea salas inexistentes.
            if not sala:
                raise ValueError('La sala no existe o ya terminó su sesión.')
            if len(sala.jugadores) >= 4:
                raise ValueError('La sala ya tiene cuatro jugadores.')
            if sala.estado in ('cuenta','jugando'):
                raise ValueError('Esperá a que termine la ronda para ingresar.')
        else:
            if len(salas) >= 6:
                raise ValueError('Máximo de salas alcanzado.')
            codigo = secrets.token_hex(3).upper()  # Código QR de seis caracteres.
            while codigo in salas:
                codigo = secrets.token_hex(3).upper()  # Evita colisiones.
            sala = Sala(codigo, identificador)  # Primer conectado administra.
            salas[codigo] = sala
        if any(getattr(j,'identificador_privado','') == identidad for j in sala.jugadores.values()):
            raise ValueError('Este celular ya está conectado a la sala.')
        modelo = Path(__file__).parent/'modelos/pose_landmarker_lite.task'  # Valida antes de reservar sala.
        if not modelo.is_file():
            raise ValueError('Falta el modelo corporal en la computadora. Ejecutá: python descargar_modelo.py')

        jugador = Jugador(identificador, nombre)  # Estado de juego.
        jugador.identificador_privado = identidad  # No se comparte en estado público.
        if not sala.administrador:
            sala.administrador = identificador  # Primer conectado a una reserva.
        sala.jugadores[identificador] = jugador  # Registra participante.
        await websocket.send_json({'tipo':'bienvenida','identificador':identificador,'sala':codigo,'administrador':sala.administrador})  # Entrega identidad ANTES de inferencia y fuera de colas descartables.
        await websocket.send_json({'tipo':'preparando','mensaje':'Sala conectada. Cargando detector corporal Python…'})
        detector = await asyncio.to_thread(crear_detector)  # Modelo CPU independiente del canal de control.
        await websocket.send_json({'tipo':'detector_listo'})  # Cliente recién ahora abre captura.
        conexiones[identificador] = cola  # Ticker solo publica cuando el detector ya está cargado.
        tarea_salida = asyncio.create_task(enviar())  # Un escritor luego de inicialización.
        ultima_imagen = 0.0  # Limitador de frecuencia.
        while True:
            paquete = await asyncio.wait_for(websocket.receive(), 25)  # Desconecta si app se suspende.
            if paquete['type'] == 'websocket.disconnect':
                break  # Limpieza en finally.
            if paquete.get('bytes') is not None:
                datos = paquete['bytes']  # JPEG de cámara frontal.
                if len(datos) > 2000000:
                    raise ValueError('La imagen supera 2 MB. Cambiá la calidad de cámara a media.')
                if time.monotonic() - ultima_imagen < .1:
                    await publicar(identificador, {'tipo':'vision','mensaje':'Esperando cámara','listo':jugador.rastreado,'puntos':[]})
                    continue  # Máximo 10 inferencias/s por cámara.
                ultima_imagen = time.monotonic()  # Marca inicio.
                vision = await asyncio.to_thread(detector.procesar, datos)  # Python ejecuta inferencia.
                jugador.rastreado = vision['listo']  # Solo listo después de calibrar.
                jugador.ultima_camara = time.monotonic()  # Refresca vigencia.
                if vision['salto']:
                    sala.saltar(identificador)  # No acepta saltos enviados por Dart.
                await publicar(identificador, vision)  # Imagen anotada + evento.
            elif paquete.get('text'):
                mensaje = json.loads(paquete['text'])  # Comandos pequeños.
                try:
                    if mensaje.get('accion') == 'listo':
                        jugador.listo = not jugador.listo  # Cambia confirmación.
                    elif mensaje.get('accion') == 'iniciar':
                        sala.comenzar(identificador)  # Valida administrador.
                    elif mensaje.get('accion') == 'calibrar':
                        detector.salto.reiniciar()  # Se ejecuta entre imágenes, sin concurrencia.
                        jugador.rastreado = False  # Pausa hasta nueva calibración.
                except ValueError as error:
                    await publicar(identificador, {'tipo':'error','mensaje':str(error)})  # Error recuperable.
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass  # Cierre esperado por salida o suspensión.
    except Exception as error:
        logging.exception('Falló la sesión Zunpi')  # Diagnóstico completo, no deja cámara muda.
        if tarea_salida:
            tarea_salida.cancel()
            try:
                await tarea_salida
            except (asyncio.CancelledError, Exception):
                pass
            tarea_salida = None  # Evita dos escritores durante el error.
        try:
            await websocket.send_json({'tipo':'error','mensaje':str(error)})  # Error inicial/cámara.
            await websocket.close(code=1008)  # Fuerza que la app deje de esperar respuestas.
        except Exception:
            pass  # Si la conexión murió, igual libera recursos.
    finally:
        if tarea_salida:
            tarea_salida.cancel()  # Cancela cola de salida.
            try:
                await tarea_salida
            except (asyncio.CancelledError, Exception):
                pass
        if detector:
            await asyncio.to_thread(detector.cerrar)  # Libera modelo de esa persona.
        if sala and jugador:
            conexiones.pop(jugador.identificador, None)  # Elimina canal.
            sala.jugadores.pop(jugador.identificador, None)  # Retira jugador.
            if sala.jugadores:
                if sala.administrador == jugador.identificador:
                    sala.administrador = next(iter(sala.jugadores))  # Transfiere administración.
                if not any(j.vivo for j in sala.jugadores.values()) and sala.estado == 'jugando':
                    sala.estado = 'terminada'  # Desconexión del último sobreviviente.
            else:
                salas.pop(sala.codigo, None)  # Cierra sala vacía.
        elif sala and not sala.jugadores:
            salas.pop(sala.codigo, None)  # No conserva salas si falló el modelo.
