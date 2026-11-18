#!/usr/bin/env python3
"""Etiquetado AUTOMATICO de las dos bases (bundle v4 y Soursop) con las mismas categorias de la hoja manual,
tablas de frecuencias y, si se da la hoja etiquetada, el ACUERDO entre lo automatico y lo manual.

Idea (metodo del curso): la muestra etiquetada a mano es la referencia; los detectores (reglas + lexico + KNN) se
aplican a todas las resenas, y el acuerdo con la muestra dice cuanto confiar en cada columna antes de sacar conclusiones.
Este script NO interpreta nada: solo cuenta y compara. Las reglas son un punto de partida para ajustar con el acuerdo.

Uso:  .venv/bin/python -I src/etiquetar_corpus.py [--hoja HOJA.xlsx [HOJA2.xlsx ...]] [--salida-dir DIR]
Escribe en data/ (o --salida-dir): corpus_etiquetado_automatico.csv, frecuencias_etiquetas_corpus.csv,
resumen_etiquetas_corpus.md y, con --hoja, acuerdo_etiquetas_manual.md.
"""
import argparse, csv, importlib.util, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from openpyxl import load_workbook
from sklearn.model_selection import StratifiedKFold, cross_val_predict

SRC = Path(__file__).resolve().parent
DATA = SRC.parent / 'data'
SEMILLA = 42
NO_DICE, NINGUNA = 'no_lo_dice', 'ninguna'


def cargar_modulo(nombre):
    """Importa un script hermano de src/ por ruta (src/ no es paquete y `python -I` no lo agrega al path)."""
    spec = importlib.util.spec_from_file_location(nombre, SRC / (nombre + '.py'))
    mod = importlib.util.module_from_spec(spec); sys.modules[nombre] = mod; spec.loader.exec_module(mod)
    return mod


cp = cargar_modulo('corpus_resenas')        # las dos bases con el mismo formato
dcl = cargar_modulo('diccionario_cliente')  # dcl.L: reglas (regex) por categoria del lenguaje del cliente
tx = cargar_modulo('taxonomia_resenas')     # tx.quejas / tx.QUEJAS: reglas de queja del proyecto
ac = cargar_modulo('acierto_sentimiento')   # limpiar / modelo_knn / elegir_k y el lexico (ac.lx)
lx = ac.lx


# ----------------------------------------------------------------------------------------------
# 1) Detectores: cada uno recibe el texto (titulo + '. ' + texto) y devuelve un CONJUNTO de etiquetas
#    (vacio => se rellena con 'ninguna' / 'no_lo_dice' segun el campo). Los nombres de etiqueta son los de la hoja manual,
#    en minusculas y con '_' en lugar de espacios, para poder compararlos.
# ----------------------------------------------------------------------------------------------
def rx(patron):
    """Compila como el diccionario del proyecto: sin letra pegada por delante y sin distinguir mayusculas."""
    return re.compile(r'(?<![a-z0-9])(?:' + patron + r')', re.I)


def norm(t):
    return t.replace('’', "'")


