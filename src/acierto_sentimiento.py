#!/usr/bin/env python3
"""Acierto del sentimiento frente a una muestra etiquetada A MANO (requisito del Trabajo Final, EAFIT).

Compara contra las etiquetas manuales (columna sentimiento_manual de la hoja de Excel):
  1. Lexico del proyecto (data/lexico_cliente_v4.json), tal como esta publicado.
  2. Lexico reaprendido SIN las resenas etiquetadas (descarta que el lexico "haya visto" la muestra).
  3. KNN entrenado con las ESTRELLAS (4-5 = positiva, 1-2 = negativa) de las demas resenas, como en knn_resenas.py.
  4. KNN reentrenado con las ETIQUETAS MANUALES (solo con el 80 % de la muestra).
Reporta: matriz de confusion, exactitud, sensibilidad, especificidad, precision, F1, AUC, y la evolucion por semestre.

Uso:  .venv/bin/python -I src/acierto_sentimiento.py [--hoja HOJA.xlsx [HOJA2.xlsx ...]] [--salida RESULTADO.md]
Por defecto lee data/etiquetado_manual_100.xlsx y escribe data/acierto_sentimiento.md.
"""
import argparse, importlib.util, itertools, json, math, re, sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from openpyxl import load_workbook
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import adjusted_rand_score, confusion_matrix, roc_auc_score, silhouette_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer

SRC = Path(__file__).resolve().parent
DATA = SRC.parent / 'data'
SEMILLA = 42            # misma semilla fija que knn_resenas.py y lexico_cliente.py
PRUEBA = 0.20           # particion 80/20
FOLDS = 5               # validacion cruzada para elegir k
ALFAS = [0.1, 0.3, 1.0, 3.0]   # valores de alfa (suavizado) candidatos para Naive Bayes
KS = [1, 3, 5, 7, 9, 11, 15, 21, 25, 31, 41, 51, 101]   # valores de k candidatos (el parametro principal del KNN)
# Aliases aceptados al leer la hoja -> etiqueta canonica (el CSV viejo usa "Neutral").
ALIAS = {'positivo': 'Positivo', 'negativo': 'Negativo', 'neutro': 'Neutro', 'neutral': 'Neutro'}


def cargar_modulo(nombre):
    """Importa un script hermano de src/ por ruta (src/ no es paquete y `python -I` no lo agrega al path)."""
    spec = importlib.util.spec_from_file_location(nombre, SRC / (nombre + '.py'))
    mod = importlib.util.module_from_spec(spec); sys.modules[nombre] = mod; spec.loader.exec_module(mod)
    return mod


dc = cargar_modulo('diccionario_cliente')   # cargar() lee el Excel v4 (id, estrellas, texto, fecha)
lx = cargar_modulo('lexico_cliente')        # aprender() / puntaje() / VACIAS: la "balanza" de palabras
he = cargar_modulo('hoja_etiquetado')       # semestre() y fechas_por_id()


# ----------------------------------------------------------------------------------------------
# 1) Lectura de la hoja etiquetada
# ----------------------------------------------------------------------------------------------
# Textos de la interfaz de Amazon que quedaron pegados en algunas reseñas de las hojas (no los escribio el comprador).
RUIDO_UI = re.compile(r'No se pudo cargar el archivo multimedia\.?|Haz clic para reproducir el video', re.I)


def sin_ruido(txt):
    """Quita los avisos de la interfaz de Amazon y los espacios sobrantes de un texto."""
    return re.sub(r'\s+', ' ', RUIDO_UI.sub(' ', txt or '')).strip()


def leer_hojas(rutas):
    """Lee una o varias hojas .xlsx etiquetadas. Devuelve (filas, pendientes): filas con sentimiento valido y
    la lista de ids sin etiquetar o con valor invalido (para avisar en vez de evaluar a medias en silencio)."""
    filas, pendientes, vistos = [], [], set()
    for ruta in rutas:
        ws = load_workbook(ruta, data_only=True)['Etiquetado']
        cab = [c.value for c in ws[1]]
        for v in ws.iter_rows(min_row=2, values_only=True):
            r = dict(zip(cab, v))
            if not r.get('id') or r['id'] in vistos:
                continue
            vistos.add(r['id'])
            etq = ALIAS.get(str(r.get('sentimiento_manual') or '').strip().lower())
            if etq is None:
                pendientes.append(r['id']); continue
            filas.append({'id': r['id'], 'titulo': sin_ruido(r.get('titulo')), 'texto': sin_ruido(r.get('texto')), 'manual': etq})
    return filas, pendientes


