#!/usr/bin/env python3
"""Diccionario palabra->lema inglés; una inferencia por palabra distinta.

Uso (también desde otro directorio):
  .venv/bin/python -I /ruta/lematizar_resenas.py
Requiere spaCy y en_core_web_sm. No modifica el diccionario original.
Los lemas aislados carecen de contexto: revisar ambigüedades y erratas.
"""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / 'data/reviews_bundle_soursop_bitters_v4.xlsx'
SALIDA = ROOT / 'data/lemas_cliente_v4.json'


def cargar_resenas(path):
    """Importa por ruta sin depender de sys.path, compatible con python -I."""
    spec = importlib.util.spec_from_file_location(
        'diccionario_cliente', Path(__file__).with_name('diccionario_cliente.py'))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo.cargar(path)


def contar_palabras(resenas):
    # Mismo criterio de palabras de separan() en el diccionario del cliente.
    frecuencias = Counter()
    for resena in resenas:
        texto = (resena['titulo'] + ' ' + resena['texto']).lower().replace('’', "'")
        frecuencias.update(p for w in re.findall(r"[a-z']+", texto)
                           if (p := w.strip("'")))
    return frecuencias


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xlsx', type=Path, default=XLSX)
    parser.add_argument('--salida', type=Path, default=SALIDA)
    args = parser.parse_args()
    import spacy
    from spacy.tokens import Doc

    resenas = cargar_resenas(args.xlsx)
    frecuencias = contar_palabras(resenas)
    nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])
    palabras = sorted(frecuencias)
    # Doc de un solo token conserva exactamente la clave (incluidas contracciones).
    # pipe recibe cada palabra única una sola vez, nunca cada aparición.
    docs = nlp.pipe((Doc(nlp.vocab, words=[p]) for p in palabras), batch_size=256)
    lemas = {p: doc[0].lemma_.lower() for p, doc in zip(palabras, docs)}
    esperados = {'bloated': {'bloat'}, 'bloating': {'bloat'},
                 'energized': {'energize', 'energise'}}
    for palabra, validos in esperados.items():
        if palabra not in lemas or lemas[palabra] not in validos:
            print(f'AVISO: {palabra} -> {lemas.get(palabra)!r} (lema sin contexto)')
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(lemas, ensure_ascii=False, indent=2) + '\n',
                           encoding='utf-8')
    print(f'{len(resenas)} reseñas; {sum(frecuencias.values())} palabras; '
          f'{len(lemas)} palabras distintas. spaCy {spacy.__version__}; '
          f'modelo {nlp.meta["version"]}.\nSalida: {args.salida}')
    for palabra in esperados:
        print(f'{palabra} -> {lemas[palabra]}')
    cuentas = Counter()
    for palabra, n in frecuencias.items():
        cuentas[lemas[palabra]] += n
    print('10 lemas menos frecuentes (apariciones; empates alfabéticos):')
    for lema, n in sorted(cuentas.items(), key=lambda x: (x[1], x[0]))[:10]:
        print(f'  {lema}: {n}')


if __name__ == '__main__':
    main()