R = dcl.L['resultado']
RX_MEJORA, RX_SIN_EFECTO = rx(R['funciona_mejora']), rx(R['sin_efecto'])
RX_ADVERSO = rx(r"side effects?|allerg\w*|rash\w*|hives|dizz\w*|nause\w*|vomit\w*|hospital|made me (?:sick|ill)|headache\w*|cramp\w*|diarrh\w*")
RX_REEMBOLSO = rx(dcl.L['objecion_reembolso']['reembolso_devolucion'] + '|' + dcl.L['objecion_reembolso']['servicio_cliente'])
RX_SABOR_OK = rx(dcl.L['objecion_sabor']['sabor_aceptable'])
RX_VALOR = rx(r"worth (?:it|the|every|every penny)|good (?:price|value|deal)|great (?:price|value|deal)|bargain|affordable|reasonable(?:ly)? priced|for the price")
RX_RECOMIENDA = rx(r"recommend\w*")
RX_NIEGA_ANTES = re.compile(r"(?:\bnot|n't|\bnever|\bno)\s+(?:\w+\s+){0,2}$", re.I)   # 'do not recommend', "wouldn't recommend"
RX_CONFIANZA = rx(r"trust\w*|reliable|legit\w*|authentic|genuine|high[- ]quality|good quality|great quality|real deal|pure\b|organic|natural")
RX_ENTREGA = rx(r"fast (?:shipping|delivery|ship)|(?:arrived|delivered|came|shipped) (?:\w+ ){0,2}(?:quickly|fast|early|on time|promptly|ahead)|quick(?:ly)? (?:shipping|delivery)|great (?:customer )?(?:service|support)|excellent (?:customer )?service|well packaged|packaged well|arrived (?:safely|intact)")
RX_RECOMPRA_SI = rx(r"re-?order\w*|(?:buy|order|purchase)(?:ing)? (?:it |this |them |some )?(?:again|more)|(?:will|gonna|going to|plan to|definitely) (?:\w+ ){0,2}(?:buy|order|purchase)\b|(?:my|the) (?:2nd|3rd|second|third|fourth|\d+th) (?:bottle|order|time)|repeat (?:customer|order|buyer)|keep (?:buying|ordering)|subscribe\w*|stock(?:ed)? up")
RX_RECOMPRA_NO = rx(r"(?:won'?t|will not|would not|wouldn'?t|never|not going to|don'?t plan to|do not plan to)\s+(?:\w+\s+){0,2}(?:buy|order|purchase|re-?order)\b|never again|not (?:re-?ordering|buying again)")
RX_TIPO_RECOMPRA = rx(r"re-?order\w*|(?:buy|order|purchase)(?:ing)? (?:\w+ ){0,2}again|(?:2nd|3rd|second|third|fourth|\d+th|another) (?:bottle|order|time)|repeat (?:customer|order|buyer)|(?:ordered|bought|purchased|tried) (?:\w+ ){0,3}(?:before|previously|last (?:month|year|time))|(?:have|'ve) been (?:buying|ordering|taking|using|drinking) (?:this |it )?(?:for|since)|keep (?:buying|ordering)|used to (?:buy|order)")
RX_TIPO_NUEVO = rx(r"first (?:time|bottle|order|dose|day|week|use|impression|try)|(?:just|recently) (?:started|began|received|got|ordered|bought|purchased|tried|arrived)|new to|(?:haven'?t|have not) (?:\w+ ){0,2}tried|day (?:one|1|two|2|three|3)\b")
FAMILIA = r"husband|wife|mom|mother|dad|father|son|daughter|boyfriend|girlfriend|fianc\w+|partner|friend|sister|brother|mother-in-law|father-in-law|grandm\w+|grandf\w+|parents|kids|children|family|aunt|uncle|cousin|neighbor|coworker|boss|dog|cat"
RX_OTRO_FUERTE = rx(r"(?:for|to) my (?:" + FAMILIA + r")|(?:bought|ordered|purchased|got)\s+(?:\w+\s+){0,3}(?:as a )?gift|\bgift\b|gave (?:it |this |them |some )?to|\bfor (?:him|her|them)\b")
RX_OTRO_DEBIL = rx(r"my (?:" + FAMILIA + r") (?:takes|take|loves?|likes?|uses?|started|has been|is taking|said|says|tried|drinks)")
RX_PARA_SI = rx(r"for myself|for me\b|\bi (?:take|took|use|used|drink|drank|started|tried|have been taking|'ve been taking|am taking|'m taking)\b|\bmy (?:stomach|gut|body|digestion|bloating|weight|health|energy|skin|sugar|blood|cholesterol|belly|bowels?)\b|\bi(?:'m| am| was| have been|'ve been) (?:\w+ ){0,2}(?:taking|using|drinking)")
MOTIVOS = {g: rx(p) for g, p in dcl.L['dolor_sintoma'].items()}   # mismos nombres que la lista de la hoja