def hojas_etiquetadas():
    """La hoja de 100 (obligatoria) + las hojas de ampliacion SOLO si estan etiquetadas por completo.
    Devuelve (filas, nombres_usadas, avisos)."""
    hojas, avisos = [DATA / 'etiquetado_manual_100.xlsx'], []
    for extra in ('etiquetado_manual_ampliacion_200.xlsx', 'etiquetado_manual_soursop_200.xlsx'):
        f_extra, pend = leer_hojas([DATA / extra])
        if f_extra and not pend:
            hojas.append(DATA / extra)
        else:
            avisos.append(f'(se omite {extra}: {len(pend)} reseñas sin etiquetar)')
    filas, pendientes = leer_hojas(hojas)
    assert not pendientes, f'Faltan {len(pendientes)} reseñas por etiquetar'
    poner_fechas(filas)
    return filas, [h.name for h in hojas], avisos


def poner_fechas(filas):
    """Agrega fecha y semestre a cada fila (la hoja no la muestra); las que no se encuentren quedan sin semestre."""
    fechas = he.fechas_por_id()
    for r in filas:
        r['fecha'] = fechas.get(r['id'])
        r['semestre'] = he.semestre(r['fecha']) if r['fecha'] else None


# ----------------------------------------------------------------------------------------------
# 2) Limpieza de texto y modelos
# ----------------------------------------------------------------------------------------------
LEMAS = json.loads((DATA / 'lemas_cliente_v4.json').read_text(encoding='utf-8'))


def limpiar(texto):
    """Mismo preprocesado que knn_resenas.py: minusculas, solo letras, lematiza y quita palabras vacias
    (conserva no/not/never porque cambian el sentido)."""
    w = [x.strip("'") for x in lx.palabras(texto)]
    return ' '.join(LEMAS.get(x, x) for x in w if x and x not in lx.VACIAS)


def modelo_knn(k, min_df):
    """TF-IDF (palabras y parejas) + KNN con distancia coseno, como en la Clase 12. min_df=2 porque con ~80
    textos de entrenamiento un minimo de 5 (usado con 937) dejaria casi sin vocabulario."""
    return make_pipeline(TfidfVectorizer(min_df=min_df, ngram_range=(1, 2)),
                         KNeighborsClassifier(n_neighbors=k, metric='cosine'))


def elegir_k(X, y, min_df, semilla=SEMILLA, folds=FOLDS):
    """Elige k por validacion cruzada estratificada SOLO con los datos de entrenamiento (el criterio es el AUC).
    Devuelve (mejor_k, {k: auc}). Descarta ks mayores que el tamano de entrenamiento de cada pliegue."""
    folds = min(folds, int(np.bincount(y).min()))   # cada pliegue necesita al menos 1 de cada clase
    if folds < 2:
        raise SystemExit('Hay menos de 2 resenas en una de las clases: no se puede validar cruzado.')
    cv = StratifiedKFold(folds, shuffle=True, random_state=semilla)
    tope = len(y) - math.ceil(len(y) / folds)       # resenas de entrenamiento en un pliegue
    ks = [k for k in KS if k <= tope] or [1]
    aucs = {k: float(cross_val_score(modelo_knn(k, min_df), X, y, cv=cv, scoring='roc_auc').mean()) for k in ks}
    return max(aucs, key=aucs.get), aucs


def modelo_nb(alfa, min_df):
    """TF-IDF (palabras y parejas) + Naive Bayes multinomial; alfa = suavizado (parametro principal)."""
    return make_pipeline(TfidfVectorizer(min_df=min_df, ngram_range=(1, 2)), MultinomialNB(alpha=alfa))


def elegir_alfa(X, y, min_df, semilla=SEMILLA, folds=FOLDS):
    """Elige alfa por validacion cruzada estratificada SOLO con el entrenamiento (criterio: AUC). Devuelve (alfa, {alfa: auc})."""
    cv = StratifiedKFold(folds, shuffle=True, random_state=semilla)
    aucs = {a: float(cross_val_score(modelo_nb(a, min_df), X, y, cv=cv, scoring='roc_auc').mean()) for a in ALFAS}
    return max(aucs, key=aucs.get), aucs


# ----------------------------------------------------------------------------------------------
# 3) Metricas
# ----------------------------------------------------------------------------------------------
def wilson(aciertos, n, z=1.96):
    """Intervalo de confianza 95 % (Wilson) de una proporcion: muestra cuanta incertidumbre deja el tamano de la muestra."""
    if n == 0:
        return (float('nan'), float('nan'))
    p = aciertos / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def metricas(y, puntaje, corte=0.0):
    """Metricas binarias con Positivo = 1. Prediccion positiva si puntaje > corte.
    sensibilidad = VP/(VP+FN); especificidad = VN/(VN+FP); precision = VP/(VP+FP); F1 = media armonica de precision y sensibilidad;
    AUC se calcula con el puntaje continuo (None si solo hay una clase)."""
    y = np.asarray(y); p = (np.asarray(puntaje, dtype=float) > corte).astype(int)
    vn, fp, fn, vp = confusion_matrix(y, p, labels=[0, 1]).ravel()
    div = lambda a, b: a / b if b else float('nan')
    sens, prec = div(vp, vp + fn), div(vp, vp + fp)
    return {'n': len(y), 'vn': int(vn), 'fp': int(fp), 'fn': int(fn), 'vp': int(vp),
            'exactitud': (vp + vn) / len(y), 'sensibilidad': sens, 'especificidad': div(vn, vn + fp), 'precision': prec,
            'f1': div(2 * prec * sens, prec + sens) if prec == prec and sens == sens else float('nan'),
            'auc': float(roc_auc_score(y, puntaje)) if len(set(y.tolist())) == 2 else None}


