#!/usr/bin/env python3
"""Base local de reseñas. Etiquetado C2 en construir_diccionario.py; sin bots.

python3 base_resenas.py [--db RUTA] init|importar RUTA.json [--asin ASIN]|resumen|exportar-json
Parseadores equivalentes a resenas_amazon_excel.py, separados aquí porque aquel
inicializa analizadores y requiere dependencias de Excel al importarlo.
"""
import argparse
from datetime import datetime, timezone, date
import json
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / 'data/resenas.db'
MESES = dict(zip('enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre'.split(), range(1, 13)))
MONTHS = dict(zip('january february march april may june july august september october november december'.split(), range(1, 13)))
SCHEMA = '''
CREATE TABLE IF NOT EXISTS resenas (
 id TEXT PRIMARY KEY, asin TEXT, nombre TEXT, estrellas REAL, fecha TEXT,
 pais TEXT, titulo TEXT, texto TEXT, verificada INTEGER, util INTEGER,
 variante TEXT, fotos INTEGER, perfil TEXT, enlace TEXT, fuente TEXT, importada_en TEXT);
CREATE TABLE IF NOT EXISTS etiquetas (
 id_resena TEXT REFERENCES resenas(id), tipo TEXT, valor TEXT, fuente TEXT,
 version_dicc TEXT, PRIMARY KEY(id_resena,tipo,valor,version_dicc));
CREATE TABLE IF NOT EXISTS diccionarios (version TEXT PRIMARY KEY, creada_en TEXT, notas TEXT);
CREATE TABLE IF NOT EXISTS ejecuciones_bot (
 id INTEGER PRIMARY KEY, inicio TEXT, fin TEXT, estado TEXT, nuevas INTEGER, detalle TEXT);
'''


def parsear_fecha(s):
    m = re.search(r'en (.+?) el (\d{1,2}) de (\w+) de (\d{4})', s)
    if m and m[3].lower() in MESES:
        return date(int(m[4]), MESES[m[3].lower()], int(m[2])).isoformat(), m[1]
    m = re.search(r'in (?:the )?(.+?) on (\w+) (\d{1,2}), (\d{4})', s)
    if m and m[2].lower() in MONTHS:
        return date(int(m[4]), MONTHS[m[2].lower()], int(m[3])).isoformat(), m[1]
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
        return date.fromisoformat(s).isoformat(), ''
    return '', ''


def votos(s):
    m = re.search(r'(\d[\d,]*)', str(s or ''))
    if m:
        return int(m[1].replace(',', ''))
    return 1 if re.search(r'\b(una|one) (persona|person)', str(s), re.I) else 0


def normalizar(r, key, fuente, asin=None):
    rid = r.get('id', key)
    if not isinstance(rid, str) or not rid.strip() or (key is not None and key != rid):
        raise ValueError(f'ID ausente o inconsistente: {key!r}')
    fecha, pais = parsear_fecha(str(r.get('fecha') or ''))
    estrella = re.match(r'[\d.]+', str(r.get('estrellas', '')))
    estrella = float(estrella[0]) if estrella else None
    if estrella is not None and not 1 <= estrella <= 5:
        raise ValueError(f'Estrellas fuera de rango: {rid}')
    verificada = r.get('verificada', False)
    if isinstance(verificada, str):
        verificada = verificada.lower().strip() in ('true', '1', 'si', 'sí', 'yes')
    fotos = r.get('fotos', 0) or 0
    fotos = len(fotos) if isinstance(fotos, list) else int(fotos)
    return (rid, r.get('asin') or asin or 'B0D4MPKGN6', r.get('nombre', ''), estrella,
            fecha, r.get('pais') or pais, r.get('titulo', ''), r.get('texto', ''),
            int(bool(verificada)), votos(r.get('util', '')), r.get('variante', ''),
            fotos, r.get('perfil', ''), r.get('enlace') or
            f'https://www.amazon.com/gp/customer-reviews/{rid}',
            r.get('fuente') or fuente, datetime.now(timezone.utc).isoformat())


def importar(conn, ruta, asin=None):
    datos = json.loads(ruta.read_text(encoding='utf-8'))
    if not isinstance(datos, (dict, list)):
        raise ValueError('Se esperaba un objeto por ID o una lista de reseñas')
    items = datos.items() if isinstance(datos, dict) else ((None, r) for r in datos)
    filas = [normalizar(r, k, str(ruta.resolve()), asin) for k, r in items]
    if len({r[0] for r in filas}) != len(filas):
        raise ValueError('IDs repetidos en la entrada')
    # INSERT OR IGNORE conserva importada_en y etiquetas en reimportaciones.
    before = conn.total_changes
    with conn:
        conn.executemany('INSERT OR IGNORE INTO resenas VALUES (' + ','.join('?' * 16) + ')', filas)
    nuevas = conn.total_changes - before
    print(f'Importadas: {nuevas}; existentes: {len(filas) - nuevas}; entrada: {len(filas)}')


def resumen(conn):
    print(f'Total reseñas: {conn.execute("SELECT COUNT(*) FROM resenas").fetchone()[0]}')
    for label, campo in [('Por estrella', 'estrellas'), ('Por variante', 'variante')]:
        print(label + ':')
        for valor, n in conn.execute(f'SELECT {campo}, COUNT(*) FROM resenas GROUP BY {campo} ORDER BY {campo}'):
            print(f'  {valor if valor is not None else "sin dato"}: {n}')

    if conn.execute("SELECT 1 FROM diccionarios WHERE version='propio_v1'").fetchone():
        print('Genero estimado (propio_v1):')
        for value, n in conn.execute("SELECT valor,COUNT(*) FROM etiquetas WHERE tipo='genero' AND version_dicc='propio_v1' GROUP BY valor ORDER BY valor"):
            print(f'  {value}: {n}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    sub = parser.add_subparsers(dest='comando', required=True)
    sub.add_parser('init')
    imp = sub.add_parser('importar'); imp.add_argument('ruta', type=Path)
    imp.add_argument('--asin', help='ASIN para reseñas sin campo asin (por defecto, el bundle B0D4MPKGN6)')
    sub.add_parser('resumen')
    exp = sub.add_parser('exportar-json'); exp.add_argument('salida', type=Path, nargs='?')
    args = parser.parse_args()
    args.db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.db) as conn:
        conn.execute('PRAGMA foreign_keys=ON')
        conn.executescript(SCHEMA)
        if args.comando == 'init':
            print(f'Base inicializada: {args.db}')
        elif args.comando == 'importar':
            importar(conn, args.ruta, args.asin)
        elif args.comando == 'resumen':
            resumen(conn)
        else:
            conn.row_factory = sqlite3.Row
            datos = {r['id']: dict(r) for r in conn.execute('SELECT * FROM resenas ORDER BY id')}
            contenido = json.dumps(datos, ensure_ascii=False, indent=2) + '\n'
            if args.salida:
                if args.salida.resolve() == args.db.resolve():
                    parser.error('La salida no puede reemplazar la base')
                args.salida.write_text(contenido, encoding='utf-8')
            else:
                print(contenido, end='')


if __name__ == '__main__':
    main()
