#!/usr/bin/env python3
"""Genera Trabajo_Final_Resenas.ipynb (notebook de Colab): codigo del analisis + el texto de cada etapa.

El texto de las celdas lleva NUMEROS calculados aqui con las mismas funciones que corre el notebook (src/acierto_sentimiento.py),
asi que si cambian los datos (p. ej. se etiqueta la ampliacion de 200) basta volver a correr este script. Las afirmaciones
cualitativas (quien acierta mas, que patron hay) estan protegidas con `assert`: si el resultado cambia de sentido el script
se detiene y avisa que hay que reescribir ese parrafo en vez de dejar un texto desactualizado.
Lo que solo sabe el equipo (nombres, costos, fechas internas) queda marcado con **[COMPLETAR: ...]**.

Uso: .venv/bin/python -I src/construir_notebook.py   (no requiere jupyter; escribe el JSON del notebook sin salidas;
las salidas se generan ejecutando el notebook, ver src/ejecutar_notebook.py).
"""
import csv, importlib.util, json, re, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CELDAS = []


def md(*lineas):
    CELDAS.append({'cell_type': 'markdown', 'metadata': {}, 'source': '\n'.join(lineas)})


def codigo(texto):
    CELDAS.append({'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [], 'source': texto.strip('\n')})


# ----------------------------------------------------------------------------------------------
# Numeros del analisis (mismas llamadas que hace el notebook)
# ----------------------------------------------------------------------------------------------
spec = importlib.util.spec_from_file_location('acierto_sentimiento', RAIZ / 'src' / 'acierto_sentimiento.py')
ac = importlib.util.module_from_spec(spec); sys.modules['acierto_sentimiento'] = ac; spec.loader.exec_module(ac)

corpus = ac.dc.cargar(ac.dc.XLSX)
filas, hojas_usadas, _avisos = ac.hojas_etiquetadas()
r = ac.evaluar(filas, corpus)
e = ac.evaluar_estrellas(corpus)
evc = r['evol_corpus']; evm = r['evol']
tem = ac.temas_por_semestre(corpus)
mens = ac.mensual(corpus, ac.lexico_proyecto()); alt = ac.alertas(mens)
from openpyxl import load_workbook
_h = list(load_workbook(ac.dc.XLSX, read_only=True)['Reseñas'].iter_rows(values_only=True))
n_sin_texto = sum(1 for v in _h[1:] if any(v) and not (dict(zip(_h[0], v))['Reseña'] or '').strip())
with (RAIZ / 'data' / 'base_preparada_resenas.csv').open(encoding='utf-8', newline='') as fh:
    prep = list(csv.DictReader(fh))


def pc(x):
    return f'{x * 100:.0f} %'


def ic(res, nombre):
    """'0.911 (IC 95 %: 0.867-0.941)' de un modelo en un diccionario de metricas."""
    m = res[nombre]; lo, hi = ac.wilson(m['vp'] + m['vn'], m['n'])
    return f"{m['exactitud']:.3f} (IC 95 %: {lo:.3f}-{hi:.3f})"


def aciertos(res, nombre):
    return res[nombre]['vp'] + res[nombre]['vn']


def verifica(condicion, aviso):
    if not condicion:
        raise SystemExit(f'El resultado cambio de sentido: reescribe el texto de {aviso} antes de regenerar el notebook.')


n_corp = len(corpus)
n_corp_fmt = f'{n_corp:,}'.replace(',', '.')
fechas = sorted(x['fecha'] for x in corpus)
estr = {k: sum(1 for x in corpus if x['estrellas'] == k) for k in range(1, 6)}
n3 = estr[3]; n_pol = n_corp - n3
sem_c = {x['semestre']: x for x in evc}
sem_m = {x['semestre']: x for x in evm}
verif = sum(1 for x in prep if x['compra_verificada'] == 'Sí')
palabras = sorted(len(x['texto'].split()) for x in prep)

# Prueba A: clasificacion con las estrellas (n grande)
pa = e['prueba']; LEX, KNN, NB = 'Lexico (aprendido con el 80 %)', 'KNN', 'Naive Bayes'
verifica(pa[KNN]['exactitud'] > pa[LEX]['exactitud'] and pa[NB]['exactitud'] > pa[LEX]['exactitud'], '§4.1 (KNN/NB ya no superan al léxico)')
verifica(abs(aciertos(pa, KNN) - aciertos(pa, NB)) <= 3, '§4.1 (KNN y NB ya no son equivalentes)')
verifica(pa[KNN]['fp'] < pa[LEX]['fp'], '§4.1 (el léxico ya no deja pasar más quejas)')
dif_kn = abs(aciertos(pa, KNN) - aciertos(pa, NB))
brecha = (pa[KNN]['exactitud'] - pa[LEX]['exactitud']) * 100
lo_k = ac.wilson(aciertos(pa, KNN), pa[KNN]['n'])[0]; hi_l = ac.wilson(aciertos(pa, LEX), pa[LEX]['n'])[1]
# Prueba B: muestra manual (n chico)
pb = r['prueba']
verifica(max(m['exactitud'] for m in pb.values()) - min(m['exactitud'] for m in pb.values()) <= 0.12 and r['n_test_bin'] <= 40,
         '§4.2 (la prueba manual ya no es tan chica o los modelos se separan)')
tb = r['todas']
_LB, _KB, _NB_ = 'Lexico del proyecto', 'KNN con estrellas', 'Naive Bayes con estrellas'
_neg_b = tb[_LB]['vn'] + tb[_LB]['fp']
verifica(tb[_LB]['fp'] <= tb[_KB]['fp'] and pa[KNN]['fp'] < pa[LEX]['fp'], '§5 recomendación 2 (las pruebas A y B ya no apuntan en sentidos opuestos)')
# Segunda lectura: reglas fijas que combinan lexico, KNN y Naive Bayes sobre las MISMAS reseñas de prueba de A y de B
_okb = r['bin_ok']; _pb = r['punt']
sl_a = ac.segunda_lectura(e['y_test'], e['punt'][LEX], e['punt'][KNN], e['punt'][NB])
sl_b = ac.segunda_lectura(r['y_bin'][_okb], _pb['Lexico sin la muestra'][_okb], _pb['KNN con estrellas'][_okb], _pb['Naive Bayes con estrellas'][_okb])
def _fila(sl, nombre): return next(f for f in sl if f['regla'].startswith(nombre))
sa_lex, sa_2, sa_3, sa_voto = (_fila(sl_a, n) for n in ('Léxico solo', 'Léxico O KNN', 'Léxico O KNN O NB', 'Voto'))
sb_lex, sb_2, sb_3 = (_fila(sl_b, n) for n in ('Léxico solo', 'Léxico O KNN', 'Léxico O KNN O NB'))
verifica(sa_2['fp'] < sa_lex['fp'] and sb_2['fp'] <= sb_lex['fp'] and sa_2['fn'] - sa_lex['fn'] <= 5,
         '§4.9 (la segunda lectura ya no reduce las quejas que se escapan)')
verifica(sa_3['fp'] >= sa_2['fp'] and sb_3['fp'] >= sb_2['fp'], '§4.9 (la tercera lectura ya aporta algo)')
# Agrupamiento (k-means) sobre el texto de la base preparada
ag = ac.agrupar(prep); et_g = ag['etiquetas']
per_g = ac.perfil_grupos(prep, et_g); sem_g = ac.grupos_por_semestre(prep, et_g)
g_queja = min(per_g, key=lambda x: x['estrellas_prom']); g_elogio = max(per_g, key=lambda x: x['estrellas_prom'])
g_mixto = next(x for x in per_g if x['grupo'] not in (g_queja['grupo'], g_elogio['grupo']))
_sem_ok = [x for x in sem_g if x['n'] >= 30]
sg_pico = max(_sem_ok, key=lambda x: x[f'grupo_{g_queja["grupo"]}']); sg_ult = _sem_ok[-1]
verifica(ag['k'] == 3 and g_queja['Cambio a botella de plastico'] > 0.3 and g_queja['pct_4_5'] < 0.2 and g_elogio['pct_4_5'] > 0.8
         and sg_pico['semestre'].startswith('2025') and sg_ult[f'grupo_{g_queja["grupo"]}'] < sg_pico[f'grupo_{g_queja["grupo"]}'] / 2,
         '§4.10 (los grupos del agrupamiento cambiaron: reescribe sus nombres y la lectura)')
def _ganadores(sl, c):
    m = min(f[f'costo_c{c}'] for f in sl); return [f['regla'] for f in sl if f[f'costo_c{c}'] == m]
gan_a = {c: _ganadores(sl_a, c) for c in (1, 2, 3, 5)}; gan_b = {c: _ganadores(sl_b, c) for c in (1, 2, 3, 5)}
_cogidas_a = sa_lex['fp'] - sa_2['fp']; _cogidas_b = sb_lex['fp'] - sb_2['fp']   # quejas nuevas que la segunda lectura atrapa (la union contiene al lexico)
_extra_fa_a = sa_2['fn'] - sa_lex['fn']
C_BASE = 5   # razon de costos de trabajo (decision de Orlando, 2026-11-18): una queja que se escapa pesa 5 falsas alarmas
_R2 = 'Léxico O KNN (segunda lectura)'
cq_a, cq_b = ac.c_equilibrio(sl_a, _R2), ac.c_equilibrio(sl_b, _R2)
verifica(cq_a is not None and cq_b is not None and cq_a <= C_BASE and cq_b <= C_BASE, '§4.9 (con c = %d la segunda lectura ya no es la de menor costo)' % C_BASE)
_anch = [(lambda lo_hi: (lo_hi[1] - lo_hi[0]) * 100)(ac.wilson(m['vp'] + m['vn'], m['n'])) for m in pb.values()]
anchos = (min(_anch), max(_anch))
ok_est, tot_est, excl_est = ac.acuerdo_estrellas(filas, corpus)
# Errores del lexico en la muestra manual (patrones leidos a mano en data/desacuerdos_lexico.md)
lex_p = ac.lexico_proyecto()
casos = []
for x in filas:
    p = ac.lx.puntaje(x['titulo'] + '. ' + x['texto'], lex_p)
    casos.append((x['manual'], ac.lectura_lexico(p)))
from collections import Counter
desac = Counter((a, b) for a, b in casos if a != b)
n_des = sum(desac.values())
# Evolucion
sem_n50 = [x for x in evc if x['n'] >= 50]
minimo = min(sem_n50, key=lambda x: x['estrellas_pos']); ultimo = evc[-1]
brecha_lex = max(abs(x['estrellas_pos'] - x['lexico_pos']) for x in sem_n50) * 100
verifica(brecha_lex <= 8, '§4.6 (el léxico ya no sigue de cerca a las estrellas)')
ci_min = ac.wilson(round(minimo['estrellas_pos'] * minimo['n']), minimo['n'])
ci_ult = ac.wilson(round(ultimo['estrellas_pos'] * ultimo['n']), ultimo['n'])
verifica(ci_min[1] < ci_ult[0], '§4.6 (los intervalos de los extremos se solapan)')
t_min = next(x for x in tem if x['semestre'] == minimo['semestre'])
t_ult = tem[-1]
t_24 = next(x for x in tem if x['semestre'] == '2024-S2')
verifica(t_min['Cambio a botella de plastico'] > 2 * t_ult['Cambio a botella de plastico'], '§4.7 (el cambio a plástico ya no cae)')
verifica(t_24['Producto roto o derrame'] > 5 * t_ult['Producto roto o derrame'] and t_min['Producto roto o derrame'] > 5 * t_ult['Producto roto o derrame'], '§4.7 (los daños en envío ya no caen)')
a25 = next((a for a in alt if a['mes'].startswith('2025')), None)
verifica(a25 is not None, '§4.8 (la regla ya no marca 2025)')
a_ult = alt[-1] if alt and alt[-1]['mes'] == mens[-1]['mes'] else None
# Fecha aproximada del cambio a botella de plastico, leida de las reseñas (mismo patron que el tema de §4.7)
_pat_pl = re.compile(ac.TEMAS['Cambio a botella de plastico'])
_pl = sorted(x['fecha'] for x in corpus if _pat_pl.search((x['titulo'] + ' ' + x['texto']).lower()))
pl_primera = _pl[0]
pl_antes_abr = sum(1 for f in _pl if f[:7] < '2025-04')
pl_mes = {m: sum(1 for f in _pl if f[:7] == m) for m in ('2025-04', '2025-05', '2025-06', '2025-09')}
verifica(pl_primera < '2025-04' and pl_mes['2025-05'] > 5 * max(pl_mes['2025-04'], 1) and pl_mes['2025-09'] < pl_mes['2025-05'] / 2,
         '§4.7 (la fecha aproximada del cambio a plástico)')
_pat_ag = re.compile(ac.TEMAS['Formula aguada o diluida'])
_ag = sorted(x['fecha'] for x in corpus if _pat_ag.search((x['titulo'] + ' ' + x['texto']).lower()))
ag_primera = _ag[0]
ag_antes_abr = sum(1 for f in _ag if f[:7] < '2025-04')
ag_mes = {m: sum(1 for f in _ag if f[:7] == m) for m in ('2025-04', '2025-05', '2025-06', '2025-09')}
verifica(ag_primera < '2025-01' and ag_mes['2025-05'] > 4 * max(ag_antes_abr / 9, 1), '§4.7 (la queja de fórmula aguada ya no antecede al cambio de plástico)')
# Calibracion del semaforo: prueba hacia atras de varios umbrales
bt = ac.backtest_alertas(mens)
def _bt(c, n): return next(f for f in bt if abs(f['caida'] - c) < 1e-9 and f['n_min'] == n)
bt_rojo, bt_amar = _bt(0.10, 30), _bt(0.05, 30)
verifica(bt_rojo['falsas_alarmas'] == 0 and bt_amar['aciertos'] > bt_rojo['aciertos'] and bt_amar['falsas_alarmas'] >= 1,
         '§4.8 (la calibración del semáforo cambió de sentido)')
amarillos = [a for a in ac.alertas(mens, 0.05, 30) if a['mes'] not in {x['mes'] for x in alt}]

# ----------------------------------------------------------------------------------------------
# Notebook
# ----------------------------------------------------------------------------------------------
md('# ¿Cuándo actuar? Sentimiento de las reseñas de Amazon de Serene Herbs Soursop Bitters',
   '### Propuesta de un modelo de analítica de negocios · Trabajo final', '',
   '**Curso:** Analítica de Negocios (CO0371), Escuela de Administración, EAFIT  |  **Profesor:** ________  |  **Fecha:** ________', '',
   '**Integrante:** Orlando Cardiles  |  **Código:** ________  |  **Correo:** ________', '',
   'Este notebook se ejecuta **de principio a fin** (Entorno de ejecución → Ejecutar todo) con los datos del repositorio. '
   'Cada etapa tiene su celda de texto y la interpretación de cada resultado.')

md('## 1. Problema de decisión', '',
   '**Organización.** Una operación de analítica que construye una herramienta para ayudar a **vendedores de productos en Amazon** a leer lo que dicen sus compradores. '
   'Quien decide es el fundador de la operación (Orlando Cardiles), que define qué mide la herramienta y qué hace con sus alertas; el vendedor que la usa decide sobre su producto. '
   'El **caso piloto** es Serene Herbs Soursop Bitters + Black Seed Bitters (bundle de 32 oz, ASIN B0D4MPKGN6), una marca que es cliente de la operación: '
   'sus reseñas sirven de ejemplo y de datos para construir y probar el modelo, pero el producto de este trabajo es la herramienta y no la marca.', '',
   '**Decisión.** Dos decisiones concretas a partir de lo que dicen los compradores en sus reseñas, y no solo de cuántas estrellas dan: '
   '(a) **cuándo revisar el lote o al proveedor**, cuando suben las quejas (por ejemplo, "fórmula aguada" o "plástico"); '
   '(b) **a qué clientes responder o reembolsar**, es decir, qué reseñas negativas atender primero.', '',
   '**Cómo se decide hoy.** Con el promedio de estrellas y leyendo reseñas sueltas, que es lo que la herramienta hace hoy; '
   'ninguna de las dos formas mide a tiempo el cambio de ánimo de los compradores ni escala a cientos de reseñas.', '',
   '**Por qué importa el sentimiento y su evolución.** La estrella resume, pero el texto explica. En esta base el porcentaje de reseñas de 4-5★ '
   f'pasó de {pc(minimo["estrellas_pos"])} en {minimo["semestre"]} a {pc(ultimo["estrellas_pos"])} en {ultimo["semestre"]}: un cambio grande que un promedio '
   'tarda en mostrar y que no dice qué lo provocó. Leer a mano las '
   f'{n_corp_fmt} reseñas no escala; un modelo que lea el sentimiento del texto permite vigilar cada mes y reaccionar a tiempo cuando baja.', '',
   '**Qué cuesta equivocarse.** Hay dos errores con costos distintos: (a) leer como elogio una queja (*falso positivo*) deja pasar un problema que nadie atiende; '
   '(b) leer como queja un elogio (*falso negativo*) genera una falsa alarma y tiempo perdido. '
   '**El error más caro es el primero (falso positivo):** una queja leída como elogio no se atiende y cuesta reputación y tiempo; '
   'la falsa alarma cuesta solo tiempo de revisión. El costo no se estimó en dinero: es un juicio de quien decide, no una medición. '
   'Esa respuesta decide qué métrica se mira primero (ver §3).')

md('## 2. Preparación del entorno y de los datos')
codigo('''
import os, sys, subprocess, importlib.util, warnings
warnings.filterwarnings('ignore')
REPO_URL = 'https://github.com/ocardiles03/resenas-nlp-trabajo-final'   # repositorio privado: en Colab guarda un token en Secretos con el nombre GITHUB_TOKEN
if not os.path.exists('src/acierto_sentimiento.py'):
    if not REPO_URL:
        raise SystemExit('Falta REPO_URL: pega arriba la URL del repositorio.')
    url = REPO_URL
    if 'google.colab' in sys.modules and url.startswith('https://') and '@' not in url:   # repositorio privado: token en los Secretos de Colab (clave GITHUB_TOKEN)
        try:
            from google.colab import userdata
            url = url.replace('https://', 'https://' + userdata.get('GITHUB_TOKEN') + '@', 1)
        except Exception:
            pass   # sin token: se intenta clonar tal cual (repositorio publico)
    subprocess.run(['git', 'clone', '--depth', '1', url, 'repo'], check=True)
    os.chdir('repo')
if 'google.colab' in sys.modules:
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'scikit-learn', 'openpyxl'], check=True)
print('Carpeta de trabajo:', os.getcwd())
''')
codigo('''
from collections import Counter
spec = importlib.util.spec_from_file_location('acierto_sentimiento', 'src/acierto_sentimiento.py')
ac = importlib.util.module_from_spec(spec); sys.modules['acierto_sentimiento'] = ac; spec.loader.exec_module(ac)
try:
    from IPython.display import Markdown, display
    def mostrar(txt): display(Markdown(txt))
except ImportError:
    def mostrar(txt): print(txt)
''')
md('### 2.1 Corpus completo (datos originales: Excel v4)')
codigo('''
corpus = ac.dc.cargar(ac.dc.XLSX)
fechas = sorted(r['fecha'] for r in corpus)
print(f"Reseñas con texto y fecha: {len(corpus)}")
print(f"Periodo: {fechas[0]} a {fechas[-1]}")
print("Distribución por estrellas:", dict(sorted(Counter(r['estrellas'] for r in corpus).items())))
''')
md('#### Preparación del corpus: de la hoja original al corpus analizado (solo conteos)')
codigo('''
from openpyxl import load_workbook
hoja = list(load_workbook(ac.dc.XLSX, read_only=True)['Reseñas'].iter_rows(values_only=True))
cab = hoja[0]; crudas = [dict(zip(cab, v)) for v in hoja[1:] if any(v)]
ids = [x['ID reseña'] for x in crudas if x['ID reseña']]
sin_texto = [x for x in crudas if not (x['Reseña'] or '').strip()]
print(f"Filas en la hoja original:              {len(crudas)}")
print(f"  sin ID de reseña:                     {sum(1 for x in crudas if not x['ID reseña'])}")
print(f"  ID repetido (se conserva la primera): {len(ids) - len(set(ids))}")
print(f"  sin texto de reseña (se descartan):   {len(sin_texto)}")
print(f"Corpus analizado:                       {len(corpus)}")
print(f"  sin fecha:                            {sum(1 for r in corpus if not r['fecha'])}")
print(f"  de 3 estrellas (en el corpus, pero fuera del entrenamiento del léxico y de los clasificadores): {sum(1 for r in corpus if r['estrellas'] == 3)}")
''')
md('#### Base preparada (`data/base_preparada_resenas.csv`, creada con `src/preparar_base.py`)')
codigo('''
import csv
with open(ac.DATA / 'base_preparada_resenas.csv', encoding='utf-8', newline='') as fh:
    prep = list(csv.DictReader(fh))
print(f"Base preparada: {len(prep)} reseñas; columnas: {list(prep[0])}")
print("Reseñas por semestre:", dict(sorted(Counter(x['semestre'] for x in prep).items())))
print("Clase según estrellas:", dict(Counter(x['clase_estrellas'] for x in prep)))
largos = sorted(len(x['texto'].split()) for x in prep)
print(f"Palabras por reseña: mediana {largos[len(largos) // 2]}, mínimo {largos[0]}, máximo {largos[-1]}")
print(f"Compra verificada: {sum(1 for x in prep if x['compra_verificada'] == 'Sí')} de {len(prep)}")
''')
md('**Decisiones de preparación (y por qué).**', '',
   f'- Se descartan las filas sin texto ({n_sin_texto}) porque no hay nada que leer; no hay IDs repetidos ni fechas faltantes.',
   '- Se agrega `semestre` (AAAA-S1/S2) para describir la evolución con grupos de tamaño razonable; por mes habría pocas reseñas en 2024.',
   '- Se agrega `clase_estrellas`: Positivo (4-5★) y Negativo (1-2★). Las de 3★ (' + str(n3) + ') no son claramente ni una ni otra y quedan fuera del entrenamiento.',
   '- Se quita `Reviewer` (nombre de una persona): no hace falta para el análisis y es dato personal.',
   '- **No se corrigen atípicos ni faltantes numéricos:** las estrellas solo toman valores 1-5 y no hay datos faltantes en las variables usadas.',
   '- El texto se pasa a minúsculas, se lematiza y se quitan palabras vacías, **conservando** *no*, *not*, *never* y las palabras de opinión (porque cambian el sentido). '
   'No hay escalamiento de variables numéricas: los modelos de texto usan TF-IDF, que ya normaliza los pesos de las palabras.')
md('#### Diccionario de variables', '',
   '| Variable | Descripción | Tipo | Unidad | Rol |', '|---|---|---|---|---|',
   '| `id` | Identificador de la reseña en Amazon | Texto | — | Identificador |',
   '| `fecha` | Fecha de publicación de la reseña | Fecha (ISO) | Día | Perfilamiento (origen de `semestre`) |',
   '| `semestre` | Semestre de la fecha (AAAA-S1 / AAAA-S2) | Categórica ordinal | Semestre | Perfilamiento (evolución en el tiempo) |',
   '| `estrellas` | Calificación que dio el comprador (1 a 5) | Numérica discreta | Estrellas | Variable numérica pronosticable (no se pronostica aquí), fuente de la etiqueta de clasificación y variable de perfilamiento de los grupos |',
   '| `clase_estrellas` | Positivo (4-5★), Negativo (1-2★) o Tibia (3★) | Categórica | — | Objetivo de clasificación (KNN y Naive Bayes) |',
   '| `titulo`, `texto` | Título y texto de la reseña (inglés) | Texto | — | Variables explicativas (entran al léxico, KNN y Naive Bayes) y variable de agrupamiento (k-means) |',
   '| `compra_verificada` | Si Amazon verificó la compra (Sí/No) | Categórica | — | Perfilamiento (de los grupos) |',
   '| `enlace` | URL de la reseña en Amazon | Texto | — | Trazabilidad (no entra al modelo) |',
   '| `sentimiento_manual` | Positivo / Negativo / Neutro según lectura humana (solo en la muestra etiquetada) | Categórica | — | Referencia para medir el acierto (objetivo de clasificación) |')
md('#### Descripción de los datos', '',
   '- **Qué es un registro:** una reseña de un comprador en Amazon.com del bundle B0D4MPKGN6, con título, texto en inglés, estrellas, fecha, enlace y marca de compra verificada.',
   f'- **Tamaño y periodo:** {n_corp_fmt} reseñas con texto, del {fechas[0]} al {fechas[-1]} (unos 2,4 años). Por estrellas: ' +
   ', '.join(f'{k}★ = {v}' for k, v in estr.items()) + f'. Compra verificada: {verif} de {len(prep)}. Mediana de {palabras[len(palabras) // 2]} palabras por reseña.',
   '- **Procedencia:** ficha completa en `data/README_datos.md`. Las reseñas se recolectaron en octubre de 2026 con el navegador (Chrome) y con la herramienta Apify; '
   'los datos originales tal como se descargaron están en `data/crudo_chrome_apify/` y `data/bundle_xlsx_historico/`. '
   'Los recolectó Orlando Cardiles con las dos herramientas. Lotes (fecha del archivo): Apify, 23 de octubre de 2026 (`dataset_amazon-reviews-scraper-with-advanced-filters_2026-10-23_...json`); '
   'Chrome, 23, 24 y 25 de octubre de 2026 (`serene_chrome_reviews.json`, `_v2` y `_v3`; las fechas de los tres son las de modificación del archivo). '
   'Enlace: `https://www.amazon.com/product-reviews/B0D4MPKGN6/`.',
   '- **Limitaciones:** (1) un solo producto y un solo canal; (2) solo reseñas con texto, y quien reseña no es el comprador promedio; '
   '(3) Amazon entrega ~10 reseñas por vista de filtro, así que se descargaron filtrando por estrellas y palabras: la proporción de estrellas de la base puede no ser la de la página; '
   '(4) todo está en inglés; (5) el periodo cubre unos 2,4 años, menos de los 4 que pide el enunciado para un corpus propio: '
   'se declara como limitación: con tan poco tiempo no se pueden estimar patrones de largo plazo como la estacionalidad.')

md('### 2.2 Muestra etiquetada a mano (referencia para medir el acierto)')
codigo('''
# La hoja de 100 es obligatoria. Las hojas de ampliación se suman SOLO si ya están etiquetadas por completo.
filas, hojas, avisos = ac.hojas_etiquetadas()
for a in avisos: print(a)
print('Hojas usadas:', hojas)
print(f"Reseñas etiquetadas a mano: {len(filas)}")
print(dict(Counter(r['manual'] for r in filas)))
''')
cnt = r['conteo']
md('**La muestra manual.**', '',
   f'- **Cómo se eligió:** {r["n"]} reseñas aleatorias estratificadas por estrellas (`docs/PLAN_base_resenas.md`, `data/validacion_100.csv`). '
   'La hoja de etiquetado (`src/hoja_etiquetado.py`) solo muestra título y texto: quien etiquetó **no vio** las estrellas ni la lectura del léxico. '
   'Como el estrato es la nota y no el semestre, algunos semestres quedan con muy pocas reseñas (ver §4.6).',
   '- **Quién etiquetó y con qué criterio:** Orlando Cardiles, a mano, leyendo solo el texto (no las estrellas). '
   '**Positivo:** el texto muestra satisfacción clara o intención de recompra. **Negativo:** la persona dice que algo falló o que no volverá a comprar '
   '(por ejemplo, "me sirvió la vez pasada pero este no me gusta igual"). **Neutro:** mixto o provisional (por ejemplo, "me sirvió el primero y estoy probando el segundo"). '
   f'Resultado: Positivo {cnt["Positivo"]}, Negativo {cnt["Negativo"]}, Neutro {cnt["Neutro"]}.',
   f'- **Neutro y las métricas:** las {cnt["Neutro"]} reseñas Neutro **no entran** en las métricas binarias (Positivo contra Negativo); quedan {r["n"] - cnt["Neutro"]}. '
   'Sí aparecen en la matriz de 3 clases (§4.4).',
   '- **Limpieza de la muestra:** 4 textos de la hoja traen avisos de la interfaz de Amazon ("No se pudo cargar el archivo multimedia", "Haz clic para reproducir el video"); '
   '`leer_hojas` los quita antes de medir.')

md('## 3. Modelos: léxico, KNN, Naive Bayes y k-means', '',
   '| Modelo | Familia del curso | Qué lee del texto |', '|---|---|---|',
   '| **Léxico del proyecto** (`data/lexico_cliente_v4.json`) | Análisis de texto y sentimientos | Una "balanza": cada palabra suma o resta y el signo del total da la lectura |',
   '| **KNN** (TF-IDF, distancia coseno) | Clasificación | Busca las *k* reseñas más parecidas y toma su voto |',
   '| **Naive Bayes** (TF-IDF) | Clasificación | Qué tan típica es cada palabra de las reseñas positivas y de las negativas |',
   '| **k-means** (TF-IDF + SVD) | Agrupamiento | Qué reseñas hablan de lo mismo, sin usar estrellas ni etiquetas |', '',
   'Son **cuatro modelos de tres familias distintas** (el enunciado exige al menos dos): los tres primeros miden el sentimiento y el cuarto descubre de qué se habla.', '',
   '**Cómo funciona cada uno, sin fórmulas.**', '',
   '- *Léxico.* Las palabras y sus pesos se aprenden de reseñas de este mismo tipo (Amazon, inglés, producto de salud): una palabra pesa +2 si el 75 % o más de sus apariciones '
   'está en reseñas de 4-5★ y -2 si el 25 % o menos (mínimo 15 apariciones en 10 reseñas), lo que da 104 palabras positivas y 78 negativas. Una negación (*no, not, never*) invierte las tres palabras siguientes. '
   'Si el total es mayor que 0 la lectura es Positivo, menor que 0 Negativo, y 0 Neutro. '
   '**Por qué es el adecuado para este idioma y tipo de texto:** un léxico general no conoce el vocabulario del producto; el aprendido de estas reseñas sí: '
   '*bloated* o *cleanse*, que suenan mal, están del lado positivo porque los compradores contentos cuentan que quedaron "menos hinchados" o que "limpió" su cuerpo.',
   '- *KNN.* Cada reseña se convierte en números según qué palabras y parejas de palabras usa (TF-IDF: pesa más lo raro y específico que lo común). Para leer una reseña nueva se buscan '
   'las *k* más parecidas (por ángulo, distancia coseno) y se mira cuántas fueron positivas. Se descarta mirar solo una (*k* = 1) porque cualquier rareza la desvía.',
   '- *Naive Bayes.* Cuenta qué tan frecuente es cada palabra en las reseñas positivas y en las negativas y combina esas frecuencias asumiendo que las palabras no se influyen entre sí '
   '(por eso "ingenuo"). El parámetro alfa es un suavizado para que una palabra vista una sola vez no decida todo.',
   '- *k-means.* Resume cada reseña en 30 números (los ejes de temas que más separan los textos, con una descomposición SVD del TF-IDF) y reparte las reseñas en *k* grupos '
   'moviendo los centros hasta que cada reseña quede con el centro que más se le parece. **Por qué se ajusta al problema:** no necesita etiquetas ni estrellas, así que muestra de qué hablan los compradores '
   'con independencia del sentimiento, que es lo que hace falta para decidir si revisar el lote (§1). El número de grupos se escoge con silueta, codo y estabilidad (§4.10).',
   '- *Alternativas descartadas.* Redes neuronales o modelos de lenguaje preentrenados: no se vieron en el curso y serían difíciles de explicar a un gerente. '
   'La regresión logística sobre TF-IDF se probó (`docs/comparacion_modelos_v4.md`, exactitud 0.915) y rinde igual que KNN, así que no aporta una conclusión distinta.', '',
   '**Configuración.** Partición 80/20 **estratificada** con semilla fija (42). El parámetro principal (*k* en KNN, alfa en Naive Bayes) se escoge con **validación cruzada de 5 pliegues '
   'solo sobre el 80 % de entrenamiento**, con el AUC como criterio. Se hacen dos pruebas:', '',
   f'- **Prueba A (estrellas como etiqueta):** {e["n"]} reseñas polares (4-5★ contra 1-2★), {e["n_train"]} de entrenamiento y {e["n_test"]} de prueba. Mide a los tres modelos sobre las mismas reseñas.',
   f'- **Prueba B (muestra manual):** las {r["n"]} reseñas etiquetadas a mano, {r["n_train"]} de entrenamiento y {r["n_test"]} de prueba ({r["n_test_bin"]} sin Neutro). Es la referencia "de verdad" pero es pequeña.', '',
   '**Métricas.** Se reportan matriz de confusión, exactitud (con intervalo de confianza), sensibilidad (positivas bien leídas), especificidad (negativas bien leídas), precisión (de lo que el modelo '
   'llama elogio, cuánto lo es) y F1 y AUC. Para el cliente importa sobre todo la **especificidad y la precisión**: son las que miden las quejas que se escapan leídas como elogio; '
   'la sensibilidad mide las falsas alarmas. Esa elección sale del juicio de quien decide (§1): el error más caro es dejar pasar una queja.')
codigo('''
# Prueba A: las estrellas como etiqueta, partición 80/20 estratificada, k y alfa por validación cruzada solo en el 80 %.
e = ac.evaluar_estrellas(corpus)
print(f"Prueba A: {e['n']} reseñas polares -> entrenamiento {e['n_train']}, prueba {e['n_test']} ({e['pos_test']} positivas)")
print(f"k elegido (KNN): {e['k']}   |   alfa elegido (Naive Bayes): {e['alfa']}   |   corte = {e['corte']:.3f} (proporción de positivas del entrenamiento)")
mostrar('| k | ' + ' | '.join(map(str, e['aucs_k'])) + ' |\\n|---|' + '---|' * len(e['aucs_k']) +
        '\\n| AUC (CV), KNN | ' + ' | '.join(ac.f(v) for v in e['aucs_k'].values()) + ' |')
mostrar('| alfa | ' + ' | '.join(map(str, e['aucs_alfa'])) + ' |\\n|---|' + '---|' * len(e['aucs_alfa']) +
        '\\n| AUC (CV), Naive Bayes | ' + ' | '.join(ac.f(v) for v in e['aucs_alfa'].values()) + ' |')
''')
codigo('''
# Prueba B: la muestra manual.
r = ac.evaluar(filas, corpus)
print(f"Partición 80/20 (semilla {ac.SEMILLA}): entrenamiento {r['n_train']}, prueba {r['n_test']} ({r['n_test_bin']} sin Neutro)")
print(f"k elegido (KNN manual): {r['k_manual']}   |   k elegido (KNN estrellas): {r['k_estrellas']}   |   alfa (Naive Bayes): {r['alfa_nb']}")
mostrar('| k | ' + ' | '.join(map(str, r['aucs_manual'])) + ' |\\n|---|' + '---|' * len(r['aucs_manual']) +
        '\\n| AUC (CV), KNN manual | ' + ' | '.join(ac.f(v) for v in r['aucs_manual'].values()) + ' |')
''')
ks = e['aucs_k']
md('**Por qué ese *k* y ese alfa.** ' +
   f'En la prueba A el AUC de validación cruzada sube de {ks[1]:.3f} con *k* = 1 hasta {max(ks.values()):.3f} con *k* = {e["k"]} y se mantiene casi plano (≥ {min(v for kk, v in ks.items() if kk >= 15):.3f}) entre 15 y 101: '
   f'pocos vecinos se dejan engañar por una reseña rara y muchísimos pierden la señal; se toma el máximo (*k* = {e["k"]}). '
   f'Para Naive Bayes los cuatro alfas dan un AUC casi idéntico ({min(e["aucs_alfa"].values()):.3f} a {max(e["aucs_alfa"].values()):.3f}); gana alfa = {e["alfa"]}, así que el suavizado casi no importa en este corpus. '
   f'En la muestra manual, con solo {r["n_train"]} reseñas de entrenamiento, el *k* elegido es {r["k_manual"]} y la curva es mucho más sensible: es otra señal de que esa muestra es chica.')

md('## 4. Resultados')
md('### 4.1 Prueba A: tres modelos sobre las mismas ' + str(e['n_test']) + ' reseñas de prueba (etiqueta = estrellas)')
codigo("mostrar('\\n'.join(ac.tabla_metricas(e['prueba'])))")
md('**Lectura.** ' +
   f'Con {e["n_test"]} reseñas de prueba (más de diez veces las de la muestra manual), KNN acierta {ic(pa, KNN)}, Naive Bayes {ic(pa, NB)} y el léxico {ic(pa, LEX)}. '
   f'KNN y Naive Bayes son prácticamente equivalentes (su cantidad de aciertos difiere en {dif_kn} reseña(s) de {e["n_test"]}). '
   f'El léxico queda {brecha:.1f} puntos por debajo de KNN y los intervalos apenas se tocan (el de KNN empieza en {lo_k:.3f}; el del léxico termina en {hi_l:.3f}): '
   'la ventaja de los clasificadores existe, pero es moderada, no abrumadora.', '',
   f'**Tipo de error.** El léxico deja pasar **{pa[LEX]["fp"]}** quejas leídas como elogio (falsos positivos) y confunde **{pa[LEX]["fn"]}** elogios con quejas o con texto sin veredicto (falsos negativos); '
   f'KNN comete {pa[KNN]["fp"]} y {pa[KNN]["fn"]}, y Naive Bayes {pa[NB]["fp"]} y {pa[NB]["fn"]}. Si lo caro es perder una queja, KNN es el mejor de los tres (mayor especificidad, {pa[KNN]["especificidad"]:.3f}, '
   f'y precisión, {pa[KNN]["precision"]:.3f}); el léxico deja escapar casi el doble de quejas.', '',
   f'**AUC.** Los tres están sobre {min(m["auc"] for m in pa.values()):.3f}: si se toman al azar una reseña positiva y una negativa, el modelo pone la positiva por encima casi siempre. '
   'Es decir, ordenan bien las reseñas aunque su exactitud sea distinta.', '',
   '**Advertencia.** La "verdad" de esta prueba es la nota en estrellas, no una lectura humana del texto: una reseña de 5★ que se queja en el texto cuenta como error del modelo aunque el modelo tenga razón. '
   'Por eso se complementa con la muestra manual (§4.2-4.3).')
md('### 4.2 Prueba B: muestra manual, conjunto de prueba (20 %)')
codigo("mostrar('\\n'.join(ac.tabla_metricas(r['prueba'])))")
md('**Lectura.** ' +
   f'La prueba tiene solo {r["n_test_bin"]} reseñas (sin Neutro). Los modelos aciertan {min(m["exactitud"] for m in pb.values()):.3f} a {max(m["exactitud"] for m in pb.values()):.3f}, es decir, '
   f'se diferencian por una o dos reseñas, y los intervalos de confianza (de {anchos[0]:.0f} a {anchos[1]:.0f} puntos de ancho) se solapan casi por completo. '
   '**Con esta muestra no se puede declarar un ganador**; sirve para comprobar que los modelos hacen algo razonable, no para ordenarlos. '
   'El KNN entrenado con etiquetas manuales aprendió de solo 80 reseñas, por eso es el menos estable.')
md('### 4.3 Prueba B: toda la muestra etiquetada (modelos que no se entrenan con ella)')
codigo("mostrar('\\n'.join(ac.tabla_metricas(r['todas'])))")
codigo('''
# ¿La nota en estrellas coincide con lo que leyó una persona? (solo reseñas no Neutro y no de 3★)
est = {x['id']: x['estrellas'] for x in corpus}
ok = tot = 0
for x in filas:
    if est.get(x['id'], 3) == 3 or x['manual'] == 'Neutro':
        continue
    tot += 1; ok += int((est[x['id']] >= 4) == (x['manual'] == 'Positivo'))
print(f"La nota coincide con la etiqueta manual en {ok} de {tot} reseñas ({ok / tot:.1%}); quedan fuera {len(filas) - tot} (Neutro, 3★ o sin nota)")
''')
md('**Lectura.** ' +
   f'Sobre las {tb["Lexico del proyecto"]["n"]} reseñas no Neutro, el léxico acierta {ic(tb, "Lexico del proyecto")} y KNN con estrellas {ic(tb, "KNN con estrellas")}. '
   f'El **léxico sin la muestra** (aprendido sin esas reseñas) acierta {ic(tb, "Lexico sin la muestra")}: casi igual, así que el buen resultado **no** se debe a que el léxico "haya visto" la muestra. '
   f'La nota coincide con la lectura humana en {ok_est} de {tot_est} reseñas ({ok_est / tot_est:.1%}), por eso las estrellas son una buena aproximación a la etiqueta manual en la muestra. '
   f'El léxico acierta menos en la prueba A ({pa[LEX]["exactitud"]:.3f}) que aquí ({tb["Lexico sin la muestra"]["exactitud"]:.3f}); con solo {tb["Lexico del proyecto"]["n"]} reseñas la diferencia '
   'no se puede atribuir con seguridad a nada, y es una razón más para ampliar la muestra manual.')
md('### 4.4 Matriz de 3 clases del léxico (filas = manual, columnas = léxico)')
codigo('''
mostrar('| manual \\\\ léxico | ' + ' | '.join(r['etq3']) + ' |\\n|---|---|---|---|\\n' +
        '\\n'.join(f'| {e_} | ' + ' | '.join(str(int(v)) for v in fila) + ' |' for e_, fila in zip(r['etq3'], r['m3'])))
''')
m3 = r['m3']; ix = {n: i for i, n in enumerate(r['etq3'])}
verifica(m3[ix['Neutro']][ix['Neutro']] <= 4 and m3[ix['Neutro']][ix['Negativo']] > m3[ix['Neutro']][ix['Positivo']], '§4.4 (el léxico ya acierta Neutro)')
md('**Lectura.** ' +
   f'El léxico lee bien los extremos ({m3[ix["Positivo"]][ix["Positivo"]]} de {int(m3[ix["Positivo"]].sum())} positivas y {m3[ix["Negativo"]][ix["Negativo"]]} de {int(m3[ix["Negativo"]].sum())} negativas), '
   f'pero casi nunca acierta un Neutro ({m3[ix["Neutro"]][ix["Neutro"]]} de {int(m3[ix["Neutro"]].sum())}): {m3[ix["Neutro"]][ix["Negativo"]]} los lee como Negativo. '
   'La razón se ve en los casos (§4.5): las reseñas Neutro suelen mezclar una queja con algo bueno, y la balanza suma la queja.')
md('### 4.5 Reseñas donde el léxico no coincide con la etiqueta manual')
codigo('''
import json
lex = ac.lexico_proyecto()
casos = []
for x in filas:
    p = ac.lx.puntaje(x['titulo'] + '. ' + x['texto'], lex)
    lectura = ac.lectura_lexico(p)
    if lectura != x['manual']:
        casos.append((x['manual'], lectura, p, x['titulo'], x['texto'][:300]))
print(f'{len(casos)} desacuerdos de {len(filas)}')
print(dict(Counter((c[0], c[1]) for c in casos)))
for c in sorted(casos): print(f'manual={c[0]:9s} léxico={c[1]:9s} puntaje={c[2]:+.1f} | {c[3]} | {c[4]}')
''')
verifica(desac[('Neutro', 'Negativo')] >= max(v for k, v in desac.items() if k != ('Neutro', 'Negativo')), '§4.5 (el desacuerdo principal ya no es Neutro→Negativo)')
md('**Lectura de los casos** (se leyeron uno a uno; el listado completo está en `data/desacuerdos_lexico.md` y `resultados/desacuerdos_lexico.csv`). ' +
   f'Hay {n_des} desacuerdos en {len(filas)} reseñas; los patrones que se repiten:', '',
   f'- **Neutro leído como Negativo ({desac[("Neutro", "Negativo")]} casos): reseñas mixtas.** Critican un aspecto (sabor, envío, servicio, botella de plástico) sin condenar el producto: '
   '"product itself is satisfactory, however I am not happy … they have switched from glass bottles to plastic bottles". La balanza suma las palabras negativas y no ve el "aunque".',
   f'- **Positivo leído como Neutro ({desac[("Positivo", "Neutro")]}): reseñas cortas o sin vocabulario conocido.** "Great purchase" suma 0 porque ninguna de esas palabras está en el léxico; '
   'una reseña en español ("Muy buenos los recomiendo") tampoco: **el léxico solo entiende inglés**.',
   f'- **Negativo leído como Neutro ({desac[("Negativo", "Neutro")]}): ironía, mayúsculas o palabras fuera del léxico.** "Just a REALLY expensive laxative … Lol" y "Horrible taste" quedan en 0.',
   f'- **Neutro leído como Positivo ({desac[("Neutro", "Positivo")]}) y Negativo leído como Positivo ({desac[("Negativo", "Positivo")]}):** palabras positivas dentro de un texto que se queja, '
   'como "Was good on the first one but the second one was not good at all" (el producto cambió entre compras).', '',
   '**Dónde se concentra el error:** en lo que no es claramente bueno ni malo (mixtas, cortas, irónicas) y en lo que no está en inglés. '
   'Ninguno de estos patrones se arregla con más palabras en el léxico; piden leer el contraste ("pero", "aunque") y la ironía, que están fuera del alcance de estos modelos.')
md('### 4.6 Evolución por semestre')
codigo('''
mostrar('**Muestra etiquetada**\\n\\n| Semestre | n | % Positivo | % Neutro | % Negativo | % positivo según léxico |\\n|---|---|---|---|---|---|\\n' +
        '\\n'.join(f"| {e_['semestre']} | {e_['n']} | {e_['pos']*100:.0f} % | {e_['neu']*100:.0f} % | {e_['neg']*100:.0f} % | {e_['lexico_pos']*100:.0f} % |" for e_ in r['evol']))
filas_c = []
for e_ in r['evol_corpus']:
    k = round(e_['estrellas_pos'] * e_['n']); lo, hi = ac.wilson(k, e_['n'])
    filas_c.append(f"| {e_['semestre']} | {e_['n']} | {e_['estrellas_pos']*100:.0f} % ({lo*100:.0f}-{hi*100:.0f} %) | {e_['lexico_pos']*100:.0f} % |")
mostrar('**Todo el corpus (sin etiquetas manuales)**\\n\\n| Semestre | n | % 4-5 estrellas (IC 95 %) | % positivo según léxico |\\n|---|---|---|---|\\n' + '\\n'.join(filas_c))
''')
codigo('''
try:
    import matplotlib.pyplot as plt
    sem = [e_['semestre'] for e_ in r['evol_corpus']]
    plt.figure(figsize=(8, 4))
    plt.plot(sem, [e_['estrellas_pos']*100 for e_ in r['evol_corpus']], marker='o', label='% 4-5 estrellas (corpus)')
    plt.plot(sem, [e_['lexico_pos']*100 for e_ in r['evol_corpus']], marker='s', label='% positivo según léxico (corpus)')
    sm = {e_['semestre']: e_['pos']*100 for e_ in r['evol']}
    plt.plot(sem, [sm.get(s) for s in sem], marker='^', linestyle='--', label='% positivo manual (muestra)')
    plt.ylabel('%'); plt.xlabel('Semestre'); plt.legend(); plt.grid(alpha=.3); plt.title('Evolución del sentimiento positivo')
    os.makedirs('resultados', exist_ok=True)
    plt.savefig('resultados/fig_evolucion_semestre.png', dpi=200, bbox_inches='tight'); plt.show()
except ImportError:
    print('matplotlib no está instalado; en Colab sí.')
''')
md('**Lectura.** ' +
   f'El sentimiento positivo **no es estable**: el % de reseñas de 4-5★ baja a {pc(minimo["estrellas_pos"])} en {minimo["semestre"]} (IC 95 %: {ci_min[0]*100:.0f}-{ci_min[1]*100:.0f} %) '
   f'y sube a {pc(ultimo["estrellas_pos"])} en {ultimo["semestre"]} ({ci_ult[0]*100:.0f}-{ci_ult[1]*100:.0f} %); esos intervalos no se tocan, así que la diferencia entre periodos es real y no ruido. '
   f'El léxico sigue a las estrellas de cerca: en los semestres con más de 50 reseñas nunca se separa más de {brecha_lex:.0f} puntos, aunque se equivoque en reseñas sueltas '
   '(los errores individuales se compensan al agregar). '
   f'La muestra manual cuenta la misma historia: {pc(sem_m["2025-S1"]["pos"])} de positivas en 2025-S1 y {pc(sem_m["2026-S1"]["pos"])} en 2026-S1; '
   f'su baja a {pc(sem_m["2026-S2"]["pos"])} en 2026-S2 está dentro del ruido de {sem_m["2026-S2"]["n"]} reseñas. '
   f'**Qué semestres son poco fiables:** 2024-S1 tiene {sem_c["2024-S1"]["n"]} reseñas en todo el corpus y solo {sem_m["2024-S1"]["n"]} en la muestra manual; 2024-S2 tiene {sem_c["2024-S2"]["n"]} y {sem_m["2024-S2"]["n"]} '
   'en la muestra. No se afirma nada de la muestra manual antes de 2025, y 2026-S2 llega solo hasta el 21 de octubre.')
md('### 4.7 ¿Qué se decía en cada semestre? Temas de queja')
codigo('''
import re
cols = list(ac.TEMAS)
cab = '| Semestre | n | Estrellas (prom.) | ' + ' | '.join(cols) + ' |'
tem = ac.temas_por_semestre(corpus)
mostrar('**% de las reseñas que mencionan cada tema (todas las estrellas)**\\n\\n' + cab + '\\n|' + '---|' * (3 + len(cols)) + '\\n' +
        '\\n'.join(f"| {t['semestre']} | {t['n']} | {t['estrellas_prom']:.2f} | " + ' | '.join(f"{t[c]*100:.0f} %" for c in cols) + ' |' for t in tem))
mostrar('**% de las reseñas de 1-2★ que mencionan cada tema**\\n\\n| Semestre | n (1-2★) | ' + ' | '.join(cols) + ' |\\n|' + '---|' * (2 + len(cols)) + '\\n' +
        '\\n'.join(f"| {t['semestre']} | {t['n_1_2']} | " + ' | '.join(f"{t[c + ' (1-2★)']*100:.0f} %" for c in cols) + ' |' for t in tem))
# Ejemplos reales: las primeras reseñas del cambio a plástico y reseñas de producto roto
def ejemplos(tema, desde, hasta, n=4):
    pat = re.compile(ac.TEMAS[tema], re.I)
    ej = sorted((x for x in corpus if x['estrellas'] <= 2 and desde <= x['fecha'][:7] <= hasta and pat.search(x['titulo'] + ' ' + x['texto'].lower())),
                key=lambda x: (x['fecha'], x['id']))
    print(f"{tema}: {len(ej)} reseñas de 1-2★ entre {desde} y {hasta}. Ejemplos:")
    for x in ej[:n]: print(f"- {x['fecha']} {x['estrellas']}★ | {x['titulo']} | {x['texto'][:230]}")
ejemplos('Cambio a botella de plastico', '2025-04', '2025-07')
ejemplos('Producto roto o derrame', '2024-09', '2025-03')
''')
md('**Lectura (hipótesis, no causa).** Aparecen dos historias distintas en el texto:', '',
   f'- **Producto roto o derramado en el envío:** {pc(t_24["Producto roto o derrame"])} de las reseñas de 2024-S2 y {pc(t_min["Producto roto o derrame"])} de las de {t_min["semestre"]} '
   f'({pc(t_min["Producto roto o derrame (1-2★)"])} de las de 1-2★), frente a {pc(t_ult["Producto roto o derrame"])} en {t_ult["semestre"]}. Son botellas de vidrio que llegan rotas ("broken glass bottle"). Parece un problema de empaque y envío que se resolvió.',
   '- **Cambio a botella de plástico y de "fórmula":** hay una primera reseña en diciembre de 2024 y se multiplican desde abril-mayo de 2025: '
   '"I received product on plastic bottle instead of glass. This is my third time buying this product" (5 de abril de 2025) y reseñas como la del 24 de mayo de 2025, '
   'que cuenta que las botellas cambiaron de vidrio a plástico y que el producto sabe "soooo different". '
   f'Las menciones del cambio a plástico son {pc(t_min["Cambio a botella de plastico"])} en {t_min["semestre"]} ({pc(t_min["Cambio a botella de plastico (1-2★)"])} de las de 1-2★) y bajan a {pc(t_ult["Cambio a botella de plastico"])} en {t_ult["semestre"]}; '
   f'las de cambio de fórmula o producto, de {pc(t_min["Cambio de formula o producto"])} a {pc(t_ult["Cambio de formula o producto"])}.', '',
   'Mayo de 2025 es además el primer mes de 2025 que marca el semáforo (§4.8): la caída del sentimiento coincide con el aumento de esas quejas. '
   'Es una pista para la organización, no una prueba: las palabras clave son amplias, una mención no dice si fue la razón de la nota, y la base se descargó filtrando por estrellas. '
   f'**Fecha aproximada del cambio, leída de las reseñas.** La primera mención del cambio a plástico es del {pl_primera}; antes de abril de 2025 hay {pl_antes_abr} en total, '
   f'en abril de 2025 hay {pl_mes["2025-04"]}, en mayo {pl_mes["2025-05"]}, en junio {pl_mes["2025-06"]} y en septiembre {pl_mes["2025-09"]}. '
   'Eso ubica el cambio, de forma aproximada, entre finales de abril y mayo de 2025 (el comprador reseña unos días después de recibir). '
   f'**La queja de "fórmula aguada" es anterior.** La primera mención de producto aguado, ralo o con fórmula distinta es del {ag_primera}; antes de abril de 2025 hay {ag_antes_abr} en total '
   f'y luego {ag_mes["2025-04"]} en abril, {ag_mes["2025-05"]} en mayo, {ag_mes["2025-06"]} en junio y {ag_mes["2025-09"]} en septiembre. '
   'Parece haber **dos problemas que se solapan**: quejas aisladas de producto aguado desde mediados de 2024 y una oleada en mayo-agosto de 2025 que coincide con el cambio a plástico. '
   'Para la decisión de revisar el lote o el proveedor (§1) eso importa: no es un solo evento. Las palabras clave son una aproximación, no un diagnóstico. '
   'Es la fecha que dicen los compradores, no la de la operación: el equipo no tiene las fechas reales del cambio de botella, de fórmula o de empaque y no están contrastadas.')
md('### 4.8 Ejemplo de uso: el tablero mensual con semáforo', '',
   'Caso concreto: cada mes el equipo mira el % de reseñas positivas según el léxico (sin entrenar nada nuevo). La regla tiene dos niveles y se mira cada mes con al menos 30 reseñas: '
   '**🔴 rojo** si el % positivo cae 10 puntos o más frente al promedio de los 3 meses anteriores (leer las reseñas negativas del mes y decidir); '
   '**🟡 amarillo** si cae entre 5 y 10 puntos (leerlas, sin actuar todavía). Se probó hacia atrás sobre todo el periodo (calibración más abajo).')
codigo('''
mens = ac.mensual(corpus, ac.lexico_proyecto())
alertas = {a['mes']: a for a in ac.alertas(mens, caida=0.10, n_min=30)}
amarillas = {a['mes']: a for a in ac.alertas(mens, caida=0.05, n_min=30) if a['mes'] not in alertas}
def luz(m):
    if m['mes'] in alertas: return f"🔴 vs {alertas[m['mes']]['referencia']*100:.0f} % previo"
    if m['mes'] in amarillas: return f"🟡 vs {amarillas[m['mes']]['referencia']*100:.0f} % previo"
    return '· (n < 30)' if m['n'] < 30 else '🟢'
mostrar('| Mes | n | % 4-5★ | % positivo (léxico) | Semáforo |\\n|---|---|---|---|---|\\n' +
        '\\n'.join(f"| {m['mes']} | {m['n']} | {m['estrellas_pos']*100:.0f} % | {m['lexico_pos']*100:.0f} % | " + luz(m) + ' |' for m in mens))
print('Meses en rojo:', sorted(alertas), '| en amarillo:', sorted(amarillas))
''')
md('**Lectura.** ' +
   f'La regla marca {len(alt)} meses: {", ".join(a["mes"] for a in alt)}. El primero de la crisis de 2025 es **{a25["mes"]}**: el léxico leyó {pc(a25["lexico_pos"])} de positivas contra {pc(a25["referencia"])} '
   f'de los tres meses anteriores, con {a25["n"]} reseñas; es decir, el tablero habría marcado la caída en el mes en que ocurrió y no al cierre del semestre. ' +
   (f'La regla también marca {a_ult["mes"]} ({pc(a_ult["lexico_pos"])} contra {pc(a_ult["referencia"])}); es un mes incompleto (datos hasta el 21) y puede ser ruido: '
    'justo para eso sirve el semáforo, para disparar la lectura de las reseñas negativas de ese mes antes de decidir nada. ' if a_ult else '') +
   f'El amarillo añade {len(amarillos)} meses ({", ".join(a["mes"] for a in amarillos)}).')
md('#### Calibración del umbral (prueba hacia atrás)', '',
   'Como no hay una tolerancia de falsas alarmas dada por el cliente, el umbral se escogió con una prueba hacia atrás. '
   '**"Evento real"** = el % de 4-5★ (las estrellas, no el léxico) cae 10 puntos o más frente a los 3 meses anteriores. '
   '**Acierto** = el semáforo se enciende en un mes con evento; **falsa alarma** = se enciende sin evento; **perdido** = hubo evento y no se encendió.')
codigo('''
bt = ac.backtest_alertas(mens)
mostrar('| Caída | n mín. | Meses evaluables | Eventos | Alertas | Aciertos | Falsas alarmas | Perdidos |\\n|---|---|---|---|---|---|---|---|\\n' +
        '\\n'.join(f"| {f['caida']*100:.0f} pts | {f['n_min']} | {f['meses_evaluables']} | {f['eventos']} | {f['alertas']} | {f['aciertos']} | {f['falsas_alarmas']} | {f['perdidos']} |" for f in bt))
''')
md('**Lectura.** ' +
   f'Con 10 puntos y 30 reseñas el semáforo da {bt_rojo["alertas"]} alertas en {bt_rojo["meses_evaluables"]} meses evaluables, todas con evento real ({bt_rojo["falsas_alarmas"]} falsas alarmas), '
   f'pero pierde {bt_rojo["perdidos"]} de {bt_rojo["eventos"]} eventos ({bt_rojo["meses_perdidos"]}). Bajar a 5 puntos recupera eventos ({bt_amar["aciertos"]} de {bt_amar["eventos"]}) '
   f'a cambio de {bt_amar["falsas_alarmas"]} falsa alarma ({bt_amar["meses_falsas"]}). Como el error más caro es dejar pasar una queja (§1), se propone el **doble nivel**: '
   f'rojo desde 10 puntos y amarillo desde 5, que en esta base son {bt_amar["alertas"]} meses con luz en {bt_amar["meses_evaluables"]} evaluables, es decir, unas {bt_amar["alertas"] / bt_amar["meses_evaluables"] * 10:.0f} lecturas de reseñas cada 10 meses (rojos incluidos). '
   f'Con 30 reseñas el margen de error de un porcentaje mensual es de unos {(ac.wilson(15, 30)[1] - ac.wilson(15, 30)[0]) * 50:.0f} puntos, así que un solo mes amarillo no es prueba de nada: sirve para leer, no para decidir. '
   f'**Limitaciones:** son pocos meses ({bt_rojo["meses_evaluables"]}), el "evento real" sale de las mismas reseñas que alimentan el léxico y la base se descargó filtrando por estrellas, '
   'así que esto compara umbrales y no promete un desempeño futuro. Cuántas falsas alarmas al mes tolera el cliente sigue siendo un dato por confirmar con él.')
md('### 4.9 Segunda lectura: léxico + KNN (y una tercera con Naive Bayes)', '',
   '**Qué se hace.** El error caro es la queja leída como elogio (§1). El léxico es transparente pero deja pasar muchas; el KNN lee distinto. '
   'La **segunda lectura** marca como queja toda reseña que el léxico **o** el KNN marquen: el KNN revisa lo que el léxico dejó como positivo. '
   'La **tercera lectura** suma Naive Bayes. Se comparan también el voto de 2 de 3 y otras reglas simples. '
   'Son 8 reglas fijas, definidas antes de ver los resultados y **sin parámetros que ajustar**, para no sobreajustar con tan pocas negativas. '
   'Se miden en las mismas reseñas de prueba que la Prueba A (estrellas) y en las 85 de la Prueba B (ningún modelo entrenó con ellas; el léxico es el que no vio la muestra). '
   'Para cada regla: fp = queja leída como elogio, fn = falsa alarma, **% marcadas** = qué parte de las reseñas habría que leer, '
   'y un **costo** = c × fp + fn, donde c es cuántas veces pesa más dejar pasar una queja que una falsa alarma (c no se midió en dinero: es un juicio de quien decide. **Se fijó c = 5 como razón de trabajo** porque en §1 se dijo que la queja que se escapa cuesta reputación y tiempo y la falsa alarma solo tiempo; **se fijó después de ver las tablas**, así que es un grado de libertad más. Por eso se muestran también c = 1, 2 y 3 y el valor de c desde el cual cambia la conclusión).')
codigo('''
costos = (1, 2, 3, 5)
yb_ = r['y_bin'][r['bin_ok']]; ok_ = r['bin_ok']; pb_ = r['punt']
tablas = {'Prueba A (estrellas)': ac.segunda_lectura(e['y_test'], e['punt']['Lexico (aprendido con el 80 %)'], e['punt']['KNN'], e['punt']['Naive Bayes']),
          'Prueba B (muestra manual, n = %d)' % len(yb_): ac.segunda_lectura(yb_, pb_['Lexico sin la muestra'][ok_], pb_['KNN con estrellas'][ok_], pb_['Naive Bayes con estrellas'][ok_])}
for titulo, filas_ in tablas.items():
    mostrar(f"**{titulo}: {filas_[0]['n']} reseñas**\\n\\n| Regla | fp (quejas escapadas) | fn (falsas alarmas) | Especificidad | Sensibilidad | Exactitud | % marcadas | " +
            ' | '.join(f'Costo c={c}' for c in costos) + ' |\\n|' + '---|' * (7 + len(costos)) + '\\n' +
            '\\n'.join(f"| {f['regla']} | {f['fp']} | {f['fn']} | {f['especificidad']:.3f} | {f['sensibilidad']:.3f} | {f['exactitud']:.3f} | {f['pct_marcadas']*100:.0f} % | " +
                      ' | '.join(str(f[f'costo_c{c}']) for c in costos) + ' |' for f in filas_))
''')
def _g(g): return {c: ' / '.join(v) for c, v in g.items()}
md('**Lectura.** ' +
   f'**La segunda lectura reduce mucho las quejas que se escapan:** en la Prueba A pasa de {sa_lex["fp"]} a {sa_2["fp"]} ({sa_lex["especificidad"]:.3f} a {sa_2["especificidad"]:.3f} de especificidad) '
   f'y en la B de {sb_lex["fp"]} a {sb_2["fp"]}. Como la regla es una unión, atrapa todo lo que atrapaba el léxico más {_cogidas_a} quejas nuevas en A '
   f'(y ninguna se pierde: {_cogidas_a} de {_cogidas_a} casos distintos van a su favor, p = {0.5 ** _cogidas_a:.4f} en una prueba de signos exacta). '
   f'En B son {_cogidas_b} casos, demasiado pocos para llamarlo significativo (p = {0.5 ** max(_cogidas_b, 1):.2f}), pero va en el mismo sentido. '
   f'**El precio:** {_extra_fa_a} falsas alarmas más en A (fn de {sa_lex["fn"]} a {sa_2["fn"]}) y hay que leer {sa_2["pct_marcadas"]*100:.0f} % de las reseñas en lugar de {sa_lex["pct_marcadas"]*100:.0f} %.', '',
   f'**La tercera lectura no aporta:** sumar Naive Bayes no baja las quejas escapadas en A (quedan {sa_3["fp"]}, igual que con la segunda) y suma {sa_3["fn"] - sa_2["fn"]} falsa(s) alarma(s) más, así que no se justifica un tercer modelo.', '',
   f'**¿Cuál regla gana?** Con la razón de trabajo c = {C_BASE}, la segunda lectura es la de menor costo en A ({sa_2["costo_c5"]} contra {min(f["costo_c5"] for f in sl_a if f["regla"] not in (_R2, "Léxico O KNN O NB (tercera lectura)"))} de la mejor otra regla, sin contar la tercera lectura, que es la misma con un lector más) y en B ({sb_2["costo_c5"]} contra {min(f["costo_c5"] for f in sl_b if f["regla"] not in (_R2, "Léxico O KNN O NB (tercera lectura)"))}). Pero depende de c. Menor costo en A: ' + '; '.join(f'c = {c}: {v}' for c, v in _g(gan_a).items()) + '. '
   'Menor costo en B: ' + '; '.join(f'c = {c}: {v}' for c, v in _g(gan_b).items()) + '. '
   f'**Umbral:** la segunda lectura cuesta lo mismo o menos que cualquier otra regla desde c = {cq_a:g} en A (en c = {cq_a:g} empata con KNN O NB, y gana cuando pesa más) y desde c = {cq_b:g} en B. Si quien decide cree que dejar pasar una queja pesa menos de {cq_a:g} veces una falsa alarma, el voto de 2 de 3 o KNN con Naive Bayes cuestan menos. '
   '**Límites:** la Prueba A usa las estrellas como etiqueta; B tiene solo 33 negativas; la segunda lectura se escogió entre 8 reglas mirando A y B, así que su ventaja puede estar algo inflada '
   '(por eso conviene reproducirla con las hojas de ampliación cuando se etiqueten).')
md('### 4.10 Agrupamiento: ¿de qué hablan los compradores? (k-means)', '',
   '**Qué se hace.** Un modelo de otra familia: en vez de leer el sentimiento, agrupa las reseñas por su texto. Se usa toda la base preparada '
   f'({len(prep)} reseñas): como no hay etiqueta que predecir no hay partición entrenamiento/prueba, y los grupos se juzgan con variables que **no entraron al modelo** '
   '(estrellas, semestre, compra verificada). **Preparación:** mismo texto limpio del KNN, TF-IDF de palabras y parejas, resumen a 30 ejes (SVD) y normalización. '
   '**Número de grupos:** para *k* de 2 a 8 se mide la inercia (codo), la silueta con distancia coseno y la estabilidad (qué tan iguales salen los grupos con 5 semillas distintas, índice de Rand ajustado: 1 = idénticos). '
   'La regla, fijada antes de mirar los grupos, es el primer *k* ≥ 3 cuya silueta es máximo local y cuya estabilidad es ≥ 0,9.')
codigo('''
ag = ac.agrupar(prep)                                   # k-means sobre TF-IDF + SVD; escoge k con silueta y estabilidad
et_g = ag['etiquetas']
mostrar('**Cómo se escogió k**\\n\\n| k | Inercia | Silueta | Estabilidad | Grupo más pequeño |\\n|---|---|---|---|---|\\n' +
        '\\n'.join(f"| {t['k']}{' ←' if t['k'] == ag['k'] else ''} | {t['inercia']:.0f} | {t['silueta']:.3f} | {t['estabilidad']:.2f} | {t['tam_min']} |" for t in ag['tabla']))
perfil = ac.perfil_grupos(prep, et_g); por_sem = ac.grupos_por_semestre(prep, et_g)
temas_g = [t for t in ac.TEMAS if t in perfil[0]]
mostrar('**Perfil de cada grupo (variables que no entraron al modelo y, como ayuda de lectura, temas de queja)**\\n\\n| Grupo | n | % | Estrellas | % 4-5★ | % verificada | ' + ' | '.join(temas_g) + ' |\\n|' + '---|' * (6 + len(temas_g)) + '\\n' +
        '\\n'.join(f"| {p['grupo']} | {p['n']} | {p['pct']*100:.0f} % | {p['estrellas_prom']:.2f} | {p['pct_4_5']*100:.0f} % | {p['pct_verificada']*100:.0f} % | " + ' | '.join(f"{p[t]*100:.0f} %" for t in temas_g) + ' |' for p in perfil))
for g_, t_ in ag['top_terminos'].items(): print(f"Grupo {g_}: " + ', '.join(t_))
mostrar('**Qué parte de cada semestre cae en cada grupo**\\n\\n| Semestre | n | ' + ' | '.join(f'Grupo {g_}' for g_ in sorted(set(et_g.tolist()))) + ' |\\n|---|---|' + '---|' * len(set(et_g.tolist())) + '\\n' +
        '\\n'.join(f"| {x['semestre']} | {x['n']} | " + ' | '.join(f"{x[f'grupo_{g_}']*100:.0f} %" for g_ in sorted(set(et_g.tolist()))) + ' |' for x in por_sem))
try:
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ks = [t['k'] for t in ag['tabla']]
    ax[0].plot(ks, [t['silueta'] for t in ag['tabla']], marker='o', label='Silueta'); ax[0].plot(ks, [t['estabilidad'] for t in ag['tabla']], marker='s', label='Estabilidad')
    ax[0].axvline(ag['k'], color='gray', linestyle=':'); ax[0].set_xlabel('Número de grupos k'); ax[0].legend(); ax[0].grid(alpha=.3); ax[0].set_title('Cómo se escogió k')
    sems = [x['semestre'] for x in por_sem if x['n'] >= 30]
    abajo = [0] * len(sems)
    for g_ in sorted(set(et_g.tolist())):
        v = [x[f'grupo_{g_}'] * 100 for x in por_sem if x['n'] >= 30]
        ax[1].bar(sems, v, bottom=abajo, label=f'Grupo {g_}'); abajo = [a_ + b_ for a_, b_ in zip(abajo, v)]
    ax[1].set_ylabel('% de las reseñas del semestre'); ax[1].legend(loc='upper center', bbox_to_anchor=(0.5, -0.08), ncol=3); ax[1].set_title('Los grupos a lo largo del tiempo (semestres con n ≥ 30)')
    plt.savefig('resultados/fig_agrupamiento.png', dpi=200, bbox_inches='tight'); plt.show()
except ImportError:
    print('matplotlib no está instalado; en Colab sí.')
''')
_nm = {g_queja['grupo']: 'queja de producto', g_elogio['grupo']: 'elogio general', g_mixto['grupo']: 'sabor y cómo me siento'}
_gq = f'grupo_{g_queja["grupo"]}'
md('**Lectura.** ' +
   f'La regla escoge **k = {ag["k"]}** (silueta {next(t for t in ag["tabla"] if t["k"] == ag["k"])["silueta"]:.3f}, estabilidad {next(t for t in ag["tabla"] if t["k"] == ag["k"])["estabilidad"]:.2f}). '
   'La silueta es baja en todos los *k* (el texto de las reseñas no se separa en grupos nítidos: hablan de lo mismo con matices) y sube sin parar con *k* a costa de grupos pequeños e inestables, '
   'así que el codo no es claro; por eso se exige también estabilidad. Los tres grupos:', '',
   f'- **Grupo {g_elogio["grupo"]}, {_nm[g_elogio["grupo"]]}** ({pc(g_elogio["pct"])}): palabras como {", ".join(ag["top_terminos"][g_elogio["grupo"]][:5])}; {g_elogio["estrellas_prom"]:.2f}★ de promedio y {pc(g_elogio["pct_4_5"])} de 4-5★.',
   f'- **Grupo {g_queja["grupo"]}, {_nm[g_queja["grupo"]]}** ({pc(g_queja["pct"])}): palabras como {", ".join(ag["top_terminos"][g_queja["grupo"]][:5])}; {g_queja["estrellas_prom"]:.2f}★ y solo {pc(g_queja["pct_4_5"])} de 4-5★. '
   f'{pc(g_queja["Cambio a botella de plastico"])} menciona el cambio a plástico, {pc(g_queja["Formula aguada o diluida"])} la fórmula aguada y {pc(g_queja["Producto roto o derrame"])} producto roto o derramado.',
   f'- **Grupo {g_mixto["grupo"]}, {_nm[g_mixto["grupo"]]}** ({pc(g_mixto["pct"])}): palabras como {", ".join(ag["top_terminos"][g_mixto["grupo"]][:5])}; {g_mixto["estrellas_prom"]:.2f}★. '
   f'{pc(g_mixto["Sabor"])} habla del sabor: es el tema de conversación, no necesariamente una queja ({pc(g_mixto["pct_4_5"])} da 4-5★).', '',
   f'**Lo que aporta frente a los otros modelos:** el grupo de queja de producto pasa de {pc(next(x for x in sem_g if x["semestre"] == "2024-S2")[_gq])} de las reseñas en 2024-S2 a **{pc(sg_pico[_gq])} en {sg_pico["semestre"]}** '
   f'y baja a {pc(sg_ult[_gq])} en {sg_ult["semestre"]}. Cuenta **la misma historia que el semáforo y los temas de §4.7, pero sin usar estrellas ni palabras clave para armar los grupos**, '
   'lo que es coherente con que la crisis de 2025 fue una queja de producto (botella, envío y fórmula) y no solo un mal humor general, aunque no lo prueba. '
   '**Límites:** los grupos son una descripción, no una prueba de causa; la silueta baja indica fronteras difusas (una reseña puede hablar de sabor y de plástico a la vez); '
   'los temas de queja del perfil se calculan con palabras clave del mismo texto, así que no son una validación independiente; y los nombres de los grupos los pone el equipo al leerlos.')
md('### Exportar tablas para el documento y las diapositivas')
codigo('''
import csv
os.makedirs('resultados', exist_ok=True)
def guardar_csv(nombre, filas_csv):
    with open(f'resultados/{nombre}', 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas_csv[0])); w.writeheader(); w.writerows(filas_csv)
for nombre, res in (('metricas_prueba_A_estrellas.csv', e['prueba']), ('metricas_prueba_B_manual_20.csv', r['prueba']), ('metricas_prueba_B_manual_completa.csv', r['todas'])):
    guardar_csv(nombre, [{'modelo': m, **v} for m, v in res.items()])
guardar_csv('evolucion_muestra_manual.csv', r['evol'])
guardar_csv('evolucion_corpus.csv', r['evol_corpus'])
guardar_csv('temas_por_semestre.csv', tem)
guardar_csv('tablero_mensual.csv', [{**m, 'rojo': m['mes'] in alertas, 'amarillo': m['mes'] in amarillas} for m in mens])
guardar_csv('calibracion_semaforo.csv', bt)
guardar_csv('agrupamiento_k.csv', ag['tabla']); guardar_csv('agrupamiento_perfil.csv', perfil); guardar_csv('agrupamiento_por_semestre.csv', por_sem)
for _t, _f in tablas.items(): guardar_csv('segunda_lectura_' + ('A' if _t.startswith('Prueba A') else 'B') + '.csv', _f)
guardar_csv('desacuerdos_lexico.csv', [dict(manual=c[0], lexico=c[1], puntaje=c[2], titulo=c[3], texto=c[4]) for c in casos])
print('Guardado en resultados/:', sorted(os.listdir('resultados')))
''')

md('## 5. Recomendaciones para la decisión', '',
   '1. **Instalar un tablero mensual de sentimiento con el léxico** (no necesita entrenar nada, es transparente y sigue a las estrellas a menos de '
   f'{brecha_lex:.0f} puntos por semestre) y la regla de semáforo de dos niveles de §4.8. Cuando el semáforo se pone amarillo o rojo, **leer las reseñas negativas de ese mes antes de actuar**.',
   '2. **Para decidir a qué quejas responder o reembolsar, usar una segunda lectura (léxico O KNN).** El error que más cuesta es dejar pasar una queja. '
   f'La segunda lectura baja las quejas escapadas de {sa_lex["fp"]} a {sa_2["fp"]} en la Prueba A y de {sb_lex["fp"]} a {sb_2["fp"]} en la B, a cambio de {_extra_fa_a} falsas alarmas más en A '
   f'y de leer {sa_2["pct_marcadas"]*100:.0f} % de las reseñas en lugar de {sa_lex["pct_marcadas"]*100:.0f} % (§4.9). Un tercer modelo (Naive Bayes) no mejora. '
   'La conclusión es más firme en A (estrellas) que en B (solo 33 negativas) y depende de cuánto más caro sea dejar pasar una queja que una falsa alarma: '
   f'con la razón de trabajo c = {C_BASE} (una queja escapada pesa 5 falsas alarmas, fijada después de ver las tablas) la segunda lectura es la de menor costo, y lo es desde c = {cq_a:g}; si el cliente la juzga menos grave que eso, el voto de 2 de 3 cuesta menos. Ese peso hay que confirmarlo con el cliente.',
   f'3. **Contrastar las dos hipótesis de §4.7 con lo que realmente cambió en la operación:** los daños en el envío (ya casi no aparecen) y el cambio de botella y de fórmula. Si se confirman, el costo se puede estimar con la caída de {pc(minimo["estrellas_pos"])} frente a {pc(ultimo["estrellas_pos"])} de reseñas positivas. '
   'El equipo no tiene esas fechas: hay que pedirlas a quien opera el producto antes de decidir.',
   f'4. **Vigilar también de qué se habla, no solo cuánto gusta:** el agrupamiento de §4.10 separa un grupo de queja de producto (botella, envío, fórmula) que llegó a {pc(sg_pico[_gq])} de las reseñas en {sg_pico["semestre"]}. '
   'Seguir su peso por mes complementa al semáforo de sentimiento: avisa **qué** está fallando, que es lo que hace falta para decidir si revisar el lote o al proveedor.',
   '5. **No usar estos modelos** para reseñas en otro idioma, para clasificar Neutro ni como único criterio ante una crisis: el léxico lee mal lo mixto y lo irónico (§4.5).', '',
   '**Qué se mediría después:** el % positivo por mes con intervalo de confianza, las alertas que fueron falsas alarmas, y cuántas de las reseñas negativas de un mes marcado terminan en una acción concreta. '
   '**Riesgo de confiar en el modelo:** una caída leída como falsa alarma por exceso de confianza; por eso la regla manda a leer reseñas y no a decidir sola.')
md('## 6. Limitaciones y trabajo futuro', '',
   f'- **Tamaño de la muestra manual ({r["n"]}; {r["n_test_bin"]} en la prueba).** Los intervalos son muy anchos: no se puede ordenar a los modelos con ella (§4.2). Efecto: la comparación se apoya en la prueba A (estrellas). '
   'Trabajo futuro: etiquetar las 400 reseñas de las hojas de ampliación y repetir (el notebook las incluye solas cuando estén completas).',
   f'- **Neutro fuera de las métricas binarias.** Son {cnt["Neutro"]} de {r["n"]}; los modelos binarios no tienen cómo decirlas y el léxico casi nunca las acierta. Efecto: el acierto real sobre texto ambiguo es menor que el reportado.',
   '- **La etiqueta de la prueba A es la nota en estrellas,** que no siempre coincide con el texto. Efecto: algunos errores de modelo son en realidad errores de la etiqueta.',
   '- **Idioma:** todo en inglés; una reseña en español queda sin leer. Efecto: no sirve tal cual para otros mercados.',
   '- **Periodo y fuente.** Unos 2,4 años, un producto, un canal y reseñas descargadas por filtros de estrellas; los semestres 2024-S1 y 2024-S2 tienen muy pocas reseñas y 2026-S2 es parcial. '
   'Efecto: la evolución se puede describir pero no pronosticar; la comparación con los 4 años exigidos queda pendiente de la aprobación del profesor.',
   '- **Agrupamiento (§4.10):** la silueta es baja (los grupos se solapan) y los nombres los pone quien los lee. Efecto: sirve para describir de qué se habla, no para asignar con certeza cada reseña a un tema.',
   '- **Qué no hace el modelo:** no explica por qué cambia el sentimiento; las pistas de §4.7 son palabras clave, no causas.')

nb = {'cells': CELDAS, 'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
      'language_info': {'name': 'python'}, 'colab': {'provenance': []}}, 'nbformat': 4, 'nbformat_minor': 5}
for i, c in enumerate(CELDAS):
    c['id'] = f'c{i:02d}'
    c['source'] = c['source'].splitlines(keepends=True)
destino = RAIZ / 'Trabajo_Final_Resenas.ipynb'
destino.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'{len(CELDAS)} celdas -> {destino}')
