"""Estudio ICP desde las reseñas de Amazon (3 productos). Solo lectura; sin red.

Une la base del bundle (resenas.db) con las reseñas nuevas del Soursop solo y del
Black Seed, mide quién escribe, qué dolor nombra, qué probó antes, qué le molesta,
dónde se enteró y cómo habla, y vuelca todo a un JSON para escribir los estudios.
Uso: python3 -I estudio_icp.py SALIDA.json
Regex por reglas: puede haber falsos positivos; genero es estimado por nombre.
"""
import json
import math
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from demografia_resenas import NOMBRES_US, APODOS

RAIZ = Path(__file__).resolve().parents[1] / 'data'
PRODUCTOS = {'B0D4MPKGN6': 'bundle', 'B0CYV4FCJS': 'soursop_solo', 'B0F2J18GFQ': 'blackseed_solo'}
MESES = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
         'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12}

TEMAS = {
    'hinchazon': r'bloat|gassy|\bgas\b|distend',
    'estrenimiento': r'constipat|backed up|can.t (go|poop)|hard stool|irregular|not (going|moving)|nothing (was )?mov',
    'digestion_general': r'digest|\bgut\b|stomach|bowel|belly|tummy|intestin',
    'energia': r'energ|sluggish|fatigue|tired|lethargic',
    'detox_limpieza': r'detox|cleans|flush|parasit|toxin',
    'peso_antojos': r'weight|appetite|craving|belly fat|slim|lost \d+',
    'inmunidad': r'immun|\bsick\b|\bcold\b|\bflu\b',
    'piel_pelo': r'\bskin\b|\bhair\b|nails|acne',
    'sueno_estres': r'sleep|stress|anxi|calm',
    'dolor_inflamacion': r'inflam|joint|arthrit|\bpain\b|swell',
    'azucar_presion': r'blood sugar|glucose|diabet|blood pressure|hypertens|cholesterol',
    'hormonas_edad': r'menopaus|perimenopaus|hormon|period\b|cycle|thyroid|fibroid|pcos',
    'cancer_grave': r'cancer|chemo|tumor|\bcirrhosis',
}
QUEJAS = {
    'sabor': r'(bad|awful|terrible|horrible|nasty|gross|vile|strong|foul|disgusting|worst|hard) (to (swallow|drink|take|stomach) )?(tast|flavor|smell)|tastes? (bad|awful|terrible|horrible|nasty|gross|like (crud|dirt|medicine|poison|death|a|mud|vomit))|(too|so|very|extremely|really|super) bitter|bitter(ness)?|disgust|nasty|gross|vile|yuck|gag|hard to (swallow|drink|take)|can.t (stand|stomach|drink)',
    'urgencia_calambres': r'cramp|urgen|diarrhea|runs\b|bathroom|toilet|loose|explosive|rush|nausea|threw up|vomit',
    'plastico_aguado': r'plastic|glass|watered|watery|diluted|thin\b|changed (the )?(formula|bottle)|used to be',
    'suscripcion_cobro': r'subscri|charged|refund|cancel|auto.?ship|recurring',
    'falso_envio': r'\bfake\b|counterfeit|not (the )?same|leak|broken|damaged|expired|tamper|opened|missing seal|wrong (item|product)|never (arrived|came)|not authentic|knock.?off|imitation|diluted|watered',
    'no_funciono': r"didn.t work|did not work|no (effect|results|change|difference)|nothing happen|waste|doesn.t work|not work|useless|no relief",
    'senna_laxante': r'senna|\bsen\b|laxative|stimulant|dependen|habit.forming',
    'precio': r'expensive|overpriced|pricey|too much money|price',
}
PROBO_ANTES = {
    'fibra': r'\bfiber\b|\bfibre\b|metamucil|psyllium|benefiber',
    'laxantes_otc': r'miralax|dulcolax|laxative|stool softener|colace|magnesium|mag citrate|senna tea|smooth move',
    'probioticos': r'probiotic|prebiotic|kombucha|kefir',
    'dieta_agua': r'drink(ing)? (more )?water|diet|eliminat|cut out|gluten|dairy',
    'doctor': r'doctor|physician|gastro|\bgi\b|colonoscop|specialist|dismiss|prescri|\bmd\b|pharmac',
    'remedios_naturales': r'bush tea|cerasee|herbal|natural|remed|apple cider|\bacv\b|castor|ginger|tea\b|aloe|prune',
    'tried_everything': r"tried (everything|so many|numerous|many|lots)|nothing (else )?(worked|helped)|everything (else|i)",
}
FUENTE = {
    'tiktok': r'tik.?tok',
    'instagram': r'instagram|\big\b|reel',
    'facebook': r'facebook|\bfb\b',
    'youtube': r'youtube|\byt\b',
    'anuncio': r'\bad\b|\bads\b|advert|commercial|influencer|saw (this|it|a video)',
    'recomendacion': r'recommend(ed)? (to me )?by|friend|my (sister|mom|mother|aunt|cousin|coworker|neighbor)|someone told|word of mouth|referred',
    'reseñas_previas': r'reviews? (convinced|made me)|read(ing)? the reviews|after reading',
}
IDENTIDAD = {
    'madre_abuela': r"\bmom\b|\bmother\b|grandma|grandmother|\bmama\b|as a mother|my kids|my children|my daughter|my son",
    'pareja': r"my husband|my hubby|my wife|my boyfriend|my fianc|my partner",
    'caribe_afro': r"jamaica|caribbean|trinidad|haiti|bush tea|cerasee|belly ache|island|africa|ghana|nigeri|my (grandma|mama|mom|aunt)s? (used|made|gave|always)|growing up|back home|heritage|ancestr|west indian",
    'cuida_familia': r"my (whole )?(family|household)|my (parents|mother|father|dad|mom|grandmother)|gave (this )?to (my|all)|kids",
    'edad_mencion': r"\b(i.m|im|i am|aged?)\s*(in my )?([2-9]\d)\b|in my (20|30|40|50|60|70)s|(\d\d) years? old|senior|seventy|sixty|fifty",
    'trabajo_estilo_vida': r"nurse|athlete|gym|workout|runner|vegan|keto|carnivore|fasting|intermittent|work(ing)? (night|long)|travel",
    'fe_natural': r"\bgod\b|bless|pray|holistic|\bnature\b|naturally",
}
ESCEPTICISMO = {
    'conoce_senna': r'senna|contains sen|has sen',
    'duda_reseñas_falsas': r'fake review|paid review|\bbots?\b|too good to be true|\bscam|\bhype\b|gimmick|placebo',
    'consulta_medico': r"consult|doctor|physician|medical (advice|professional)|not (a )?(doctor|md)|disclaimer|check with",
    'precaucion_dosis': r'diluted|dilute|start(ed)? (slow|small|with a)|half|teaspoon|tablespoon|tbsp|tsp|dose|dosage',
}
EMOCION = {
    'sorpresa_positiva': r'surpris|amaz|wow|shock|unbelievable|blown away|did not expect|didn.t expect',
    'alivio': r'relie[fv]|finally|at last|thank (god|goodness)|life.?chang|game.?chang|best (thing|decision)',
    'duda_inicial': r'skeptic|sceptic|hesitat|nervous|wasn.t sure|wary|doubt|on the fence|didn.t believe|did not believe',
    'frustracion': r'frustrat|disappoint|upset|angry|mad\b|regret|rip.?off|waste of|ruined',
    'miedo_cuidado': r'scared|afraid|worried|concern|careful|warn|beware|caution|dangerous|harm',
    'recompra': r'reorder|re-order|buy again|bought (it )?again|repeat|keep (buying|ordering)|stock up|will (buy|order)|subscribe',
}
USO = {
    'primer_dia': r'first (day|time|dose|night|morning)|first few',
    'mañana_ayunas': r'morning|empty stomach|before breakfast|first thing|upon waking',
    'noche': r'at night|before bed|bedtime|evening',
    'diluido': r'dilute|in (water|juice|tea)|mix(ed)? with|chaser|with juice|shot',
    'semanas': r'(\d+|two|three|four|a couple|few) (weeks?|months?)|week \d|\d+ days?',
    'dias_rapido': r'(same|next) day|within (hours|a day|24)|overnight|hours? later|immediately|right away',
}


