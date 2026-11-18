#!/usr/bin/env python3
"""Lista las resenas etiquetadas a mano donde el lexico del proyecto NO coincide con la etiqueta manual,
con el texto completo, para revisarlas a ojo (p. ej. buscar ironia, sarcasmo, mezcla de bueno y malo).
No mide ironia: solo junta los casos para que una persona los lea.

Uso:  .venv/bin/python -I src/desacuerdos_lexico.py [--hoja HOJA.xlsx ...] [--salida data/desacuerdos_lexico.md]
"""
import argparse, importlib.util, json, sys
from collections import defaultdict
from pathlib import Path

SRC = Path(__file__).resolve().parent
DATA = SRC.parent / 'data'
spec = importlib.util.spec_from_file_location('acierto_sentimiento', SRC / 'acierto_sentimiento.py')
ac = importlib.util.module_from_spec(spec); sys.modules['acierto_sentimiento'] = ac; spec.loader.exec_module(ac)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--hoja', nargs='+', default=[str(DATA / 'etiquetado_manual_100.xlsx')])
    ap.add_argument('--salida', default=str(DATA / 'desacuerdos_lexico.md'))
    a = ap.parse_args()
    filas, pend = ac.leer_hojas(a.hoja)
    if pend:
        raise SystemExit(f'Faltan {len(pend)} resenas sin sentimiento_manual valido.')
    d = json.loads((DATA / 'lexico_cliente_v4.json').read_text(encoding='utf-8'))
    lex = {**{x: 2 for x in d['positivas']}, **{x: -2 for x in d['negativas']}}
    grupos = defaultdict(list)
    for r in filas:
        p = ac.lx.puntaje(r['titulo'] + '. ' + r['texto'], lex)
        lect = ac.lectura_lexico(p)
        if lect != r['manual']:
            grupos[(r['manual'], lect)].append((r, p))
    total = sum(len(v) for v in grupos.values())
    out = [f'# Resenas donde el lexico no coincide con tu etiqueta ({total} de {len(filas)})', '',
           'Lee cada una y anota si hay ironia, sarcasmo, mezcla de bueno y malo u otra razon. Solo es una lista: no mide nada.', '']
    out += ['| Tu etiqueta -> lo que leyo el lexico | casos |', '|---|---|']
    out += [f'| {m} -> {l} | {len(v)} |' for (m, l), v in sorted(grupos.items(), key=lambda kv: -len(kv[1]))]
    for (m, l), v in sorted(grupos.items(), key=lambda kv: -len(kv[1])):
        out += ['', f'## Tu etiqueta: {m}  |  Lexico: {l}  ({len(v)})']
        for r, p in v:
            out += ['', f"**{r['id']}** (puntaje del lexico: {p:+.1f}) - {r['titulo']}", '', '> ' + r['texto'].replace('\n', '\n> ')]
    Path(a.salida).write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(f'{total} desacuerdos de {len(filas)} -> {a.salida}')
    for (m, l), v in sorted(grupos.items(), key=lambda kv: -len(kv[1])):
        print(f'  {m} -> {l}: {len(v)}')


if __name__ == '__main__':
    main()
