"""Ranking por nombre: mismo nombre normalizado comparte la mejor marca."""
import sqlite3  # Persistencia integrada.
from pathlib import Path  # Carpeta configurable.
import os  # Configuración de almacenamiento.
import unicodedata  # Normalización Unicode consistente.

RUTA = Path(os.environ.get('ZUNPI_DATOS', str(Path(__file__).parent / 'datos')))

def clave_nombre(nombre):
    return unicodedata.normalize('NFKC',' '.join(nombre.split())).casefold()  # Jaime/jaime y espacios equivalen; ñ se conserva.

def conexion():
    RUTA.mkdir(parents=True, exist_ok=True)
    base = sqlite3.connect(RUTA/'ranking.sqlite3')
    base.row_factory = sqlite3.Row
    base.execute('CREATE TABLE IF NOT EXISTS ranking_nombres (clave TEXT PRIMARY KEY, nombre TEXT NOT NULL, puntos INTEGER NOT NULL, fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')
    base.execute('CREATE TABLE IF NOT EXISTS migraciones (version TEXT PRIMARY KEY)')
    if not base.execute("SELECT 1 FROM migraciones WHERE version='nombres_v3'").fetchone():
        anterior = base.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ranking'").fetchone()  # Conserva tabla anterior intacta.
        if anterior:
            for fila in base.execute('SELECT nombre,puntos FROM ranking ORDER BY puntos ASC').fetchall():
                base.execute('INSERT INTO ranking_nombres(clave,nombre,puntos) VALUES(?,?,?) ON CONFLICT(clave) DO UPDATE SET nombre=CASE WHEN excluded.puntos>ranking_nombres.puntos THEN excluded.nombre ELSE ranking_nombres.nombre END,puntos=MAX(ranking_nombres.puntos,excluded.puntos)', (clave_nombre(fila['nombre']),fila['nombre'],fila['puntos']))
        base.execute("INSERT INTO migraciones VALUES('nombres_v3')")  # Migración una sola vez, no reimporta récords antiguos al consultar.
    base.commit()
    return base

def registrar(identificador, nombre, puntos):
    nombre = ' '.join(nombre.split())  # Conserva escritura visible, limpia espacios.
    with conexion() as base:
        base.execute('INSERT INTO ranking_nombres(clave,nombre,puntos) VALUES(?,?,?) ON CONFLICT(clave) DO UPDATE SET nombre=CASE WHEN excluded.puntos>ranking_nombres.puntos THEN excluded.nombre ELSE ranking_nombres.nombre END,puntos=MAX(ranking_nombres.puntos,excluded.puntos),fecha=CASE WHEN excluded.puntos>ranking_nombres.puntos THEN CURRENT_TIMESTAMP ELSE ranking_nombres.fecha END', (clave_nombre(nombre),nombre,puntos))
    base.close()  # Identificador mantenido solo por compatibilidad con el motor; el ranking usa nombre.

def ranking():
    with conexion() as base:
        filas = base.execute('SELECT nombre,puntos FROM ranking_nombres ORDER BY puntos DESC,fecha ASC LIMIT 50').fetchall()
    base.close()
    return [dict(fila) for fila in filas]