def matriz_3(manual, lectura):
    """Matriz de confusion de 3 clases (filas = etiqueta manual, columnas = lectura del modelo)."""
    etq = ['Negativo', 'Neutro', 'Positivo']
    return etq, confusion_matrix(manual, lectura, labels=etq)


def lectura_lexico(puntaje):
    """Misma regla que lexico_cliente.py puntuar: >0 positiva, <0 negativa, 0 neutra."""
    return 'Positivo' if puntaje > 0 else ('Negativo' if puntaje < 0 else 'Neutro')


# ----------------------------------------------------------------------------------------------
# 4) Calculo principal (sin imprimir: lo usan la linea de comandos y las pruebas)
# ----------------------------------------------------------------------------------------------
def evaluar(filas, corpus, semilla=SEMILLA, min_df=2):
    """filas: resenas etiquetadas a mano. corpus: todas las resenas del Excel v4 (con estrellas), para el lexico y el KNN-estrellas.
    Binario = Positivo vs Negativo (las Neutro manuales se excluyen del KNN y de las metricas binarias, igual que
    las 3 estrellas en knn_resenas.py), pero la matriz de 3 clases del lexico si las incluye."""
    ids = {r['id'] for r in filas}
    for r in filas:
        r['txt'] = r['titulo'] + '. ' + r['texto']; r['limpio'] = limpiar(r['txt'])
    manual = np.array([r['manual'] for r in filas])
    # Particion 80/20 estratificada por la etiqueta manual, semilla fija.
    idx = np.arange(len(filas))
    conteo = Counter(manual.tolist())
    estratificar = manual if min(conteo.values()) >= 2 else None   # una clase con 1 sola resena no se puede estratificar
    itr, ite = train_test_split(idx, test_size=PRUEBA, random_state=semilla, stratify=estratificar)
    # --- Lexicos ---
    ruta_lex = DATA / 'lexico_cliente_v4.json'
    d = json.loads(ruta_lex.read_text(encoding='utf-8'))
    lex_proy = {**{x: 2 for x in d['positivas']}, **{x: -2 for x in d['negativas']}}
    sin_muestra = [r for r in corpus if r['id'] not in ids and r['estrellas'] != 3]   # entrenamiento del lexico y del KNN-estrellas
    lex_nuevo = lx.aprender(sin_muestra)
    punt = {'Lexico del proyecto': np.array([lx.puntaje(r['txt'], lex_proy) for r in filas], dtype=float),
            'Lexico sin la muestra': np.array([lx.puntaje(r['txt'], lex_nuevo) for r in filas], dtype=float)}
    # --- KNN con estrellas (no ve ninguna resena etiquetada) ---
    Xe = np.array([limpiar(r['titulo'] + '. ' + r['texto']) for r in sin_muestra])
    ye = np.array([1 if r['estrellas'] >= 4 else 0 for r in sin_muestra])
    k_est, aucs_est = elegir_k(Xe, ye, min_df=5, semilla=semilla)   # corpus grande: min_df=5 como knn_resenas.py
    knn_est = modelo_knn(k_est, 5).fit(Xe, ye)
    corte_est = ye.mean()                                           # corte = proporcion de positivas del entrenamiento
    punt['KNN con estrellas'] = knn_est.predict_proba(np.array([r['limpio'] for r in filas]))[:, 1] - corte_est
    # --- Naive Bayes con estrellas (misma base de entrenamiento y mismo texto limpio que el KNN con estrellas) ---
    alfa_nb, aucs_nb = elegir_alfa(Xe, ye, min_df=5, semilla=semilla)
    nb_est = modelo_nb(alfa_nb, 5).fit(Xe, ye)
    punt['Naive Bayes con estrellas'] = nb_est.predict_proba(np.array([r['limpio'] for r in filas]))[:, 1] - corte_est
    # --- KNN con etiquetas manuales: SOLO entrena con el 80 % de la muestra (sin Neutro) ---
    bin_ok = manual != 'Neutro'
    yb = (manual == 'Positivo').astype(int)
    X = np.array([r['limpio'] for r in filas])
    tr_b = np.array([i for i in itr if bin_ok[i]]); te_b = np.array([i for i in ite if bin_ok[i]])
    k_man, aucs_man = elegir_k(X[tr_b], yb[tr_b], min_df=min_df, semilla=semilla)
    knn_man = modelo_knn(k_man, min_df).fit(X[tr_b], yb[tr_b])
    corte_man = yb[tr_b].mean()
    p_man = np.full(len(filas), np.nan)
    p_man[te_b] = knn_man.predict_proba(X[te_b])[:, 1] - corte_man   # solo hay prediccion honesta fuera del entrenamiento
    # --- Tablas de metricas ---
    prueba = {n: metricas(yb[te_b], s[te_b]) for n, s in punt.items()}
    prueba['KNN con etiquetas manuales'] = metricas(yb[te_b], p_man[te_b])
    todas = {n: metricas(yb[bin_ok], s[bin_ok]) for n, s in punt.items()}   # modelos que no entrenan con la muestra
    # --- Matriz de 3 clases del lexico del proyecto sobre toda la muestra ---
    lect3 = [lectura_lexico(s) for s in punt['Lexico del proyecto']]
    etq3, m3 = matriz_3(manual, lect3)
    # --- Evolucion por semestre ---
    evol = evolucion(filas, manual, punt['Lexico del proyecto'])
    evol_corpus = evolucion_corpus(corpus, lex_proy)
    return {'n': len(filas), 'conteo': dict(conteo), 'n_train': len(itr), 'n_test': len(ite), 'n_test_bin': len(te_b),
            'k_manual': k_man, 'aucs_manual': aucs_man, 'corte_manual': float(corte_man),
            'k_estrellas': k_est, 'aucs_estrellas': aucs_est, 'alfa_nb': alfa_nb, 'aucs_nb': aucs_nb, 'n_corpus_train': len(sin_muestra),
            'prueba': prueba, 'todas': todas, 'etq3': etq3, 'm3': m3, 'evol': evol, 'evol_corpus': evol_corpus,
            'punt': punt, 'y_bin': yb, 'bin_ok': bin_ok}