def num(v):
    m = re.search(r'\d+', str(v or ''))
    return int(m.group()) if m else 0


def norm(s):
    return (s or '').replace('’', "'").lower()


def cuenta_fecha(f):
    f = norm(f)
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', f)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r'(\d{1,2}) de (\w+) de (\d{4})', f)
    if m and m.group(2) in MESES:
        return int(m.group(3)), MESES[m.group(2)]
    m = re.search(r'(\w+) (\d{1,2}), (\d{4})', f)
    if m:
        mes = {'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6, 'july': 7, 'august': 8,
               'september': 9, 'october': 10, 'november': 11, 'december': 12}.get(m.group(1))
        return int(m.group(3)), mes
    return None, None


def estrellas(v):
    m = re.match(r'(\d)', str(v))
    return int(m.group(1)) if m else None


def genero(nombre):
    p = re.findall(r"[a-z]+", norm(nombre))
    if not p:
        return 'No claro'
    n = APODOS.get(p[0], p[0])
    for k, lst in NOMBRES_US.items():
        if n in lst:
            return {'unisex': 'No claro'}.get(k, k)
    return 'No claro'


def cargar():
    filas = []
    c = sqlite3.connect(RAIZ / 'resenas.db')
    c.row_factory = sqlite3.Row
    for r in c.execute('select * from resenas'):
        a, m = cuenta_fecha(r['fecha'])
        filas.append(dict(id=r['id'], producto=PRODUCTOS.get(r['asin'], 'bundle'), nombre=r['nombre'], est=int(r['estrellas']), anio=a, mes=m,
                          titulo=r['titulo'] or '', texto=r['texto'] or '', verif=bool(r['verificada']),
                          util=num(r['util']), fotos=num(r['fotos']), variante=r['variante'] or ''))
    for arch, prod in (('nuevas_resenas_soursop.json', 'soursop_solo'), ('nuevas_resenas_blackseed.json', 'blackseed_solo')):
        for k, v in json.load(open(RAIZ / arch)).items():
            a, m = cuenta_fecha(v.get('fecha'))
            filas.append(dict(id=k, producto=prod, nombre=v.get('nombre', ''), est=estrellas(v.get('estrellas')),
                              anio=a, mes=m, titulo=v.get('titulo', ''), texto=v.get('texto', ''),
                              verif=bool(v.get('verificada')), util=num(v.get('util')), fotos=num(v.get('fotos')),
                              variante=v.get('variante', '')))
    # genero: etiqueta de la base (texto + nombre + gender-guesser) cuando existe; si no, lista de nombres
    gen_db = {}
    for rid, val, conf in c.execute("select g.id_resena, g.valor, c.valor from etiquetas g left join etiquetas c on c.id_resena=g.id_resena and c.tipo='genero_confianza' and c.version_dicc=g.version_dicc where g.tipo='genero' and g.version_dicc='propio_v1'"):
        gen_db[rid] = {'unisex': 'No claro'}.get(val, val)
    # quitar duplicados por id
    vistos, out = set(), []
    for f in filas:
        if f['id'] in vistos or not f['est']:
            continue
        vistos.add(f['id'])
        f['genero'] = gen_db.get(f['id']) or genero(f['nombre'])
        f['t'] = norm(f['titulo'] + '. ' + f['texto'])
        out.append(f)
    return out


