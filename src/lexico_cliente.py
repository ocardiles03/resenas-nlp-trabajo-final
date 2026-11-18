#!/usr/bin/env python3
"""Balanza de palabras aprendida de las resenas (idea de la Clase 11, EAFIT), solo stdlib.
  aprender : entrena con 80 % (4-5 estrellas = positiva, 1-2 = negativa), califica con 20 % y guarda lexico_cliente_v4.json
  puntuar CSV [--col texto] : lee un CSV de comentarios sin estrellas (TikTok/IG) y escribe CSV_puntuado.csv
Uso: python3 lexico_cliente.py aprender | puntuar comentarios.csv [--col texto]
"""
import csv, importlib.util, json, random, re, sys
from collections import Counter, defaultdict
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
OUT = TOOLS.parent / 'data'
spec = importlib.util.spec_from_file_location('dc', TOOLS / 'diccionario_cliente.py')
dc = importlib.util.module_from_spec(spec); sys.modules['dc'] = dc; spec.loader.exec_module(dc)

VACIAS = set("the a an and or of to in on for with is was it this that i my me we you your as at be are have has had so from by they them its were been can will would could one if when then than also get got just very am do does did".split())
NEG = {'no', 'not', 'never', 'nor', 'neither', "don't", "doesn't", "didn't", "won't", "can't", "isn't", "wasn't", "wouldn't", 'dont', 'doesnt', 'didnt', 'cant'}
MIN_VECES, MIN_RES, VENTANA = 15, 10, 3


def palabras(t):
    return [x.strip("'") for x in re.findall(r"[a-z']+", t.lower().replace('’', "'"))]


def parejas(w):
    return [w[i] + ' ' + w[i + 1] for i in range(len(w) - 1) if w[i] not in VACIAS and w[i + 1] not in VACIAS]


def aprender(train, lemas=None):
    cp, cn, rs = Counter(), Counter(), defaultdict(set)
    for r in train:
        pos = r['estrellas'] >= 4
        w = palabras(r['titulo'] + ' ' + r['texto'])
        if lemas:
            w = [lemas.get(x, x) for x in w]
        it = [x for x in w if x not in VACIAS and len(x) > 2 and x not in NEG] + parejas(w)
        (cp if pos else cn).update(it)
        for x in set(it):
            rs[x].add(r['id'])
    tp, tn = sum(cp.values()), sum(cn.values())
    lex = {}
    for x in set(cp) | set(cn):
        if cp[x] + cn[x] < MIN_VECES or len(rs[x]) < MIN_RES:
            continue
        a, b = cp[x] / tp * 1e4, cn[x] / tn * 1e4
        pc = a / (a + b) * 100
        if pc >= 75: lex[x] = 2
        elif pc <= 25: lex[x] = -2
    return lex


def puntaje(texto, lex, lemas=None):
    w = palabras(texto)
    if lemas:
        w = [lemas.get(x, x) for x in w]
    s, quedan = 0, 0
    for x in w:
        if x in NEG:
            quedan = VENTANA; continue
        p = lex.get(x, 0)
        if quedan:
            if p: p, quedan = -p, 0
            else: quedan -= 1
        s += p
    for e in parejas(w):
        s += lex.get(e, 0)
    return s


def auc(y, s):
    pares = sorted(zip(s, y)); rank, i, sp = 0, 0, 0.0
    n = len(pares)
    while i < n:
        j = i
        while j < n and pares[j][0] == pares[i][0]: j += 1
        for k in range(i, j):
            if pares[k][1] == 1: sp += (i + j + 1) / 2
        i = j
    np_ = sum(y); nn = n - np_
    return (sp - np_ * (np_ + 1) / 2) / (np_ * nn)


def cmd_aprender():
    lemas = None
    lp = OUT / 'lemas_cliente_v4.json'
    if '--lemas' in sys.argv and lp.exists():
        lemas = json.loads(lp.read_text(encoding='utf-8'))
    rev = [r for r in dc.cargar(dc.XLSX) if r['estrellas'] != 3]
    random.Random(42).shuffle(rev)
    k = int(len(rev) * 0.8)
    train, test = rev[:k], rev[k:]
    y = [1 if r['estrellas'] >= 4 else 0 for r in test]
    base = [int(puntaje(r['titulo'] + ' ' + r['texto'], {}, lemas) > 0) for r in test]  # sin lexico: todo negativo (referencia)
    lex = aprender(train, lemas)
    s = [puntaje(r['titulo'] + ' ' + r['texto'], lex, lemas) for r in test]
    d = [int(v > 0) for v in s]
    vn = sum(1 for a, b in zip(y, d) if a == 0 and b == 0); fp = sum(1 for a, b in zip(y, d) if a == 0 and b == 1)
    fn = sum(1 for a, b in zip(y, d) if a == 1 and b == 0); vp = sum(1 for a, b in zip(y, d) if a == 1 and b == 1)
    m = {'train': len(train), 'test': len(test), 'positivas_test': sum(y), 'exactitud': round((vp + vn) / len(y), 3),
         'sensibilidad': round(vp / (vp + fn), 3), 'especificidad': round(vn / (vn + fp), 3),
         'precision': round(vp / max(vp + fp, 1), 3), 'auc': round(auc(y, s), 3), 'errores': fp + fn,
         'proporcion_positivas_test': round(sum(y) / len(y), 3), 'terminos': len(lex), 'lematizado': bool(lemas)}
    # lexico final: se reaprende con todas las resenas
    lex_all = aprender(rev, lemas)
    top = lambda sg: sorted([x for x, p in lex_all.items() if p == sg])
    (OUT / 'lexico_cliente_v4.json').write_text(json.dumps({'_meta': {'metricas_prueba_20pct': m, 'semilla': 42, 'reglas': f'>=75% en 4-5 estrellas: +2; <=25%: -2; min {MIN_VECES} apariciones en {MIN_RES} resenas; negacion ventana {VENTANA}'}, 'positivas': top(2), 'negativas': top(-2)}, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps(m, ensure_ascii=False, indent=1)); print('+2:', len(top(2)), '-2:', len(top(-2)))


def cmd_puntuar():
    ruta = Path(sys.argv[2]); col = sys.argv[sys.argv.index('--col') + 1] if '--col' in sys.argv else 'texto'
    d = json.loads((OUT / 'lexico_cliente_v4.json').read_text(encoding='utf-8'))
    lex = {**{x: 2 for x in d['positivas']}, **{x: -2 for x in d['negativas']}}
    rows = list(csv.DictReader(ruta.open(encoding='utf-8-sig')))
    for r in rows:
        r['puntaje'] = puntaje(r[col], lex); r['lectura'] = 'positiva' if r['puntaje'] > 0 else ('negativa' if r['puntaje'] < 0 else 'neutra')
    out = ruta.with_name(ruta.stem + '_puntuado.csv')
    with out.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(Counter(r['lectura'] for r in rows), '->', out)


if __name__ == '__main__':
    {'aprender': cmd_aprender, 'puntuar': cmd_puntuar}.get(sys.argv[1] if len(sys.argv) > 1 else '', lambda: print(__doc__))()