def evaluar_estrellas(corpus, semilla=SEMILLA):
    """Clasificacion con la NOTA como etiqueta (4-5 = positivo, 1-2 = negativo; las de 3 estrellas quedan fuera) sobre TODO el
    corpus: particion 80/20 estratificada con semilla fija; k (KNN) y alfa (Naive Bayes) por validacion cruzada SOLO en el 80 %.
    El lexico del proyecto se mide en las mismas reseñas de prueba. Devuelve el 'prueba' (dict modelo -> metricas) y los parametros."""
    util = [r for r in corpus if r['estrellas'] != 3]
    X = np.array([limpiar(r['titulo'] + '. ' + r['texto']) for r in util])
    y = np.array([1 if r['estrellas'] >= 4 else 0 for r in util])
    itr, ite = train_test_split(np.arange(len(util)), test_size=PRUEBA, random_state=semilla, stratify=y)
    k, aucs_k = elegir_k(X[itr], y[itr], min_df=5, semilla=semilla)
    a, aucs_a = elegir_alfa(X[itr], y[itr], min_df=5, semilla=semilla)
    corte = y[itr].mean()
    knn = modelo_knn(k, 5).fit(X[itr], y[itr]); nb = modelo_nb(a, 5).fit(X[itr], y[itr])
    # El lexico publicado se aprendio con TODO el corpus (habria visto la prueba), asi que aqui se reaprende solo con el 80 %.
    lex = lx.aprender([util[i] for i in itr])
    p_lex = np.array([lx.puntaje(util[i]['titulo'] + '. ' + util[i]['texto'], lex) for i in ite], dtype=float)
    prueba = {'Lexico (aprendido con el 80 %)': metricas(y[ite], p_lex),
              'KNN': metricas(y[ite], knn.predict_proba(X[ite])[:, 1] - corte),
              'Naive Bayes': metricas(y[ite], nb.predict_proba(X[ite])[:, 1] - corte)}
    punt = {'Lexico (aprendido con el 80 %)': p_lex, 'KNN': knn.predict_proba(X[ite])[:, 1] - corte, 'Naive Bayes': nb.predict_proba(X[ite])[:, 1] - corte}
    return {'n': len(util), 'n_train': len(itr), 'n_test': len(ite), 'k': k, 'aucs_k': aucs_k, 'alfa': a, 'aucs_alfa': aucs_a,
            'corte': float(corte), 'pos_test': int(y[ite].sum()), 'prueba': prueba, 'punt': punt, 'y_test': y[ite]}


# Temas de queja que se vigilan por semestre (palabras clave en ingles; cuentan reseñas que MENCIONAN el tema, no prueban su causa).
TEMAS = {'Producto roto o derrame': r'broken|leak|damag|spill|shatter|crack|arrived open|came open|soaked',
         'Cambio a botella de plastico': r"plastic (?:bottle|container|jar)|(?:from|to|changed|switch\w*|now) (?:\w+ ){0,3}plastic|used to (?:be|come) in glass",
         'Sabor': r'tast|flavor|bitter',
         'Cambio de formula o producto': r"formula|different|changed|change from|used to|not the same|switch",
         'Envio o servicio': r'ship|deliver|arriv|customer service|never received|late',
         'Efecto laxante': r'laxativ|diarrh|bathroom|poop|bowel',
         'No funciona': r"didn'?t work|no (?:difference|change|effect)|nothing happened|waste|scam",
         'Formula aguada o diluida': r"watered|watery|thinner|diluted (?:version|formula)|formula (?:has )?(?:been )?(?:changed|watered)|changed (?:the|their) formula|different formula|new formula"}