def sin_negacion(regex, t):
    """True si la regex aparece en alguna parte SIN una negacion justo antes (p. ej. 'recommend' pero no 'do not recommend')."""
    return any(not RX_NIEGA_ANTES.search(t[max(0, m.start() - 20):m.start()]) for m in regex.finditer(t))


def det_resultado(t):
    s = set()
    if RX_MEJORA.search(t) and not RX_SIN_EFECTO.search(t):
        s.add('mejora')
    if RX_SIN_EFECTO.search(t):
        s.add('sin_efecto')
    if RX_ADVERSO.search(t):
        s.add('efecto_adverso')
    return s or {NO_DICE}


def det_objecion(t):
    """Reglas de queja del proyecto (taxonomia_resenas.QUEJAS) + reembolso/servicio, efecto adverso y no funciona."""
    s = set(tx.quejas(norm(t).lower(), {g: [] for g in tx.QUEJAS}))
    if RX_REEMBOLSO.search(t): s.add('servicio_reembolso')
    if RX_ADVERSO.search(t): s.add('efecto_adverso')
    if RX_SIN_EFECTO.search(t): s.add('no_funciona')
    return s or {NINGUNA}


def det_razon_positiva(t):
    s = set()
    if RX_MEJORA.search(t) and not RX_SIN_EFECTO.search(t): s.add('resultado')
    if RX_SABOR_OK.search(t): s.add('sabor_aceptable')
    if RX_VALOR.search(t): s.add('buen_valor')
    if sin_negacion(RX_RECOMIENDA, t) or (RX_RECOMPRA_SI.search(t) and not RX_RECOMPRA_NO.search(t)): s.add('recomienda_recompra')
    if RX_CONFIANZA.search(t): s.add('confianza_marca')
    if RX_ENTREGA.search(t): s.add('entrega_servicio')
    return s or {NINGUNA}


def det_motivo(t):
    return {g for g, r in MOTIVOS.items() if r.search(t)} or {NO_DICE}


def det_recompra(t):
    if RX_RECOMPRA_NO.search(t): return {'no'}
    return {'si'} if RX_RECOMPRA_SI.search(t) else {NO_DICE}


def det_comprador_tipo(t):
    if RX_TIPO_RECOMPRA.search(t): return {'recompra'}
    return {'nuevo'} if RX_TIPO_NUEVO.search(t) else {NO_DICE}


def det_comprador_para(t):
    if RX_OTRO_FUERTE.search(t): return {'para_otra_persona'}
    if RX_PARA_SI.search(t): return {'para_si_mismo'}
    return {'para_otra_persona'} if RX_OTRO_DEBIL.search(t) else {NO_DICE}


_demo = None


def demografia():
    """Demografia (genero/zona del proyecto), creada una sola vez porque carga listas de nombres."""
    global _demo
    if _demo is None:
        _demo = cargar_modulo('demografia_resenas').Demografia(cargar_modulo('resenas_amazon_excel'))
    return _demo


def a_etiqueta(v):
    return v.strip().lower().replace(' ', '_')


def det_genero(t):
    """Genero SOLO por lo que dice el texto (sin nombre), igual que la hoja manual."""
    return {a_etiqueta(demografia().genero('', t)['genero'])}


def det_region(t):
    """Region de EE. UU. mencionada en el texto; 'ambigua' si el lugar no fija una region; 'no_se_menciona' si no hay."""
    return {a_etiqueta(m['region'] or 'Ambigua') for m in demografia().zona(t)['menciones']} or {'no_se_menciona'}


