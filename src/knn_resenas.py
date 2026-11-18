#!/usr/bin/env python3
"""KNN sobre las resenas de Amazon (Clase 12, EAFIT): lee la opinion de un texto por sus vecinos mas parecidos.
Correr con el venv: .venv/bin/python -I src/knn_resenas.py
Pide scikit-learn y numpy. Lee el xlsx v4 y lemas_cliente_v4.json; escribe knn_resenas_v4.md y knn_resenas_v4.csv.
"""
import csv, importlib.util, json, re, sys
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import confusion_matrix, roc_auc_score
from sklearn.model_selection import cross_val_predict, cross_val_score, StratifiedKFold, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline

TOOLS = Path(__file__).resolve().parent
OUT = TOOLS.parent / 'data'
spec = importlib.util.spec_from_file_location('dc', TOOLS / 'diccionario_cliente.py')
dc = importlib.util.module_from_spec(spec); sys.modules['dc'] = dc; spec.loader.exec_module(dc)
# palabras vacias SIN negaciones ni opinion (leccion de la Clase 11)
VACIAS = set("the a an and or of to in on for with is was it this that i my me we you your as at be are have has had so from by they them its were been can will would could one if when then than also get got just very am do does did".split())

lemas = json.loads((OUT / 'lemas_cliente_v4.json').read_text(encoding='utf-8'))


def limpiar(t, vacias=True, lematizar=True):
    w = [x.strip("'") for x in re.findall(r"[a-z']+", t.lower().replace('’', "'"))]
    return ' '.join((lemas.get(x, x) if lematizar else x) for x in w if x and not (vacias and x in VACIAS))


def modelo(k, min_df=5):
    return make_pipeline(TfidfVectorizer(min_df=min_df, ngram_range=(1, 2)), KNeighborsClassifier(n_neighbors=k, metric='cosine'))


def medidas(nombre, y, p):
    vn, fp, fn, vp = confusion_matrix(y, p > 0).ravel()
    return {'modelo': nombre, 'exactitud': (vp + vn) / len(y), 'positivas_ok': vp / (vp + fn), 'negativas_ok': vn / (vn + fp),
            'auc': roc_auc_score(y, p), 'errores': int(fp + fn), 'neg': f'{vn}/{vn+fp}', 'pos': f'{vp}/{vp+fn}'}


rev = dc.cargar(dc.XLSX)
for r in rev:
    r['txt'] = r['titulo'] + '. ' + r['texto']; r['limpio'] = limpiar(r['txt'])
pol = [r for r in rev if r['estrellas'] != 3]
y = np.array([1 if r['estrellas'] >= 4 else 0 for r in pol])
X = np.array([r['limpio'] for r in pol]); idx = np.arange(len(pol))
itr, ite = train_test_split(idx, test_size=0.20, random_state=42, stratify=y)
corte = y[itr].mean()
md = ['# KNN sobre las reseñas de Amazon (método de la Clase 12, EAFIT)', '',
      f'Fuente: Excel v4, {len(rev)} reseñas con texto; 4-5★ = positiva, 1-2★ = negativa, 3★ = tibia (fuera de entrenamiento). Entrenamiento {len(itr)} · prueba {len(ite)} · positivas en entrenamiento {corte*100:.1f} % (= punto de corte). Texto lematizado (spaCy en_core_web_sm) y sin palabras vacías, conservando no/not/never.', '']
# 1) k por validacion cruzada
cv = StratifiedKFold(5, shuffle=True, random_state=42)
ks = [1, 5, 15, 25, 51, 101, 201, 401]
aucs = {k: cross_val_score(modelo(k), X[itr], y[itr], cv=cv, scoring='roc_auc').mean() for k in ks}
mk = max(aucs, key=aucs.get)
md += ['## 1. ¿Cuántos vecinos?', '', '| k | ' + ' | '.join(map(str, ks)) + ' |', '|---|' + '---|' * len(ks),
       '| AUC (CV 5) | ' + ' | '.join(f'{aucs[k]:.3f}' for k in ks) + f' |', '', f'Mejor k = **{mk}**.', '']
# 2) prueba
knn = modelo(mk).fit(X[itr], y[itr])
pp = knn.predict_proba(X[ite])[:, 1]
filas = [medidas('Regla ingenua (todas positivas)', y[ite], np.ones(len(ite))), medidas('KNN, corte 0.5', y[ite], pp - 0.5),
         medidas(f'KNN, corte {corte:.3f}', y[ite], pp - corte)]