def temas_por_semestre(corpus):
    """Por semestre: n, promedio de estrellas y % de las reseñas que mencionan cada tema (todas y solo 1-2 estrellas)."""
    por = defaultdict(list)
    for r in corpus:
        por[he.semestre(r['fecha'])].append(r)
    out = []
    for sem in sorted(por):
        rs = por[sem]; bajas = [r for r in rs if r['estrellas'] <= 2]
        fila = {'semestre': sem, 'n': len(rs), 'estrellas_prom': sum(r['estrellas'] for r in rs) / len(rs), 'n_1_2': len(bajas)}
        for tema, pat in TEMAS.items():
            hit = lambda r: re.search(pat, (r['titulo'] + ' ' + r['texto']).lower())
            fila[tema] = sum(1 for r in rs if hit(r)) / len(rs)
            fila[tema + ' (1-2★)'] = sum(1 for r in bajas if hit(r)) / len(bajas) if bajas else float('nan')
        out.append(fila)
    return out


def mensual(corpus, lex):
    """Por mes: n, % de 4-5 estrellas y % positivo segun el lexico (la 'tabla de mando' mensual del ejemplo de uso)."""
    por = defaultdict(list)
    for r in corpus:
        por[r['fecha'][:7]].append(r)
    return [{'mes': m, 'n': len(rs), 'estrellas_pos': sum(1 for r in rs if r['estrellas'] >= 4) / len(rs),
             'lexico_pos': sum(1 for r in rs if lx.puntaje(r['titulo'] + '. ' + r['texto'], lex) > 0) / len(rs)}
            for m, rs in sorted(por.items()) for rs in [rs]]


def acuerdo_estrellas(filas, corpus):
    """En la muestra manual (sin Neutro ni 3 estrellas): cuantas veces la nota (4-5 = positivo, 1-2 = negativo) coincide con
    la etiqueta manual. Devuelve (coinciden, total_comparadas, excluidas)."""
    est = {r['id']: r['estrellas'] for r in corpus}
    ok = tot = 0
    for f in filas:
        e = est.get(f['id'])
        if e is None or e == 3 or f['manual'] == 'Neutro':
            continue
        tot += 1; ok += int((e >= 4) == (f['manual'] == 'Positivo'))
    return ok, tot, len(filas) - tot


def alertas(mens, caida=0.10, n_min=30, previos=3):
    """Regla de semaforo del ejemplo de uso: un mes se marca si su % positivo (lexico) cae `caida` o mas frente al promedio
    de los `previos` meses anteriores y tiene al menos `n_min` reseñas."""
    out = []
    for i, m in enumerate(mens):
        if i < previos or m['n'] < n_min:
            continue
        ref = sum(x['lexico_pos'] for x in mens[i - previos:i]) / previos
        if ref - m['lexico_pos'] >= caida:
            out.append({'mes': m['mes'], 'n': m['n'], 'lexico_pos': m['lexico_pos'], 'referencia': ref})
    return out


def backtest_alertas(mens, caidas=(0.05, 0.10, 0.15, 0.20), n_mins=(30, 50), previos=3, caida_real=0.10):
    """Prueba hacia atras de la regla del semaforo. 'Evento real' = el % de 4-5 estrellas (NO el lexico) cae `caida_real` o mas
    frente al promedio de los `previos` meses anteriores con al menos n_min reseñas. Para cada (caida, n_min) cuenta alertas del lexico,
    aciertos (alerta en un mes con evento), falsas alarmas (alerta sin evento) y eventos perdidos. Es una prueba sobre los mismos meses
    de los que salio la regla: sirve para comparar umbrales, no para prometer un desempeño futuro."""
    filas = []
    for n_min in n_mins:
        ev = set()
        for i, m in enumerate(mens):
            if i < previos or m['n'] < n_min:
                continue
            if sum(x['estrellas_pos'] for x in mens[i - previos:i]) / previos - m['estrellas_pos'] >= caida_real:
                ev.add(m['mes'])
        evaluables = sum(1 for i, m in enumerate(mens) if i >= previos and m['n'] >= n_min)
        for caida in caidas:
            al = {a['mes'] for a in alertas(mens, caida, n_min, previos)}
            filas.append({'caida': caida, 'n_min': n_min, 'meses_evaluables': evaluables, 'eventos': len(ev), 'alertas': len(al),
                          'aciertos': len(al & ev), 'falsas_alarmas': len(al - ev), 'perdidos': len(ev - al),
                          'meses_alerta': ', '.join(sorted(al)), 'meses_falsas': ', '.join(sorted(al - ev)),
                          'meses_perdidos': ', '.join(sorted(ev - al))})
    return filas