# campo -> (detector, columna manual equivalente en la hoja)
DETECTORES = {
    'genero': (det_genero, 'genero_manual'),
    'region': (det_region, 'region_manual'),
    'motivo_compra': (det_motivo, 'motivo_compra'),
    'resultado': (det_resultado, 'resultado_manual'),
    'objecion': (det_objecion, 'objecion_principal'),
    'razon_positiva': (det_razon_positiva, 'razon_positiva'),
    'recompra': (det_recompra, 'recompra'),
    'comprador_tipo': (det_comprador_tipo, 'comprador_tipo'),
    'comprador_para': (det_comprador_para, 'comprador_para'),
}


# ----------------------------------------------------------------------------------------------
# 2) Sentimiento de todo el corpus: lexico del proyecto y KNN con estrellas (entrenado con el bundle)
# ----------------------------------------------------------------------------------------------
def sentimiento_corpus(corpus):
    """Devuelve {id: dict(sentimiento_lexico, puntaje_lexico, prob_positiva_knn, sentimiento_knn)}.
    KNN: se entrena con las 4-5 vs 1-2 estrellas del bundle. Las resenas del bundle con nota (1,2,4,5) se puntuan
    fuera de muestra (validacion cruzada) para que no vean su propia nota; las 3 estrellas y todo el Soursop usan el modelo completo."""
    d = json.loads((ac.DATA / 'lexico_cliente_v4.json').read_text(encoding='utf-8'))
    lex = {**{x: 2 for x in d['positivas']}, **{x: -2 for x in d['negativas']}}
    txt = {r['id']: r['titulo'] + '. ' + r['texto'] for r in corpus}
    out = {r['id']: {'puntaje_lexico': lx.puntaje(txt[r['id']], lex)} for r in corpus}
    for v in out.values():
        v['sentimiento_lexico'] = ac.lectura_lexico(v['puntaje_lexico'])
    ent = [r for r in corpus if r['base'] == 'bundle' and r['estrellas'] != 3]
    X = np.array([ac.limpiar(txt[r['id']]) for r in ent]); y = np.array([1 if r['estrellas'] >= 4 else 0 for r in ent])
    k, _ = ac.elegir_k(X, y, min_df=5)
    cv = StratifiedKFold(5, shuffle=True, random_state=SEMILLA)
    oof = cross_val_predict(ac.modelo_knn(k, 5), X, y, cv=cv, method='predict_proba')[:, 1]
    p = {r['id']: pr for r, pr in zip(ent, oof)}
    modelo = ac.modelo_knn(k, 5).fit(X, y)
    resto = [r for r in corpus if r['id'] not in p]
    for r, pr in zip(resto, modelo.predict_proba(np.array([ac.limpiar(txt[r['id']]) for r in resto]))[:, 1]):
        p[r['id']] = pr
    corte = y.mean()   # punto de corte = proporcion de positivas del entrenamiento (como knn_resenas.py)
    for i, v in out.items():
        v['prob_positiva_knn'] = float(p[i]); v['sentimiento_knn'] = 'Positivo' if p[i] > corte else 'Negativo'
    return out, k


# ----------------------------------------------------------------------------------------------
# 3) Etiquetar todo el corpus y contar
# ----------------------------------------------------------------------------------------------
def etiquetar(corpus):
    sent, k = sentimiento_corpus(corpus)
    filas = []
    for r in corpus:
        t = r['titulo'] + '. ' + r['texto']
        f = dict(r); f.update(sent[r['id']])
        for campo, (det, _) in DETECTORES.items():
            f[campo] = '|'.join(sorted(det(t)))
        filas.append(f)
    return filas, k


def grupo_estrellas(e):
    return '1-2' if e <= 2 else ('3' if e == 3 else '4-5')


CAMPOS_FREQ = ['sentimiento_lexico', 'sentimiento_knn'] + list(DETECTORES)