def etiquetar(filas, dicc):
    pats = {k: re.compile(v) for k, v in dicc.items()}
    for f in filas:
        f.setdefault('tags', set())
        for k, p in pats.items():
            if p.search(f['t']):
                f['tags'].add(k)


def conteo(filas, tag, filtro=lambda f: True):
    sub = [f for f in filas if filtro(f)]
    n = sum(1 for f in sub if tag in f['tags'])
    return n, len(sub)


def citas(filas, tag, k=4, minlen=60, maxlen=320):
    """Citas literales: las más votadas y más largas dentro del rango."""
    c = [f for f in filas if tag in f['tags'] and minlen <= len(f['texto']) <= maxlen]
    c.sort(key=lambda f: (-(f['util']), -len(f['texto'])))
    return [dict(id=f['id'], est=f['est'], gen=f['genero'], prod=f['producto'], texto=f['texto'].strip()) for f in c[:k]]


def logodds(filas, pos, neg, top=25, minc=8):
    stop = set('the a an and or but is are was were be been to of in on for with it its this that i my me you your we our they them he she his her at as by from so if not no do did have has had just very can will would could get got than then there their about out up all more most really also one two too into over some any when what which how who because even much'.split())
    cp, cn = Counter(), Counter()
    np_, nn = 0, 0
    for f in filas:
        w = set(w for w in re.findall(r"[a-z']{3,}", f['t']) if w not in stop)
        if pos(f):
            cp.update(w); np_ += 1
        elif neg(f):
            cn.update(w); nn += 1
    res = []
    for w in set(cp) | set(cn):
        if cp[w] + cn[w] < minc:
            continue
        lo = math.log((cp[w] + 0.5) / (np_ - cp[w] + 0.5)) - math.log((cn[w] + 0.5) / (nn - cn[w] + 0.5))
        res.append((lo, w, cp[w], cn[w]))
    res.sort(reverse=True)
    return dict(n_pos=np_, n_neg=nn,
                pos=[(w, a, b, round(lo, 2)) for lo, w, a, b in res[:top]],
                neg=[(w, a, b, round(lo, 2)) for lo, w, a, b in res[-top:][::-1]])


