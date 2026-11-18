#!/usr/bin/env python3
"""Base PREPARADA para el trabajo final: Excel v4 (original) -> data/base_preparada_resenas.csv.
Decisiones de preparacion (cada una queda contada en el notebook, seccion 2.1):
  - se descartan las filas sin ID, con ID repetido (se conserva la primera) o sin texto de resena;
  - se agregan: semestre (AAAA-S1/S2 desde la fecha), clase_estrellas (Positivo 4-5, Negativo 1-2, Tibia 3);
  - se QUITA la columna Reviewer (nombre de una persona): no hace falta para el analisis y es dato personal.
Uso: .venv/bin/python -I src/preparar_base.py
"""
import csv, importlib.util, sys
from pathlib import Path

from openpyxl import load_workbook

SRC = Path(__file__).resolve().parent
DATA = SRC.parent / 'data'
SALIDA = DATA / 'base_preparada_resenas.csv'
CAMPOS = ['id', 'fecha', 'semestre', 'estrellas', 'clase_estrellas', 'titulo', 'texto', 'compra_verificada', 'enlace']


def semestre(f):
    return f[:4] + ('-S1' if int(f[5:7]) <= 6 else '-S2')


def clase(e):
    return 'Positivo' if e >= 4 else ('Negativo' if e <= 2 else 'Tibia')


def preparar(xlsx):
    """Lee la hoja 'Reseñas' del Excel v4 y devuelve la lista de filas preparadas (dicts con CAMPOS)."""
    ws = load_workbook(xlsx, read_only=True)['Reseñas']
    filas = list(ws.iter_rows(values_only=True)); cab = filas[0]
    out, vistos = [], set()
    for v in filas[1:]:
        r = dict(zip(cab, v))
        if not r['ID reseña'] or r['ID reseña'] in vistos or not (r['Reseña'] or '').strip():
            continue
        vistos.add(r['ID reseña'])
        e = int(float(r['Estrellas']))
        out.append({'id': r['ID reseña'], 'fecha': r['Fecha'], 'semestre': semestre(r['Fecha']), 'estrellas': e,
                    'clase_estrellas': clase(e), 'titulo': (r['Título'] or '').strip(), 'texto': r['Reseña'].strip(),
                    'compra_verificada': r['Compra verificada'], 'enlace': r['Enlace']})
    return out


if __name__ == '__main__':
    spec = importlib.util.spec_from_file_location('dc', SRC / 'diccionario_cliente.py')
    dc = importlib.util.module_from_spec(spec); sys.modules['dc'] = dc; spec.loader.exec_module(dc)
    filas = preparar(dc.XLSX)
    with SALIDA.open('w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS); w.writeheader(); w.writerows(filas)
    print(f'{len(filas)} resenas -> {SALIDA}')