def frecuencias(filas):
    """Cuenta, para cada base x semestre x grupo de estrellas, en cuantas resenas aparece cada valor de cada campo.
    Las etiquetas 'todas'/'todos' agregan. Un campo con varias etiquetas cuenta la resena una vez por etiqueta."""
    cont = defaultdict(Counter)   # (base, semestre, grupo) -> Counter{(campo, valor): n}
    tam = Counter()               # (base, semestre, grupo) -> resenas
    for f in filas:
        pares = [(c, v) for c in CAMPOS_FREQ for v in f[c].split('|')]
        for b in (f['base'], 'todas'):
            for s in (f['semestre'], 'todos'):
                for g in (grupo_estrellas(f['estrellas']), 'todas'):
                    tam[(b, s, g)] += 1
                    cont[(b, s, g)].update(pares)
    out = []
    for clave in sorted(cont):
        n = tam[clave]
        out.append(clave + ('n_resenas', '', n, 1.0))
        out += [clave + (campo, valor, v, v / n) for (campo, valor), v in sorted(cont[clave].items())]
    return out


def resumen_md(filas, k):
    """Tabla por campo: % de resenas con cada valor, por base (solo numeros)."""
    n = Counter(f['base'] for f in filas)
    md = ['# Etiquetado automatico del corpus: frecuencias por base', '',
          f"Resenas: bundle {n['bundle']}, soursop {n['soursop']}. KNN con estrellas: k = {k}. Un campo con varias etiquetas cuenta la resena en cada una; los % son sobre todas las resenas de la base.", '']
    for campo in CAMPOS_FREQ:
        cont = {b: Counter(v for f in filas if f['base'] == b for v in f[campo].split('|')) for b in n}
        valores = sorted(set().union(*cont.values()), key=lambda v: -sum(c[v] for c in cont.values()))
        md += [f'## {campo}', '', '| Valor | bundle n | bundle % | soursop n | soursop % |', '|---|---|---|---|---|']
        md += [f"| {v} | {cont['bundle'][v]} | {100 * cont['bundle'][v] / n['bundle']:.1f} | {cont['soursop'][v]} | {100 * cont['soursop'][v] / n['soursop']:.1f} |" for v in valores]
        md.append('')
    return '\n'.join(md) + '\n'


# ----------------------------------------------------------------------------------------------
# 4) Acuerdo entre lo automatico y la muestra etiquetada a mano
# ----------------------------------------------------------------------------------------------
def leer_hojas_completas(rutas):
    """Lee las hojas etiquetadas: lista de dicts con todas las columnas (valores vacios = None)."""
    filas, vistos = [], set()
    for ruta in rutas:
        ws = load_workbook(ruta, data_only=True)['Etiquetado']
        cab = [c.value for c in ws[1]]
        for v in ws.iter_rows(min_row=2, values_only=True):
            r = dict(zip(cab, v))
            if r.get('id') and r['id'] not in vistos:
                vistos.add(r['id']); filas.append(r)
    return filas


def parsear_manual(v):
    """Celda manual -> conjunto de etiquetas normalizadas (separa por '|'); None si esta vacia (esa fila no cuenta en ese campo)."""
    if v is None or not str(v).strip():
        return None
    return {a_etiqueta(x) for x in str(v).split('|') if x.strip()}


def acuerdo(hoja):
    """Por campo: n de filas con etiqueta manual, % de coincidencia exacta de conjuntos y, por etiqueta, precision/sensibilidad/F1
    de su presencia (etiqueta en el conjunto automatico vs en el manual). Nota de metodo: objecion_principal manual es UNA sola
    etiqueta por resena y la automatica puede detectar varias, por eso en 'objecion' la medida clave es la sensibilidad
    (principal manual contenida en las detectadas) y la precision queda subestimada."""
    res = {}
    for campo, (det, col) in DETECTORES.items():
        pares = []
        for r in hoja:
            m = parsear_manual(r.get(col))
            if m is not None:
                pares.append((m, det((r.get('titulo') or '') + '. ' + (r.get('texto') or ''))))
        if not pares:
            continue
        etqs = {}
        for e in sorted(set().union(*[m | a for m, a in pares])):
            vp = sum(1 for m, a in pares if e in m and e in a); fp = sum(1 for m, a in pares if e not in m and e in a)
            fn = sum(1 for m, a in pares if e in m and e not in a)
            pr = vp / (vp + fp) if vp + fp else float('nan'); se = vp / (vp + fn) if vp + fn else float('nan')
            f1 = 2 * pr * se / (pr + se) if pr == pr and se == se and pr + se else float('nan')
            etqs[e] = {'apoyo': vp + fn, 'vp': vp, 'fp': fp, 'fn': fn, 'precision': pr, 'sensibilidad': se, 'f1': f1}
        res[campo] = {'n': len(pares), 'exacta': sum(1 for m, a in pares if m == a) / len(pares),
                      'contenida': sum(1 for m, a in pares if m <= a) / len(pares), 'etiquetas': etqs}
    return res


