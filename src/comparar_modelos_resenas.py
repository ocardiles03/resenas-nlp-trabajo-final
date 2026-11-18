#!/usr/bin/env python3
"""Compara la balanza aprendida, KNN y variantes sobre TODAS las resenas con texto del Excel v4, con validacion cruzada
(cada resena se lee solo con modelos que no la vieron). Correr: .venv/bin/python -I este_archivo.py
Salida: comparacion_modelos_v4.md / .csv en data/. Las de 3 estrellas se puntuan con el modelo ajustado a todas las polares.
"""
import csv, importlib.util, sys
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.stats import rankdata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline

TOOLS = Path(__file__).resolve().parent
def cargar(n):
    sp = importlib.util.spec_from_file_location(n, TOOLS / (n + '.py')); m = importlib.util.module_from_spec(sp); sys.modules[n] = m; sp.loader.exec_module(m); return m
dc, lx, kn = cargar('diccionario_cliente'), cargar('lexico_cliente'), None
OUT = dc.OUT
import json, re
lemas = json.loads((OUT / 'lemas_cliente_v4.json').read_text(encoding='utf-8'))
VAC = lx.VACIAS
def limpiar(t, vac=True, lem=True):
    w = [x.strip("'") for x in re.findall(r"[a-z']+", t.lower().replace('’', "'"))]
    return ' '.join((lemas.get(x, x) if lem else x) for x in w if x and not (vac and x in VAC))

rev = dc.cargar(dc.XLSX)
for r in rev: r['txt'] = r['titulo'] + '. ' + r['texto']; r['cl'] = limpiar(r['txt'])
pol = [r for r in rev if r['estrellas'] != 3]; tib = [r for r in rev if r['estrellas'] == 3]
y = np.array([int(r['estrellas'] >= 4) for r in pol]); n = len(pol)
txt = [r['txt'] for r in pol]; cl = np.array([r['cl'] for r in pol])
K = 25

def knn(k=K, ng=(1, 2), mdf=5, vocab=None):
    return make_pipeline(TfidfVectorizer(min_df=mdf if vocab is None else 1, ngram_range=ng, vocabulary=vocab), KNeighborsClassifier(n_neighbors=k, metric='cosine'))

def pred(nombre, itr, ite, textos_tr=None):
    """devuelve puntaje (mayor = mas positivo) para ite, entrenando solo con itr"""
    if nombre == 'balanza':
        lex = lx.aprender([pol[i] for i in itr]); return np.array([lx.puntaje(txt[i], lex) for i in ite], float)
    if nombre == 'knn':
        return knn().fit(cl[itr], y[itr]).predict_proba(cl[ite])[:, 1]
    if nombre == 'knn_sin_lemas':
        c = np.array([limpiar(t, lem=False) for t in txt]); return knn().fit(c[itr], y[itr]).predict_proba(c[ite])[:, 1]
    if nombre == 'knn_unigramas':
        return knn(ng=(1, 1)).fit(cl[itr], y[itr]).predict_proba(cl[ite])[:, 1]
    if nombre == 'knn_sin_quitar_vacias':
        c = np.array([limpiar(t, vac=False) for t in txt]); return knn().fit(c[itr], y[itr]).predict_proba(c[ite])[:, 1]
    if nombre == 'knn_con_diccionario':   # KNN que solo mira los terminos del diccionario aprendido en el entrenamiento
        lex = lx.aprender([pol[i] for i in itr], lemas)
        voc = sorted({t for t in lex}) 
        m = make_pipeline(TfidfVectorizer(vocabulary=voc, ngram_range=(1, 2), token_pattern=r"[a-z']+"), KNeighborsClassifier(n_neighbors=K, metric='cosine'))
        c = np.array([' '.join(lemas.get(x, x) for x in re.findall(r"[a-z']+", t.lower().replace('’', "'"))) for t in txt])
        # filas vacias (sin ningun termino del diccionario) caen en 0 vectores: se les da la proporcion base
        try: return m.fit(c[itr], y[itr]).predict_proba(c[ite])[:, 1]
        except Exception: return np.full(len(ite), y[itr].mean())
    if nombre == 'regresion_logistica':
        return make_pipeline(TfidfVectorizer(min_df=5, ngram_range=(1, 2)), LogisticRegression(C=3, max_iter=2000)).fit(cl[itr], y[itr]).predict_proba(cl[ite])[:, 1]
    if nombre == 'knn+balanza':
        a = pred('knn', itr, ite); b = pred('balanza', itr, ite)
        return (rankdata(a) + rankdata(b)) / (2 * len(ite))
    if nombre == 'knn+regresion':
        a = pred('knn', itr, ite); b = pred('regresion_logistica', itr, ite)
        return (rankdata(a) + rankdata(b)) / (2 * len(ite))

