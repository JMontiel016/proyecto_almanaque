"""Juego individual: salud HTTP y cámara/control por WebSocket, sin salas ni QR."""
import asyncio
from contextlib import suppress
import json
import logging
from pathlib import Path
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from buzon import Buzon
from motor import Juego, Jugador

VERSION = '0.6.0'
app = FastAPI(title='Zunpi individual')
# Una cámara activa evita multiplicar modelos y competir por CPU.
ocupado = False

def crear_detector():
    from seguimiento import Seguimiento
    return Seguimiento()

@app.get('/salud')
async def salud():
    return {'juego':'Zunpi','version':VERSION,
            'modelo':(Path(__file__).parent/'modelos/pose_landmarker_lite.task').is_file(),
            'modo':'individual','ocupado':ocupado}

@app.websocket('/conexion')
async def conectar(websocket: WebSocket):
    global ocupado
    await websocket.accept()
    if ocupado:
        await websocket.send_json({'tipo':'error','mensaje':'Ya hay un celular jugando. Cerrá esa partida antes de conectar otro.'})
        await websocket.close(code=1008)
        return
    ocupado = True
    detector = None
    tareas = []
    juego = Juego()
    jugador = Jugador('local', 'Jugador')
    juego.jugadores['local'] = jugador
    buzon = Buzon()

    async def enviar():
        while True:
            await websocket.send_json(await buzon.get())

    async def animar():
        anterior = time.monotonic()
        difundir = anterior
        while True:
            await asyncio.sleep(1/30)
            ahora = time.monotonic()
            juego.avanzar(ahora-anterior, ahora)
            anterior = ahora
            if ahora-difundir >= .1:
                buzon.publicar(juego.publico())
                difundir = ahora

    try:
        saludo = await asyncio.wait_for(websocket.receive_json(), 10)
        nombre = str(saludo.get('nombre','Jugador')).strip()
        if not nombre or len(nombre) > 18:
            raise ValueError('El nombre debe tener entre 1 y 18 caracteres.')
        jugador.nombre = nombre
        await websocket.send_json({'tipo':'bienvenida','identificador':'local'})
        await websocket.send_json({'tipo':'preparando','mensaje':'Preparando cámara corporal…'})
        detector = await asyncio.to_thread(crear_detector)
        await websocket.send_json({'tipo':'detector_listo'})
        buzon.publicar(juego.publico())
        tareas = [asyncio.create_task(enviar()), asyncio.create_task(animar())]
        while True:
            paquete = await asyncio.wait_for(websocket.receive(), 25)
            if paquete['type'] == 'websocket.disconnect':
                break
            if paquete.get('bytes') is not None:
                datos = paquete['bytes']
                if len(datos) > 500000:
                    raise ValueError('Imagen demasiado grande. Usá la cámara en resolución media.')
                vision = await asyncio.to_thread(detector.procesar, datos)
                jugador.rastreado = vision['listo']
                jugador.ultima_camara = time.monotonic()
                jugador.agachado = bool(vision.get('agachado',False))
                if vision['salto']:
                    juego.saltar('local')
                buzon.publicar(vision)
            elif paquete.get('text'):
                mensaje = json.loads(paquete['text'])
                try:
                    if mensaje.get('accion') == 'iniciar':
                        juego.comenzar()
                    elif mensaje.get('accion') == 'pausar':
                        if juego.estado not in ('cuenta', 'jugando'):
                            raise ValueError('La partida no está en curso.')
                        juego.pausa_manual = not juego.pausa_manual
                    elif mensaje.get('accion') == 'calibrar':
                        detector.salto.reiniciar()
                        jugador.rastreado = jugador.agachado = False
                    else:
                        raise ValueError('Acción desconocida.')
                except ValueError as error:
                    buzon.publicar({'tipo':'error','mensaje':str(error)})
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    except Exception as error:
        logging.exception('Falló la partida individual')
        for tarea in tareas: tarea.cancel()
        for tarea in tareas:
            with suppress(asyncio.CancelledError, Exception): await tarea
        tareas = []
        with suppress(Exception):
            await websocket.send_json({'tipo':'error','mensaje':str(error)})
            await websocket.close(code=1008)
    finally:
        for tarea in tareas: tarea.cancel()
        for tarea in tareas:
            with suppress(asyncio.CancelledError, Exception): await tarea
        try:
            if detector is not None:
                await asyncio.to_thread(detector.cerrar)
        finally:
            ocupado = False