def agrupar(filas, k_min=2, k_max=8, semilla=SEMILLA, n_comp=30, n_init=50, n_semillas=5, min_df=5):
    """Agrupamiento (k-means) de las reseñas por su TEXTO. filas: dicts con 'titulo' y 'texto'.
    Preparacion: mismo texto limpio del KNN -> TF-IDF (palabras y parejas, min_df=5) -> SVD a `n_comp` dimensiones (resume ~1.400 columnas
    casi vacias en 30 ejes de temas) -> normalizado, para que k-means (distancia euclidiana) equivalga a agrupar por coseno.
    Numero de grupos: para cada k de k_min a k_max se mide la inercia (codo), la silueta con distancia coseno y la ESTABILIDAD (indice de Rand
    ajustado medio entre `n_semillas` semillas distintas: 1 = siempre los mismos grupos). Regla: el primer k >= 3 cuya silueta supera a la de sus
    dos vecinos (maximo local) y cuya estabilidad es >= 0,9. No hay particion entrenamiento/prueba: no hay etiqueta que predecir, y los grupos
    se juzgan con variables que NO entraron al modelo (estrellas, semestre, compra verificada)."""
    textos = [limpiar(f['titulo'] + '. ' + f['texto']) for f in filas]
    vec = TfidfVectorizer(min_df=min_df, ngram_range=(1, 2)); X = vec.fit_transform(textos)
    Z = Normalizer().fit_transform(TruncatedSVD(n_comp, random_state=semilla).fit_transform(X))
    tabla = []
    for k in range(k_min, k_max + 1):
        labs = [KMeans(k, n_init=n_init, random_state=semilla + i).fit(Z) for i in range(n_semillas)]
        L = [m.labels_ for m in labs]
        tabla.append({'k': k, 'inercia': float(labs[0].inertia_),
                      'silueta': float(np.mean([silhouette_score(Z, l, metric='cosine') for l in L])),
                      'estabilidad': float(np.mean([adjusted_rand_score(a, b) for a, b in itertools.combinations(L, 2)])),
                      'tam_min': int(min(np.bincount(L[0])))})
    elegido = next((t['k'] for i, t in enumerate(tabla)
                    if 0 < i < len(tabla) - 1 and t['k'] >= 3 and t['silueta'] > tabla[i - 1]['silueta'] and t['silueta'] >= tabla[i + 1]['silueta']
                    and t['estabilidad'] >= 0.9), None)
    if elegido is None:
        raise ValueError('ningun k cumple la regla de silueta + estabilidad')
    et = KMeans(elegido, n_init=n_init, random_state=semilla).fit(Z).labels_
    terminos = vec.get_feature_names_out()
    top = {g: [str(t) for t in terminos[np.asarray(X[et == g].mean(axis=0)).ravel().argsort()[::-1][:10]]] for g in range(elegido)}
    return {'tabla': tabla, 'k': elegido, 'etiquetas': et, 'top_terminos': top, 'n_comp': n_comp, 'n_columnas': X.shape[1]}


def perfil_grupos(filas, etiquetas):
    """Describe cada grupo con variables que NO entraron al modelo: estrellas, compra verificada y, solo como ayuda de lectura, el % de reseñas
    que mencionan cada tema de TEMAS (esas palabras clave salen del mismo texto, asi que no son una validacion independiente)."""
    out = []
    for g in sorted(set(etiquetas.tolist())):
        rs = [f for f, e in zip(filas, etiquetas) if e == g]
        est = [int(f['estrellas']) for f in rs]
        fila = {'grupo': g, 'n': len(rs), 'pct': len(rs) / len(filas), 'estrellas_prom': sum(est) / len(est),
                'pct_4_5': sum(1 for x in est if x >= 4) / len(est),
                'pct_verificada': sum(1 for f in rs if f.get('compra_verificada') == 'Sí') / len(rs)}
        for tema, pat in TEMAS.items():
            fila[tema] = sum(1 for f in rs if re.search(pat, (f['titulo'] + ' ' + f['texto']).lower())) / len(rs)
        out.append(fila)
    return out


def grupos_por_semestre(filas, etiquetas):
    """Por semestre: n y que parte de las reseñas cae en cada grupo."""
    por = defaultdict(list)
    for f, e in zip(filas, etiquetas):
        por[f['semestre']].append(int(e))
    return [{'semestre': sem, 'n': len(v), **{f'grupo_{g}': v.count(g) / len(v) for g in sorted(set(etiquetas.tolist()))}} for sem, v in sorted(por.items())]