# balanza aprendida (lexico_cliente.py) con la misma particion
spec2 = importlib.util.spec_from_file_location('lx', TOOLS / 'lexico_cliente.py'); lx = importlib.util.module_from_spec(spec2); sys.modules['lx'] = lx; spec2.loader.exec_module(lx)
lex = lx.aprender([pol[i] for i in itr]); sb = np.array([lx.puntaje(pol[i]['txt'], lex) for i in ite], dtype=float)
filas.append(medidas('Balanza aprendida (lexico_cliente.py)', y[ite], sb))
md += ['## 2. ¿Qué tan bien lee? (reseñas de prueba con la nota tapada)', '', '| Modelo | Exactitud | Positivas reconocidas | Negativas reconocidas | AUC | Errores |', '|---|---|---|---|---|---|']
for f in filas:
    md.append(f"| {f['modelo']} | {f['exactitud']:.3f} | {f['pos']} ({f['positivas_ok']:.2f}) | {f['neg']} ({f['negativas_ok']:.2f}) | {f['auc']:.3f} | {f['errores']} |")
md.append('')
# 3) deciles de quejas
o = np.argsort(pp, kind='stable'); neg = (y[ite][o] == 0)
dec = np.arange(len(o)) * 10 // len(o) + 1
base = neg.mean() * 100
md += ['## 3. ¿Cuáles son quejas? (leer primero las de arriba)', '', f'Al azar, {base:.1f} % de las reseñas de prueba es queja.', '', '| Decil | Reseñas | Quejas | % queja | Elevación | % de todas las quejas (acum.) |', '|---|---|---|---|---|---|']
acum = 0
for d in range(1, 11):
    m = dec == d; n = int(neg[m].sum()); acum += n
    md.append(f'| {d} | {int(m.sum())} | {n} | {n/m.sum()*100:.0f} % | {n/m.sum()*100/base:.2f} | {acum/neg.sum()*100:.0f} % |')
md.append('')
# 4) salida: probabilidad fuera de muestra para todas las resenas con texto
pf = np.zeros(len(pol))
pf[ite] = pp
pf[itr] = cross_val_predict(modelo(mk), X[itr], y[itr], cv=cv, method='predict_proba')[:, 1]
tib = [r for r in rev if r['estrellas'] == 3]
pt = knn.predict_proba(np.array([r['limpio'] for r in tib]))[:, 1]
filas_csv = [(r['id'], r['estrellas'], r['genero'], round(float(p), 3), 'positiva' if p > corte else 'negativa', 'prueba' if i in set(ite) else 'entrenamiento (fuera de muestra)', r['txt'])
             for i, (r, p) in enumerate(zip(pol, pf))]
filas_csv += [(r['id'], 3, r['genero'], round(float(p), 3), 'positiva' if p > corte else 'negativa', 'tibia', r['txt']) for r, p in zip(tib, pt)]
filas_csv.sort(key=lambda f: f[3])
with (OUT / 'knn_resenas_v4.csv').open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f); w.writerow(['id', 'estrellas', 'genero_estimado', 'prob_positiva', 'lectura_knn', 'origen', 'texto']); w.writerows(filas_csv)
# 5) tibias: cuantas lee como positivas / negativas, y vecinos de ejemplo
md += ['## 4. Las reseñas de 3 estrellas (tibias), leídas por KNN', '', f'De {len(tib)} reseñas de 3★: {int((pt > corte).sum())} se leen positivas y {int((pt <= corte).sum())} negativas.', '']
# 6) explicar: 3 vecinos de 3 quejas de prueba mal leidas y 2 bien leidas
def vecinos(i):
    t = knn[0].transform([X[i]]); d, pos = knn[1].kneighbors(t, n_neighbors=3)
    return [(1 - dd, itr[p]) for dd, p in zip(d[0], pos[0])]
mal = [j for j, i in enumerate(ite) if (pp[j] > corte) != (y[i] == 1) and y[i] == 0][:3]
bien = [j for j, i in enumerate(ite) if (pp[j] <= corte) and y[i] == 0][:2]
md += ['## 5. Dime con quién andas (ejemplos con vecinos)', '']
for etq, lst in (('Queja bien leída', bien), ('Queja que KNN leyó como positiva (error)', mal)):
    for j in lst:
        i = ite[j]; r = pol[i]
        md += [f"**{etq}** · `{r['id']}` · {r['estrellas']}★ · prob. positiva {pp[j]:.2f} (corte {corte:.2f}) — «{r['txt'][:300]}»", '']
        for par, v in vecinos(i):
            rv = pol[v]; md.append(f"- parecido {par:.2f} · {rv['estrellas']}★ · `{rv['id']}` — «{rv['txt'][:160]}»")
        md.append('')
md += ['## Cómo usarlo', '', '- `knn_resenas_v4.csv` ordena las 1,271 reseñas de más negativa a más positiva (probabilidad fuera de muestra; las de entrenamiento se leen por validación cruzada, sin ver su propia nota). Sirve para leer primero las quejas.',
       '- Probabilidad de positiva = parte de los k vecinos que es 4-5★. El corte es la proporción de positivas del entrenamiento, no 0.5.',
       '- Cuidado: hay una sola marca/producto, así que KNN puede reconocer el tema (plástico, sello, sabor) y no solo la opinión; no hay prueba por producto como en la Clase 12.', '']
(OUT / 'knn_resenas_v4.md').write_text('\n'.join(md), encoding='utf-8')
print('\n'.join(md[:60]))