def main(salida):
    filas = cargar()
    for d in (TEMAS, QUEJAS, PROBO_ANTES, FUENTE, IDENTIDAD, ESCEPTICISMO, EMOCION, USO):
        etiquetar(filas, d)
    out = {'n': len(filas)}
    prods = sorted(set(f['producto'] for f in filas))
    out['por_producto'] = {p: dict(n=sum(1 for f in filas if f['producto'] == p),
                                   est=dict(sorted(Counter(f['est'] for f in filas if f['producto'] == p).items())),
                                   verif=sum(f['verif'] for f in filas if f['producto'] == p),
                                   anios=dict(Counter(f['anio'] for f in filas if f['producto'] == p)),
                                   long_media=round(sum(len(f['texto']) for f in filas if f['producto'] == p) / max(1, sum(1 for f in filas if f['producto'] == p)))) for p in prods}
    out['genero'] = {p: dict(Counter(f['genero'] for f in filas if f['producto'] == p)) for p in prods}
    out['genero_total'] = dict(Counter(f['genero'] for f in filas))
    # tasa de estrellas por genero
    out['est_por_genero'] = {g: dict(sorted(Counter(f['est'] for f in filas if f['genero'] == g).items())) for g in ('Mujer', 'Hombre', 'No claro')}
    # meses
    out['por_mes'] = {f'{a}-{m:02d}': n for (a, m), n in sorted(Counter((f['anio'], f['mes']) for f in filas if f['anio']).items())}
    # variantes bundle
    out['variantes'] = dict(Counter(re.sub(r'\s+', ' ', f['variante']) for f in filas if f['producto'] == 'bundle').most_common(8))
    out['util_top'] = [dict(id=f['id'], util=f['util'], est=f['est'], texto=f['texto'][:300]) for f in sorted(filas, key=lambda f: -f['util'])[:12]]
    grupos = dict(TEMAS=TEMAS, QUEJAS=QUEJAS, PROBO_ANTES=PROBO_ANTES, FUENTE=FUENTE, IDENTIDAD=IDENTIDAD,
                  ESCEPTICISMO=ESCEPTICISMO, EMOCION=EMOCION, USO=USO)
    segs = {
        'todas': lambda f: True,
        'mujer': lambda f: f['genero'] == 'Mujer',
        'hombre': lambda f: f['genero'] == 'Hombre',
        '1-2★': lambda f: f['est'] <= 2,
        '3★': lambda f: f['est'] == 3,
        '4-5★': lambda f: f['est'] >= 4,
        'mujer_1-2★': lambda f: f['genero'] == 'Mujer' and f['est'] <= 2,
        'mujer_4-5★': lambda f: f['genero'] == 'Mujer' and f['est'] >= 4,
        'bundle': lambda f: f['producto'] == 'bundle',
        'soursop_solo': lambda f: f['producto'] == 'soursop_solo',
        'blackseed_solo': lambda f: f['producto'] == 'blackseed_solo',
        'texto_largo_300+': lambda f: len(f['texto']) >= 300,
    }
    out['segmentos_n'] = {s: sum(1 for f in filas if fn(f)) for s, fn in segs.items()}
    out['tabla'] = {}
    for gname, d in grupos.items():
        out['tabla'][gname] = {}
        for tag in d:
            out['tabla'][gname][tag] = {s: conteo(filas, tag, fn)[0] for s, fn in segs.items()}
    out['citas'] = {}
    for gname, d in grupos.items():
        for tag in d:
            out['citas'][f'{gname}.{tag}'] = citas(filas, tag)
    out['logodds_5_vs_1'] = logodds(filas, lambda f: f['est'] == 5, lambda f: f['est'] <= 2)
    out['logodds_mujer_vs_hombre'] = logodds(filas, lambda f: f['genero'] == 'Mujer', lambda f: f['genero'] == 'Hombre')
    # reseñas largas de mujeres 4-5★ y 1-2★ para lectura directa
    mm = [f for f in filas if f['genero'] == 'Mujer' and len(f['texto']) >= 350]
    mm.sort(key=lambda f: -f['util'])
    out['lectura_mujeres'] = [dict(id=f['id'], est=f['est'], prod=f['producto'], texto=f['texto'][:700]) for f in mm[:30]]
    # coocurrencias: dolor x probó antes (mujeres y todas)
    out['coocurrencia_dolor_probo'] = {d: {p: sum(1 for f in filas if d in f['tags'] and p in f['tags']) for p in PROBO_ANTES} for d in ('hinchazon', 'estrenimiento', 'digestion_general', 'energia', 'detox_limpieza')}
    out['coocurrencia_dolor_queja'] = {d: {q: sum(1 for f in filas if d in f['tags'] and q in f['tags']) for q in QUEJAS} for d in ('hinchazon', 'estrenimiento', 'digestion_general', 'energia', 'detox_limpieza')}
    out['coocurrencia_dolor_estrellas'] = {d: dict(sorted(Counter(f['est'] for f in filas if d in f['tags']).items())) for d in TEMAS}
    json.dump(out, open(salida, 'w'), ensure_ascii=False, indent=1, default=list)
    print('ok', out['n'], salida)


if __name__ == '__main__':
    main(sys.argv[1])