def segunda_lectura(y, p_lex, p_knn, p_nb, costos=(1, 2, 3, 5)):
    """Combina las lecturas de los tres modelos con reglas fijas, declaradas antes de mirar los resultados (sin parametros que ajustar).
    y: 1 = positiva, 0 = negativa. p_*: puntajes ya centrados (> 0 = lo lee como positiva). 'Marca' = la regla lo lee como QUEJA.
    Segunda lectura = el KNN revisa lo que el lexico dejo pasar como positivo (queja si CUALQUIERA de los dos la marca); tercera = se suma Naive Bayes.
    fp = queja leida como elogio (el error caro); fn = elogio leido como queja (falsa alarma). costo(c) = c * fp + fn.
    Devuelve una fila por regla, con % marcadas (la carga de lectura) y el costo para cada razon c."""
    L, K, N = (np.asarray(p, dtype=float) <= 0 for p in (p_lex, p_knn, p_nb))
    reglas = {'Léxico solo': L, 'KNN solo': K, 'Naive Bayes solo': N, 'Léxico O KNN (segunda lectura)': L | K,
              'Léxico O KNN O NB (tercera lectura)': L | K | N, 'Voto 2 de 3': (L.astype(int) + K + N) >= 2,
              'KNN O NB': K | N, 'Léxico Y KNN': L & K}
    y = np.asarray(y); filas = []
    for nombre, marca in reglas.items():
        m = metricas(y, (~marca).astype(float), corte=0.5)
        filas.append({'regla': nombre, 'fp': m['fp'], 'fn': m['fn'], 'especificidad': m['especificidad'], 'sensibilidad': m['sensibilidad'],
                      'exactitud': m['exactitud'], 'pct_marcadas': float(marca.mean()), 'n': m['n'],
                      **{f'costo_c{c}': c * m['fp'] + m['fn'] for c in costos}})
    return filas


def c_equilibrio(filas, regla):
    """Menor razon c desde la cual `regla` cuesta lo mismo o menos que cualquier otra (costo = c * fp + fn), o None si no lo logra a ningun c.
    Contra una regla rival con d_fp = fp_rival - fp_regla y d_fn = fn_rival - fn_regla: si d_fp > 0 hace falta c >= -d_fn / d_fp;
    si d_fp = 0 hace falta d_fn >= 0 (siempre o nunca); si d_fp < 0 la rival gana cuando c es grande, asi que no hay umbral."""
    base = next(f for f in filas if f['regla'] == regla); umbral = 0.0
    for f in filas:
        if f is base:
            continue
        d_fp, d_fn = f['fp'] - base['fp'], f['fn'] - base['fn']
        if d_fp > 0:
            umbral = max(umbral, -d_fn / d_fp)
        elif d_fp < 0 or d_fn < 0:
            return None
    return umbral


def lexico_proyecto():
    """Lexico publicado (data/lexico_cliente_v4.json) en el formato {palabra: peso}."""
    d = json.loads((DATA / 'lexico_cliente_v4.json').read_text(encoding='utf-8'))
    return {**{x: 2 for x in d['positivas']}, **{x: -2 for x in d['negativas']}}


def evolucion(filas, manual, puntaje_lexico):
    """Por semestre: n, % Positivo / Neutro / Negativo segun la etiqueta manual y % que el lexico lee como positivo."""
    por = defaultdict(list)
    for i, r in enumerate(filas):
        por[r['semestre'] or 'sin fecha'].append(i)
    out = []
    for s in sorted(por):
        ii = por[s]; n = len(ii)
        c = Counter(manual[i] for i in ii)
        lp = sum(1 for i in ii if puntaje_lexico[i] > 0)
        out.append({'semestre': s, 'n': n, 'pos': c['Positivo'] / n, 'neu': c['Neutro'] / n, 'neg': c['Negativo'] / n, 'lexico_pos': lp / n})
    return out


def evolucion_corpus(corpus, lex):
    """Mismo calculo sobre TODO el corpus del Excel v4 (sin etiquetas manuales): % de 4-5 estrellas y % que el lexico lee positivo."""
    por = defaultdict(list)
    for r in corpus:
        por[he.semestre(r['fecha'])].append(r)
    out = []
    for s in sorted(por):
        rs = por[s]; n = len(rs)
        out.append({'semestre': s, 'n': n, 'estrellas_pos': sum(1 for r in rs if r['estrellas'] >= 4) / n,
                    'lexico_pos': sum(1 for r in rs if lx.puntaje(r['titulo'] + '. ' + r['texto'], lex) > 0) / n})
    return out


# ----------------------------------------------------------------------------------------------
# 5) Reporte (solo tablas con numeros, sin interpretacion)
# ----------------------------------------------------------------------------------------------
def f(x):
    return 'n/d' if x is None or x != x else f'{x:.3f}'