modelos = ['balanza', 'knn', 'knn_con_diccionario', 'knn_sin_lemas', 'knn_unigramas', 'knn_sin_quitar_vacias', 'regresion_logistica', 'knn+balanza', 'knn+regresion']
rskf = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=42)
res = {m: {'auc': [], 'acc': [], 'pos': [], 'neg': []} for m in modelos}
oof = {m: np.zeros(n) for m in modelos}; cuenta = np.zeros(n)
for itr, ite in rskf.split(np.zeros(n), y):
    cuenta[ite] += 1
    for m in modelos:
        s = pred(m, itr, ite); oof[m][ite] += s
        if m == 'balanza': d = s > 0
        elif m in ('knn+balanza', 'knn+regresion'): d = s > np.quantile(s, 1 - y[itr].mean())   # corte: misma proporcion de positivas que el entrenamiento
        else: d = s > y[itr].mean()
        yt = y[ite]
        res[m]['auc'].append(roc_auc_score(yt, s)); res[m]['acc'].append((d == yt).mean())
        res[m]['pos'].append(d[yt == 1].mean()); res[m]['neg'].append((~d)[yt == 0].mean())
for m in modelos: oof[m] /= cuenta
ms = lambda v: f'{np.mean(v):.3f} ± {np.std(v):.3f}'
md = ['# Comparación de modelos sobre todas las reseñas escritas (Excel v4)', '',
      f'{len(rev)} reseñas con texto: {n} polares (4-5★ = positiva: {int(y.sum())}; 1-2★ = negativa: {int((1-y).sum())}) y {len(tib)} de 3★. Validación cruzada de 5 grupos repetida 3 veces (15 ajustes): cada reseña se lee siempre con modelos que no la vieron. KNN con k={K}, TF-IDF de palabras y parejas, texto lematizado. Corte de KNN y regresión = proporción de positivas del entrenamiento; la balanza usa >0; las combinaciones usan la misma proporción.', '',
      '## 1. Resultados (media ± desviación en los 15 ajustes)', '', '| Modelo | Exactitud | Positivas reconocidas | Negativas reconocidas | AUC |', '|---|---|---|---|---|']
nom = {'balanza': 'Balanza aprendida (diccionario anterior)', 'knn': 'KNN (palabras + parejas, lematizado)', 'knn_con_diccionario': 'KNN solo con términos del diccionario', 'knn_sin_lemas': 'KNN sin lematizar', 'knn_unigramas': 'KNN solo palabras sueltas', 'knn_sin_quitar_vacias': 'KNN sin quitar palabras vacías', 'regresion_logistica': 'Regresión logística (TF-IDF)', 'knn+balanza': 'KNN + balanza (promedio de posiciones)', 'knn+regresion': 'KNN + regresión'}
md.append(f'| Regla ingenua (todas positivas) | {y.mean():.3f} | 1.000 | 0.000 | 0.500 |')
for m in sorted(modelos, key=lambda m: -np.mean(res[m]['auc'])):
    r = res[m]; md.append(f"| {nom[m]} | {ms(r['acc'])} | {ms(r['pos'])} | {ms(r['neg'])} | {ms(r['auc'])} |")
md.append('')
# por estrellas (fuera de muestra)
best = max(modelos, key=lambda m: np.mean(res[m]['auc']))
st = np.array([r['estrellas'] for r in pol]); gen = np.array([r['genero'] for r in pol])
def dec(m):
    s = oof[m]; return s > 0 if m == 'balanza' else (s > np.quantile(s, 1 - y.mean()) if '+' in m else s > y.mean())
