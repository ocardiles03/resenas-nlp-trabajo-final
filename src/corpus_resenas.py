#!/usr/bin/env python3
"""Carga las DOS bases de resenas del proyecto con el mismo formato (lista de dicts).

  bundle  : Excel v4 del bundle B0D4MPKGN6 (1271 resenas con texto). Base con la que se construyeron el lexico y el KNN.
  soursop : data/resenas_soursop_base_organizada.csv, producto B0CYV4FCJS (2524 resenas; las que no tienen texto se omiten).
Las dos bases no comparten ningun id. Cada resena: base, id, estrellas (int), titulo, texto, fecha (ISO AAAA-MM-DD), semestre.
"""
import csv, importlib.util, sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
DATA = SRC.parent / 'data'
SOURSOP_CSV = DATA / 'resenas_soursop_base_organizada.csv'


def semestre(fecha_iso):
    """'2025-03-14' -> '2025-S1' (ene-jun = S1, jul-dic = S2)."""
    return fecha_iso[:4] + ('-S1' if int(fecha_iso[5:7]) <= 6 else '-S2')


def cargar_bundle():
    """Base 1: reutiliza el lector del Excel v4 de diccionario_cliente.py."""
    spec = importlib.util.spec_from_file_location('diccionario_cliente', SRC / 'diccionario_cliente.py')
    dc = importlib.util.module_from_spec(spec); sys.modules['diccionario_cliente'] = dc; spec.loader.exec_module(dc)
    return [{'base': 'bundle', 'id': r['id'], 'estrellas': r['estrellas'], 'titulo': r['titulo'], 'texto': r['texto'],
             'fecha': r['fecha'], 'semestre': semestre(r['fecha'])} for r in dc.cargar(dc.XLSX) if r['fecha']]


def cargar_soursop():
    """Base 2: CSV ya organizado (fechas ISO y estrellas numericas). Se leen con el modulo csv porque hay saltos de linea en los textos."""
    with SOURSOP_CSV.open(encoding='utf-8-sig', newline='') as f:
        filas = list(csv.DictReader(f))
    return [{'base': 'soursop', 'id': r['ID'], 'estrellas': int(float(r['Estrellas'])), 'titulo': r['Titulo'].strip(), 'texto': r['Texto'].strip(),
             'fecha': r['Fecha'], 'semestre': semestre(r['Fecha'])} for r in filas if r['Texto'].strip() and r['Fecha']]


def cargar_todo():
    return cargar_bundle() + cargar_soursop()


if __name__ == '__main__':
    for b in (cargar_bundle(), cargar_soursop()):
        print(b[0]['base'], len(b), min(r['fecha'] for r in b), max(r['fecha'] for r in b))