def acuerdo_md(res, hojas):
    f = lambda x: 'n/d' if x != x else f'{x:.2f}'
    md = ['# Acuerdo entre etiquetas automaticas y etiquetas manuales', '', f"Hoja(s): {', '.join(hojas)}. Solo cuentan las filas con la columna manual llena.",
          'exacta = el conjunto automatico es igual al manual; contenida = lo manual esta dentro de lo detectado. Por etiqueta: apoyo = veces que aparece en lo manual.', '']
    for campo, d in res.items():
        md += [f"## {campo} (n = {d['n']}; coincidencia exacta {d['exacta']:.2f}; contenida {d['contenida']:.2f})", '',
               '| Etiqueta | Apoyo | VP | FP | FN | Precision | Sensibilidad | F1 |', '|---|---|---|---|---|---|---|---|']
        md += [f"| {e} | {v['apoyo']} | {v['vp']} | {v['fp']} | {v['fn']} | {f(v['precision'])} | {f(v['sensibilidad'])} | {f(v['f1'])} |" for e, v in d['etiquetas'].items()]
        md.append('')
    return '\n'.join(md) + '\n'


def main():
    ap = argparse.ArgumentParser(description='Etiquetado automatico del corpus y acuerdo con la muestra manual')
    ap.add_argument('--hoja', nargs='+', type=Path, help='hoja(s) etiquetadas para medir el acuerdo (opcional)')
    ap.add_argument('--salida-dir', type=Path, default=DATA)
    a = ap.parse_args()
    corpus = cp.cargar_todo()
    filas, k = etiquetar(corpus)
    a.salida_dir.mkdir(parents=True, exist_ok=True)
    cols = ['base', 'id', 'fecha', 'semestre', 'estrellas', 'sentimiento_lexico', 'puntaje_lexico', 'sentimiento_knn', 'prob_positiva_knn'] + list(DETECTORES) + ['titulo', 'texto']
    with (a.salida_dir / 'corpus_etiquetado_automatico.csv').open('w', encoding='utf-8-sig', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore'); w.writeheader()
        w.writerows([{**f, 'prob_positiva_knn': round(f['prob_positiva_knn'], 3)} for f in filas])
    with (a.salida_dir / 'frecuencias_etiquetas_corpus.csv').open('w', encoding='utf-8-sig', newline='') as fh:
        w = csv.writer(fh); w.writerow(['base', 'semestre', 'estrellas', 'campo', 'valor', 'n', 'proporcion']); w.writerows(frecuencias(filas))
    (a.salida_dir / 'resumen_etiquetas_corpus.md').write_text(resumen_md(filas, k), encoding='utf-8')
    print(f'{len(filas)} resenas etiquetadas -> {a.salida_dir}')
    if a.hoja:
        res = acuerdo(leer_hojas_completas(a.hoja))
        (a.salida_dir / 'acuerdo_etiquetas_manual.md').write_text(acuerdo_md(res, [p.name for p in a.hoja]), encoding='utf-8')
        print('acuerdo ->', a.salida_dir / 'acuerdo_etiquetas_manual.md')


if __name__ == '__main__':
    main()