md += [f'## 2. Aciertos por número de estrellas y por género estimado (fuera de muestra)', '', '| Grupo | Reseñas | Balanza | KNN | KNN + balanza |', '|---|---|---|---|---|']
for etq, mask in [(f'{e}★', st == e) for e in (1, 2, 4, 5)] + [(g, gen == g) for g in ('Hombre', 'Mujer', 'No claro')]:
    if mask.sum() == 0: continue
    ok = lambda m: ((dec(m) == y)[mask]).mean()
    md.append(f'| {etq} | {int(mask.sum())} | {ok("balanza"):.2f} | {ok("knn"):.2f} | {ok("knn+balanza"):.2f} |')
md.append('')
# 3 estrellas
m_all = knn().fit(cl, y); pt = m_all.predict_proba(np.array([r['cl'] for r in tib]))[:, 1]
lex_all = lx.aprender(pol); sb = np.array([lx.puntaje(r['txt'], lex_all) for r in tib], float)
md += ['## 3. Las 99 reseñas de 3★ (sin respuesta correcta; lectura de los modelos ajustados a todas las polares)', '',
       f'- KNN: {(pt > y.mean()).sum()} positivas y {(pt <= y.mean()).sum()} negativas (media de probabilidad {pt.mean():.2f}).',
       f'- Balanza: {(sb > 0).sum()} positivas, {(sb < 0).sum()} negativas, {(sb == 0).sum()} neutras.', '']
# errores confiados
err = [(abs(oof['knn'][i] - y[i]), i) for i in range(n) if dec('knn')[i] != y[i]]
err.sort(reverse=True)
md += [f'## 4. Errores del KNN: {len(err)} de {n} ({len(err)/n*100:.1f} %). Los 12 más seguros de sí mismos', '', '| ID | Estrellas | Prob. positiva | Texto |', '|---|---|---|---|']
for _, i in err[:12]:
    md.append(f"| `{pol[i]['id']}` | {pol[i]['estrellas']}★ | {oof['knn'][i]:.2f} | {pol[i]['txt'][:170].replace('|', '/')} |")
md.append('')
tipos = Counter('queja leída como elogio' if y[i] == 0 else 'elogio leído como queja' for _, i in err)
md += ['Tipos de error:', ''] + [f'- {k}: {v}' for k, v in tipos.items()] + ['']
# curva de aprendizaje y k
rs = np.random.default_rng(0); curva = []
for frac in (0.25, 0.5, 0.75, 1.0):
    a = []
    for itr, ite in list(RepeatedStratifiedKFold(n_splits=5, n_repeats=1, random_state=7).split(np.zeros(n), y)):
        sub = rs.choice(itr, int(len(itr) * frac), replace=False)
        a.append(roc_auc_score(y[ite], knn().fit(cl[sub], y[sub]).predict_proba(cl[ite])[:, 1]))
    curva.append((frac, np.mean(a)))
md += ['## 5. ¿Más reseñas ayudarían? (curva de aprendizaje del KNN, AUC)', '', '| % del entrenamiento | ' + ' | '.join(f'{int(f*100)}' for f, _ in curva) + ' |', '|---|---|---|---|---|', '| AUC | ' + ' | '.join(f'{a:.3f}' for _, a in curva) + ' |', '']
(OUT / 'comparacion_modelos_v4.md').write_text('\n'.join(md), encoding='utf-8')
with (OUT / 'comparacion_modelos_v4.csv').open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f); w.writerow(['id', 'estrellas', 'genero', 'prob_knn', 'puntaje_balanza', 'prob_knn_mas_balanza', 'real', 'texto'])
    for i, r in enumerate(pol): w.writerow([r['id'], r['estrellas'], r['genero'], round(oof['knn'][i], 3), round(oof['balanza'][i], 2), round(oof['knn+balanza'][i], 3), 'positiva' if y[i] else 'negativa', r['txt']])
    for r, p, s in zip(tib, pt, sb): w.writerow([r['id'], 3, r['genero'], round(p, 3), round(s, 2), '', 'tibia', r['txt']])
print('\n'.join(md))
