#!/usr/bin/env python3
"""Diccionario del lenguaje del cliente (frases literales por categoria) desde el Excel de resenas.
Solo stdlib. Uso: python3 diccionario_cliente.py [XLSX] [SALIDA_DIR]
No toca los archivos de resenas_amazon_excel.py / construir_diccionario.py; solo lee el xlsx.
"""
import json, re, sys, zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / 'data/reviews_bundle_soursop_bitters_v4.xlsx'
OUT = ROOT / 'data'
M = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


def leer_hoja(path, nombre):
    z = zipfile.ZipFile(path)
    ss = []
    if 'xl/sharedStrings.xml' in z.namelist():
        ss = [''.join(t.text or '' for t in si.iter('{%s}t' % M))
              for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('{%s}si' % M)]
    rels = {r.get('Id'): r.get('Target') for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    for s in ET.fromstring(z.read('xl/workbook.xml')).find('{%s}sheets' % M):
        if s.get('name') != nombre:
            continue
        t = rels[s.get('{%s}id' % R)].lstrip('/')
        t = t if t.startswith('xl/') else 'xl/' + t
        rows = []
        for row in ET.fromstring(z.read(t)).iter('{%s}row' % M):
            r = []
            for c in row:
                letras = re.match(r'[A-Z]+', c.get('r')).group()
                i = 0
                for ch in letras:
                    i = i * 26 + ord(ch) - 64
                i -= 1
                r += [None] * (i + 1 - len(r))
                v = c.find('{%s}v' % M)
                if c.get('t') == 's' and v is not None:
                    r[i] = ss[int(v.text)]
                elif c.get('t') == 'inlineStr':
                    r[i] = ''.join(x.text or '' for x in c.iter('{%s}t' % M))
                else:
                    r[i] = v.text if v is not None else None
            rows.append(r)
        return rows
    raise SystemExit('hoja no encontrada: ' + nombre)


# categoria -> grupo -> {etiqueta: regex}. Textos en ingles (idioma del cliente).
L = {
 'dolor_sintoma': {
  'estrenimiento': r"constipat\w*|can'?t (?:go|poop)|hard stool|irregular|backed up",
  'hinchazon_gases': r"bloat\w*|gas(?:sy)?\b|flatulen\w*|fart\w*|distend\w*",
  'digestion_estomago': r"digest\w*|stomach|tummy|belly|gut\b|intestin\w*|colon|bowel|indigestion",
  'acidez_reflujo': r"acid reflux|heartburn|\breflux|\bgerd\b|acid\w*",
  'diarrea_nausea': r"diarrh\w*|nause\w*|vomit\w*|threw up|throw up|puk\w*|cramp\w*|upset stomach|stomach ache|loose stool",
  'dolor_inflamacion': r"inflam\w*|arthrit\w*|joint\w*|\bpain\w*|\bache\w*|headache|migraine|swell\w*",
  'azucar_presion': r"blood sugar|glucose|diabet\w*|a1c|blood pressure|cholesterol|hypertens\w*",
  'energia_fatiga': r"energy|energi[sz]\w*|fatigue\w*|tired\w*|lethargic|sluggish|exhaust\w*",
  'sueno_estres': r"\bsleep\w*|insomnia|anxiety|stress\w*|\bcalm\w*|relax\w*",
  'peso_apetito': r"weight|\blost? \d+ ?(?:lbs|pounds)|appetite|crav\w*|bellyfat|belly fat|\bslim\w*",
  'parasitos_detox': r"parasit\w*|worms?\b|detox\w*|cleans\w*|flush\w*|candida|toxin\w*|\bpurge\w*",
  'inmunidad': r"immun\w*|\bcold\b|\bflu\b|infection\w*|sick\b",
  'piel_cabello': r"\bskin\b|acne|eczema|psoria\w*|\bhair\b|\bnails?\b|rash\w*",
  'higado_rinon_tiroides': r"\bliver\b|kidney\w*|thyroid|hormon\w*|menopaus\w*",
  'cancer_enfermedad_grave': r"cancer\w*|tumou?r\w*|chemo\w*|\bcyst\w*|fibroid\w*",
 },
 'resultado': {
  'funciona_mejora': r"(?:it |this |really |definitely )?works?\b(?! for me\? no)|worked|helps?\b|helped|improv\w*|relief|relieve\w*|noticed (?:a )?(?:difference|change)|feel(?:ing)? (?:so much )?better|results?\b|effective|game ?changer|life ?saver|life changing",
  'sin_efecto': r"(?:did not|didn'?t|doesn'?t|does not|not|never|no) (?:\w+ ){0,2}(?:work\w*|help\w*|change|difference|effect\w*|results?)|waste of money|nothing happened|useless|no results?",
  'efecto_adverso': r"side effects?|allerg\w*|reaction|made me (?:sick|nauseous|ill|dizzy)|burn\w*|rash|hives|dizzy|migraine|hospital|er\b|diarrh\w*",
  'efecto_rapido_fuerte': r"within (?:minutes|an hour|hours|a day|days)|right away|immediately|next day|first (?:day|dose|time)|powerful|strong\b|kicked in|bathroom|\bpoop\w*|\bbowel movement\w*|\bBM\b",
  'recompra_recomienda': r"reorder\w*|re-order\w*|buy(?:ing)? again|order(?:ing)? again|repurchase\w*|will (?:buy|order|purchase)|recommend\w*|go-?to|staple|never (?:be )?without|keep (?:buying|ordering)|my second|third bottle",
 },
 'objecion_sabor': {
  'amargo': r"bitter(?!s\b)\w*|\bbite\b|harsh|sour\b",
  'sabor_malo_asco': r"nasty|disgust\w*|gross|awful|terrible|horrible|foul|yuck|vile|undrinkable|gag\w*|can'?t (?:stand|drink|swallow)|hard to (?:drink|swallow|take)|repuls\w*",
  'sabor_aceptable': r"taste (?:is |was )?(?:good|great|fine|ok|okay|nice|pleasant|not (?:bad|that bad))|not (?:that )?bad|tolerable|bearable|pleasant|delicious|yummy|love the taste|gets? used to|chaser|mix(?:ed|ing)? (?:it )?(?:with|in)|in (?:juice|water|tea)",
  'sabor_general': r"\btaste\w*|flavou?r\w*|aftertaste|smell\w*|odor|tast(?:es|ing)",
  'natural_de_hierbas': r"herb\w*|tinct\w*|natural|organic|ingredient\w*|botanical|alcohol|extract",
 },
 'objecion_precio': {
  'caro': r"expensive|overpriced|pricey|too much|costly|rip-?off|cost\w*",
  'buen_valor': r"worth (?:it|the|every|every penny)|good (?:price|value|deal)|great (?:price|value|deal)|bargain|affordable|cheap\w*|value",
  'precio_general': r"\bprice\w*|\$ ?\d+|\bpaid\b|\bpay\b|\bmoney\b|\bdeal\b|\bsale\b",
 },
 'objecion_envio_producto': {
  'envio_tardio': r"late\b|delay\w*|took (?:\w+ ){0,3}(?:weeks?|days)|never (?:came|arrived)|shipping|delivery|deliver\w*|arrived|package|packag\w*",
  'danado_derrame': r"leak\w*|broken|broke|spill\w*|damag\w*|crushed|cracked|open(?:ed)? when|soaked|melted",
  'sello_envase': r"seal\w*|tamper\w*|plastic|bottle\w*|\blid\b|cap\b|safety (?:seal|band)",
  'autenticidad_diluido': r"fake|counterfeit|authentic\w*|watered|diluted|different (?:than|from)|not the same|changed (?:the )?(?:formula|bottle|label)|formula|scam|real\b|expired|expir\w*",
 },
 'objecion_reembolso': {
  'reembolso_devolucion': r"refund\w*|return(?:ed|ing|s)?\b|money back|replace\w*|exchange|cancel\w*|reimburs\w*",
  'servicio_cliente': r"customer (?:service|support)|contact(?:ed)? (?:the )?(?:seller|company|amazon)|support|complain\w*|dispute",
 },
 'emocional': {
  'gratitud_amor': r"love\w*|thank\w*|grateful|blessed|blessing|amazing|wonderful|fantastic|excellent|awesome|happy|great\b",
  'sorpresa_asombro': r"surpris\w*|wow|shocked|can'?t believe|unbelievable|miracle|magic\w*|incredible|impress\w*",
  'alivio': r"relief|relieved|finally|at last|no more|so much better|a lot better|feel(?:ing)? (?:great|good|amazing|light|clean|lighter)|lighter|cleaner",
  'enojo_decepcion': r"disappoint\w*|upset|angry|furious|waste|regret\w*|worst|ripped off|never again|do not (?:buy|waste)|don'?t (?:buy|waste)|unhappy|frustrat\w*|horrible|terrible|awful",
  'miedo_duda_escepticismo': r"skeptic\w*|doubt\w*|nervous|afraid|worried|scared|hesitant|hesitat\w*|not sure|unsure|wasn'?t sure|iffy|didn'?t think|didn'?t expect|expect\w*|hope\w*|desperate|tried everything",
  'confianza_fe': r"trust\w*|swear|believe\w*|faith|honest\w*|legit|reliable|pray\w*|testimon\w*",
  'cambio_vida': r"life ?chang\w*|life ?sav\w*|saved my|game ?chang\w*|changed my life|new person|back to normal|my health",
 },
}
STOP = set('the a an and or of to in on for with is was it this that i my me we you your as at be are have has had but not so very just from by they them its were been can will would could one if when then than also get got take took taking'.split())


def oraciones(txt):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', txt) if s.strip()]


def cargar(path):
    rows = leer_hoja(path, 'Reseñas')
    h = rows[0]
    ix = {n: i for i, n in enumerate(h)}
    out, vistos = [], set()
    for r in rows[1:]:
        r = r + [None] * (len(h) - len(r))
        txt = ' '.join(x for x in [r[ix['Título']], r[ix['Reseña']]] if x).strip()
        if not r[ix['ID reseña']] or r[ix['ID reseña']] in vistos or not (r[ix['Reseña']] or '').strip():
            continue
        vistos.add(r[ix['ID reseña']])
        out.append({'id': r[ix['ID reseña']], 'estrellas': int(float(r[ix['Estrellas']])),
                    'genero': r[ix['Género (estimado)']] or 'No claro', 'titulo': r[ix['Título']] or '',
                    'texto': r[ix['Reseña']].strip(), 'fecha': r[ix['Fecha']], 'fuente': r[ix['Fuente']]})
    return out


# Palabras vacias en ingles SIN las de opinion/negacion (idea de la Clase 11: no, not, never, good, bad, better, worse se conservan).
VACIAS = set("the a an and or of to in on for with is was it this that i my me we you your as at be are have has had so from by they them its were been can will would could one if when then than also get got just very am do does did".split())


def separan(rev, min_veces=15, min_resenas=10):
    """Adaptado de comparar() de la Clase 11 (EAFIT): % de cada palabra/pareja en 4-5 estrellas frente a 1-2,
    normalizado por cada 10,000 palabras de cada grupo (el grupo positivo es mas largo). Cerca de 50 % no separa."""
    cp, cn = Counter(), Counter()
    rs = defaultdict(set)
    for r in rev:
        if r['estrellas'] == 3:
            continue
        pos = r['estrellas'] >= 4
        w = re.findall(r"[a-z']+", (r['titulo'] + ' ' + r['texto']).lower().replace('\u2019', "'"))
        w = [x.strip("'") for x in w]
        items = [x for x in w if x not in VACIAS and len(x) > 2]
        items += [' '.join(w[i:i + 2]) for i in range(len(w) - 1) if w[i] not in VACIAS and w[i + 1] not in VACIAS]
        (cp if pos else cn).update(items)
        for x in set(items):
            rs[x].add(r['id'])
    tp, tn = sum(cp.values()) or 1, sum(cn.values()) or 1
    filas = []
    for x in set(cp) | set(cn):
        n = cp[x] + cn[x]
        if n < min_veces or len(rs[x]) < min_resenas:
            continue
        a, b = cp[x] / tp * 1e4, cn[x] / tn * 1e4
        filas.append((x, cp[x], cn[x], round(a / (a + b) * 100, 1), len(rs[x])))
    filas.sort(key=lambda f: f[3])
    return filas


def main():
    xlsx = Path(sys.argv[1]) if len(sys.argv) > 1 else XLSX
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT
    rev = cargar(xlsx)
    comp = {c: {g: {k: re.compile(r'(?<![a-z0-9])(?:' + p + r')', re.I) for k, p in gs.items()}
                for g, gs in L[c].items()} for c in L} if False else None
    res = {}
    for cat, grupos in L.items():
        res[cat] = {}
        for g, pat in grupos.items():
            rx = re.compile(r"(?<![a-z0-9])(?:" + pat + r")", re.I)
            ids, est, gen, terms, citas = set(), Counter(), Counter(), Counter(), []
            for r in rev:
                for s in oraciones(r['titulo'] + '. ' + r['texto']):
                    ms = list(rx.finditer(s))
                    if not ms:
                        continue
                    if r['id'] not in ids:
                        ids.add(r['id'])
                        est[r['estrellas']] += 1
                        gen[r['genero']] += 1
                    for m in ms:
                        terms[m.group(0).lower().strip()] += 1
                    if 25 <= len(s) <= 260:
                        citas.append((len(ms), r['estrellas'], r['id'], r['genero'], s))
            citas.sort(key=lambda c: (-c[0], c[2]))
            # diversidad de estrellas: hasta 2 por estrella, 8 en total
            sel, cnt = [], Counter()
            for c in citas:
                if cnt[c[1]] < 2 and len(sel) < 8 and not any(c[2] == x[2] for x in sel):
                    sel.append(c); cnt[c[1]] += 1
            res[cat][g] = {'resenas': len(ids), 'por_estrellas': {str(k): est.get(k, 0) for k in (1, 2, 3, 4, 5)},
                           'por_genero': dict(gen), 'terminos_top': terms.most_common(12),
                           'citas': [{'id': c[2], 'estrellas': c[1], 'genero': c[3], 'texto': c[4]} for c in sel]}
    # n-gramas de 2-3 palabras (frases del cliente) por banda de estrellas
    ng = {}
    for banda, ok in {'1-2 estrellas': lambda e: e <= 2, '3 estrellas': lambda e: e == 3, '4-5 estrellas': lambda e: e >= 4}.items():
        c = Counter()
        for r in rev:
            if not ok(r['estrellas']):
                continue
            w = re.findall(r"[a-z']+", (r['titulo'] + ' ' + r['texto']).lower())
            seen = set()
            for n in (2, 3):
                for i in range(len(w) - n + 1):
                    g = w[i:i + n]
                    if g[0] in STOP or g[-1] in STOP or all(x in STOP for x in g):
                        continue
                    seen.add(' '.join(g))
            c.update(seen)
        ng[banda] = [(k, v) for k, v in c.most_common(40) if v >= 3]
    sep = separan(rev)
    tot = Counter(r['estrellas'] for r in rev)
    totg = Counter(r['genero'] for r in rev)
    meta = {'fuente': str(xlsx.relative_to(ROOT)) if xlsx.is_relative_to(ROOT) else str(xlsx), 'resenas': len(rev),
            'por_estrellas': {str(k): tot[k] for k in sorted(tot)}, 'por_genero_estimado': dict(totg),
            'nota': 'Genero estimado (nombre/texto), aproximado. Conteo = resenas distintas que mencionan el grupo. Coincidencias por regex: pueden incluir falsos positivos (p. ej. bitter como nombre del producto).'}
    out.mkdir(parents=True, exist_ok=True)
    (out / 'diccionario_cliente_v4.json').write_text(json.dumps({'_meta': meta, 'categorias': res, 'frases_por_banda': ng, 'palabras_que_separan': sep}, ensure_ascii=False, indent=1), encoding='utf-8')
    # markdown
    T = {'dolor_sintoma': 'Dolor / sintoma', 'resultado': 'Resultado', 'objecion_sabor': 'Objecion: sabor', 'objecion_precio': 'Objecion: precio',
         'objecion_envio_producto': 'Objecion: envio / envase / autenticidad', 'objecion_reembolso': 'Objecion: reembolso y servicio', 'emocional': 'Lenguaje emocional'}
    md = ['# Diccionario del lenguaje del cliente (Bundle Black Seed + Soursop Bitters, B0D4MPKGN6)', '',
          f"Fuente: `{meta['fuente']}` · {len(rev)} resenas con texto · estrellas {meta['por_estrellas']} · genero estimado {meta['por_genero_estimado']}.", '',
          'Uso interno (investigacion del cliente). Las frases de salud NO se copian tal cual a anuncios (claims). Genero = estimado por nombre/texto, aproximado. Un grupo cuenta resenas distintas; las citas son literales en ingles con ID de resena. Las calificaciones de solo estrella (~4,000) no tienen texto y no entran aqui.',
          'Regex por reglas: puede haber falsos positivos (p. ej. «bitter» en el nombre del producto, «gas» como palabra suelta). Las columnas E1-2/E3/E4-5 = estrellas; H/M/NC = Hombre/Mujer/No claro+unisex.', '']
    for cat, nom in T.items():
        md += [f'## {nom}', '', '| Grupo | Resenas | % | 1-2★ | 3★ | 4-5★ | H | M | NC | Palabras top |', '|---|---|---|---|---|---|---|---|---|---|']
        for g, d in res[cat].items():
            e = d['por_estrellas']; gg = d['por_genero']
            md.append(f"| {g} | {d['resenas']} | {100*d['resenas']/len(rev):.0f}% | {e['1']+e['2']} | {e['3']} | {e['4']+e['5']} | {gg.get('Hombre',0)} | {gg.get('Mujer',0)} | {len(rev) and d['resenas']-gg.get('Hombre',0)-gg.get('Mujer',0)} | {', '.join(f'{t} ({n})' for t,n in d['terminos_top'][:6])} |")
        md.append('')
        for g, d in res[cat].items():
            if not d['citas']:
                continue
            md.append(f'**{g}** — citas:')
            for c in d['citas'][:6]:
                md.append(f"- ({c['estrellas']}★, {c['genero']}, `{c['id']}`) «{c['texto']}»")
            md.append('')
    md += ['## Frases frecuentes (2-3 palabras) por banda de estrellas', '', '_Resenas distintas que contienen la frase (minimo 3)._', '']
    for b, lst in ng.items():
        md += [f'**{b}:** ' + '; '.join(f'{k} ({v})' for k, v in lst[:30]), '']
    md += ['## Palabras que separan elogio de queja (adaptado de la Clase 11, EAFIT)', '',
           '% de la palabra/pareja en resenas 4-5★ frente a 1-2★, normalizado por 10,000 palabras de cada grupo (50 % = no separa). Minimo 15 apariciones en 10 resenas. Sin lematizar. 3★ excluidas.', '',
           '**Hacia la queja (1-2★):** ' + '; '.join(f'{x} ({pc:.0f}%, {a}+/{b}-)' for x, a, b, pc, n in sep[:40]), '',
           '**Hacia el elogio (4-5★):** ' + '; '.join(f'{x} ({pc:.0f}%, {a}+/{b}-)' for x, a, b, pc, n in reversed(sep[-40:])), '']
    (out / 'diccionario_cliente_v4.md').write_text('\n'.join(md), encoding='utf-8')
    print('ok', len(rev), 'resenas ->', out / 'diccionario_cliente_v4.md')


if __name__ == '__main__':
    main()