def tabla_metricas(res):
    enc = ['| Modelo | n | VN | FP | FN | VP | Exactitud (IC 95 %) | Sensibilidad | Especificidad | Precision | F1 | AUC |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for nombre, m in res.items():
        lo, hi = wilson(m['vp'] + m['vn'], m['n'])
        enc.append(f"| {nombre} | {m['n']} | {m['vn']} | {m['fp']} | {m['fn']} | {m['vp']} | {f(m['exactitud'])} ({f(lo)}-{f(hi)}) | "
                   f"{f(m['sensibilidad'])} | {f(m['especificidad'])} | {f(m['precision'])} | {f(m['f1'])} | {f(m['auc'])} |")
    return enc


def reporte(r, hojas):
    md = ['# Acierto del sentimiento frente a etiquetas manuales', '',
          f"Hoja(s): {', '.join(map(str, hojas))}. Etiquetadas: {r['n']} ({', '.join(f'{k} {v}' for k, v in sorted(r['conteo'].items()))}).",
          f"Particion 80/20 estratificada, semilla {SEMILLA}: entrenamiento {r['n_train']}, prueba {r['n_test']} ({r['n_test_bin']} sin Neutro).",
          'Binario = Positivo (clase 1) vs Negativo; las Neutro manuales no entran en las metricas binarias. VN/FP/FN/VP = matriz de confusion.', '',
          '## 1. Conjunto de prueba (20 %): todos los modelos con las mismas resenas', ''] + tabla_metricas(r['prueba']) + ['',
          f"KNN con etiquetas manuales: k = {r['k_manual']} (CV de hasta {FOLDS} pliegues sobre el entrenamiento), corte = {r['corte_manual']:.3f}. "
          f"KNN con estrellas: k = {r['k_estrellas']}, entrenado con {r['n_corpus_train']} resenas del Excel v4 (sin las etiquetadas). "
          f"Naive Bayes con estrellas: alfa = {r['alfa_nb']} (CV de {FOLDS} pliegues, misma base de entrenamiento).", '',
          '| k | ' + ' | '.join(map(str, r['aucs_manual'])) + ' |', '|---|' + '---|' * len(r['aucs_manual']),
          '| AUC (CV), KNN manual | ' + ' | '.join(f(v) for v in r['aucs_manual'].values()) + ' |', '',
          '## 2. Toda la muestra etiquetada (modelos que no se entrenan con ella)', ''] + tabla_metricas(r['todas']) + ['',
          '## 3. Matriz de confusion de 3 clases: lexico del proyecto (filas = manual, columnas = lexico)', '',
          '| manual \\ lexico | ' + ' | '.join(r['etq3']) + ' |', '|---|---|---|---|']
    md += [f'| {e} | ' + ' | '.join(str(int(v)) for v in fila) + ' |' for e, fila in zip(r['etq3'], r['m3'])]
    md += ['', '## 4. Evolucion por semestre (muestra etiquetada)', '',
           '| Semestre | n | % Positivo manual | % Neutro manual | % Negativo manual | % positivo segun lexico |', '|---|---|---|---|---|---|']
    md += [f"| {e['semestre']} | {e['n']} | {e['pos']*100:.0f} % | {e['neu']*100:.0f} % | {e['neg']*100:.0f} % | {e['lexico_pos']*100:.0f} % |" for e in r['evol']]
    md += ['', '## 5. Evolucion por semestre (todo el Excel v4, sin etiquetas manuales)', '',
           '| Semestre | n | % 4-5 estrellas | % positivo segun lexico |', '|---|---|---|---|']
    md += [f"| {e['semestre']} | {e['n']} | {e['estrellas_pos']*100:.0f} % | {e['lexico_pos']*100:.0f} % |" for e in r['evol_corpus']]
    return '\n'.join(md) + '\n'


def main():
    ap = argparse.ArgumentParser(description='Acierto del sentimiento frente a etiquetas manuales')
    ap.add_argument('--hoja', nargs='+', type=Path, default=[DATA / 'etiquetado_manual_100.xlsx'], help='una o varias hojas etiquetadas (p. ej. la de 100 y la ampliacion)')
    ap.add_argument('--salida', type=Path, default=DATA / 'acierto_sentimiento.md')
    ap.add_argument('--min-df', type=int, default=2, help='frecuencia minima de palabras del KNN con etiquetas manuales')
    ap.add_argument('--parcial', action='store_true', help='evalua solo las ya etiquetadas (por defecto exige todas)')
    a = ap.parse_args()
    filas, pendientes = leer_hojas(a.hoja)
    if pendientes and not a.parcial:
        raise SystemExit(f'Faltan {len(pendientes)} resenas sin sentimiento_manual valido (p. ej. {pendientes[:3]}). Termina de etiquetar o usa --parcial.')
    if len(filas) < 20:
        raise SystemExit(f'Solo {len(filas)} etiquetadas: son muy pocas para medir.')
    poner_fechas(filas)
    corpus = dc.cargar(dc.XLSX)
    r = evaluar(filas, corpus, min_df=a.min_df)
    txt = reporte(r, [p.name for p in a.hoja])
    a.salida.write_text(txt, encoding='utf-8')
    print(txt); print('->', a.salida)


if __name__ == '__main__':
    main()
