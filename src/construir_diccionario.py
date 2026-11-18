#!/usr/bin/env python3
"""C2: diccionario reproducible y etiquetado local, sin red ni LLM.
Ejecutar con el venv NLP y -I; el corpus fuente nunca se modifica.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
from functools import lru_cache
import importlib.util
import json
import math
from pathlib import Path
import random
import re
import sqlite3
import sys

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
DEFAULT = ROOT / 'data'
VERSION = 'propio_v1'


def local(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def norm(text):
    return str(text or '').lower().replace('’', "'")


@lru_cache(maxsize=None)
def pattern(term):
    return re.compile(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])")


def matches(term, text):
    return bool(pattern(term).search(norm(text)))


def negated(term, text):
    # Evita interpretar «not happy» o «doesn't work» como satisfacción/mejora.
    return bool(re.search(r"\b(?:not|no|never|don't|doesn't|didn't|did not|does not|do not)\s+(?:\w+\s+){0,2}" + re.escape(term) + r'\b', norm(text)))


def write_csv(path, rows, headers):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def preservar_correcciones(path, sample):
    """Actualiza etiquetas automaticas sin perder ninguna columna manual por ID."""
    if not path.exists():
        return
    with path.open(encoding='utf-8-sig', newline='') as f:
        previous = list(csv.DictReader(f))
    corrections = {row['id']: {k:v for k,v in row.items() if k.endswith('_manual')} for row in previous}
    ids = {row['id'] for row in sample}
    if any(any(v for v in fixes.values()) and rid not in ids for rid,fixes in corrections.items()):
        raise RuntimeError('Cambiar muestra perderia correcciones humanas')
    manual_keys = sorted({k for fixes in corrections.values() for k in fixes})
    for row in sample:
        for key in manual_keys:
            row[key] = corrections.get(row['id'], {}).get(key, row.get(key, ''))


def build(folder, db):
    import nltk
    from nltk.corpus import wordnet, brown
    # Lista inglesa fija para reproducibilidad, sin descargas de stopwords.
    ENGLISH_STOP_WORDS = set("a an the and or but if while of at by for with about against between into through during before after above below to from up down in out on off over under again further then once here there when where why how all any both each few more most other some such only own same so than too very can will just should now i me my myself we our ours ourselves you your yours yourself yourselves he him his himself she her hers herself it its itself they them their theirs themselves what which who whom this that these those am is are was were be been being have has had having do does did doing would could shall may might must as until because also get got really much many still ever never not no nor don't doesn't didn't i'm i've i'll it's that's can't won't isn't wasn't weren't aren't couldn't wouldn't don't".split())
    # No descarga implícita de datos. WordNet local es la alternativa prevista.
    nltk.data.path.insert(0, str(ROOT / 'diccionarios_nlp/wordnet'))
    try:
        reference = Counter(norm(w) for w in brown.words() if w.isalpha())
        baseline = 'Brown: frecuencias de tokens'
    except LookupError:
        reference = Counter()
        for syn in wordnet.all_synsets():
            for lemma in syn.lemmas():
                if lemma.count():
                    reference[norm(lemma.name()).replace('_', ' ')] += lemma.count()
        baseline = 'WordNet: conteos de uso de lemas (proxy; no corpus general balanceado)'
    stop = set(ENGLISH_STOP_WORDS) | {'im', 'ive', 'dont', 'didnt', 'doesnt', 'isnt', 'wasnt', 'couldnt', 'wouldnt'}
    source = folder / 'serene_resenas_amazon_v3.json'
    reviews = json.loads(source.read_text())
    texts = [norm(r.get('titulo', '') + '. ' + r.get('texto', '')) for r in reviews]
    counts = Counter(); by_star = defaultdict(Counter)
    for r, text in zip(reviews, texts):
        # No unir a través de stopwords ni puntuación para inventar frases.
        tokens = re.findall(r"[a-z]+(?:'[a-z]+)?|[.!?,;:]", text)
        for n in (1, 2, 3):
            terms = [' '.join(tokens[i:i+n]) for i in range(len(tokens)-n+1)
                     if all(t not in stop and re.fullmatch(r"[a-z]+(?:'[a-z]+)?", t) for t in tokens[i:i+n])]
            counts.update(terms)
            by_star[int(float(str(r['estrellas']).split()[0]))].update(terms)
    tax = local('taxonomia_resenas')
    manual = json.loads((TOOLS / 'diccionario_salud_resenas.json').read_text())
    candidates = json.loads((folder / 'diccionario_candidatos.json').read_text())
    groups = {k: defaultdict(dict) for k in ['temas', 'temas_producto', 'emociones', 'slang', 'resultado', 'regiones']}
    def add(section, group, term, origin):
        term = norm(term).replace('_', ' ').strip()
        if not term or len(term.split()) > 4:
            return
        current = groups[section][group].setdefault(term, {'termino': term, 'fuentes': [], 'frecuencia': sum(len(re.findall(r'(?<![a-z0-9])' + re.escape(term) + r'(?![a-z0-9])', t)) for t in texts), 'resenas': sum(matches(term, t) for t in texts)})
        if origin not in current['fuentes']:
            current['fuentes'].append(origin)
    for section in ['temas', 'emociones', 'resultado']:
        for group, terms in manual[section].items():
            for term in terms:
                add(section, group, term, 'manual')
    for group, data in candidates.items():
        for item in data['terminos']:
            for term in [item['termino']] + item.get('sinonimos', []):
                add('temas', group, term, item['fuente'])
    for group, terms in {
        'digestion': ['gut health', 'bubble guts'], 'estrenimiento': ['number two', 'backed up'],
        'diarrea_nausea': ['the runs', 'runs', 'watery stool'],
    }.items():
        for term in terms:
            add('temas', group, term, 'manual')
    groups['temas'] = tax.fusionar(groups['temas'])
    # Seleccion determinista: vocabulario util revisado, frecuencia literal en v3.
    useful = []
    for group, terms in tax.CANDIDATOS.items():
        for term in terms.split('|'):
            freq = sum(len(pattern(term).findall(t)) for t in texts)
            if freq:
                useful.append({'termino':term, 'tema':group, 'frecuencia':freq,
                               'estrella_1':sum(len(pattern(term).findall(t)) for r,t in zip(reviews,texts) if str(r['estrellas']).startswith('1')),
                               'estrella_5':sum(len(pattern(term).findall(t)) for r,t in zip(reviews,texts) if str(r['estrellas']).startswith('5'))})
    useful.sort(key=lambda e:(-e['frecuencia'],e['termino'],e['tema']))
    selected = useful[:150]
    if len({e['termino'] for e in selected}) != 150:
        raise ValueError('Se requieren 150 terminos utiles distintos presentes en el corpus')
    write_csv(folder/'terminos_producto_top150.csv', selected,
              ['termino','tema','frecuencia','estrella_1','estrella_5'])
    for e in selected:
        add('temas_producto', e['tema'], e['termino'], 'corpus')
        add('temas_producto', e['tema'], e['termino'], 'manual')
    for group, terms in tax.SEMILLAS.items():
        for term in terms.split('|'):
            add('temas_producto', group, term, 'manual')
    slang = ['legit', 'game changer', 'gut', 'bloated', "ain't", 'hits different', 'sketchy', 'scam', 'the runs', 'backed up', 'poop', 'gonna', 'yall', "y'all", 'tummy', 'rip off']
    for term in slang:
        add('slang', 'coloquial_eeuu', term, 'manual')
    excel = local('resenas_amazon_excel')
    demo = local('demografia_resenas').Demografia(excel)
    for state, (region, _) in excel.ESTADOS.items():
        add('regiones', region, state, 'manual')
    for city, state in excel.CIUDADES.items():
        add('regiones', excel.ESTADOS[state][0], city, 'manual')
    for term, region in excel.REGIONES_VAGAS.items():
        add('regiones', region, term, 'manual')
    result = {'_meta': {'version': VERSION, 'fuente': source.name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'resenas': len(reviews), 'referencia': baseline, 'frecuencia': 'ocurrencias literales; resenas = frecuencia documental', 'advertencia': 'Menciones automaticas; no diagnosticos, causalidad ni residencia. Requiere validacion humana.'}}
    for section, categories in groups.items():
        result[section] = {group: sorted(entries.values(), key=lambda x: (-x['frecuencia'], x['termino'])) for group, entries in sorted(categories.items())}
    result['_meta']['taxonomia'] = {'version':'v3', 'alias_salud':tax.ALIASES, 'canon_salud':sorted(tax.CANONICOS), 'producto_top':len(selected), 'criterio':'Top 150 por ocurrencias literales entre candidatos utiles revisados; se conservan ademas las semillas solicitadas. Menciones no son quejas.'}
    demo.agregar_diccionario(result, texts)
    result['_meta']['demografia'] = {'version': 'v2', 'nombres': demo.names_source, 'confianza': 'alta: texto explicito o acuerdo nombre-texto; media: solo nombre; baja: indirecta, unisex, conflicto o ausencia', 'zona': '4 regiones/9 divisiones censales; mencion no residencia; sin division si indeterminada'}
    for entries in result['genero_nombres'].values():
        for e in entries:
            e['frecuencia'] = sum(len(re.findall(pattern(e['termino']).pattern, norm(r.get('nombre','')))) for r in reviews)
            e['resenas'] = sum(matches(e['termino'], r.get('nombre','')) for r in reviews)
    (folder / 'diccionario_propio_v1.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    total = sum(counts.values()); ref_total = sum(reference.values())
    vocab = len(set(counts) | set(reference))
    ranking = []
    for term, freq in counts.items():
        # Log odds suavizado; bigramas/trigramas con referencia 0 en WordNet son aproximados.
        a = freq + .5; b = reference[term] + .5
        odds = math.log(a / (total + .5*vocab-a)) - math.log(b / (ref_total + .5*vocab-b))
        parts = term.split()
        subterms = {' '.join(parts[i:j]) for i in range(len(parts)) for j in range(i+1,len(parts)+1)}
        covered = sorted(group for section in ('temas','temas_producto') for group, entries in groups[section].items() if subterms.intersection(entries))
        ranking.append({'termino': term, 'n': len(term.split()), 'frecuencia': freq, 'estrella_1': by_star[1][term], 'estrella_5': by_star[5][term], 'log_odds': round(odds, 4), 'temas': '|'.join(covered)})
    ranking.sort(key=lambda x: (-x['frecuencia'], -x['log_odds'], x['termino']))
    headers = ['termino', 'n', 'frecuencia', 'estrella_1', 'estrella_5', 'log_odds', 'temas']
    write_csv(folder / 'frecuencias_corpus.csv', ranking, headers)
    unknown = [r for r in ranking if not r['temas']][:300]
    write_csv(folder / 'terminos_sin_clasificar.csv', unknown, headers)
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        all_rows = [dict(r) for r in conn.execute('SELECT * FROM resenas ORDER BY id')]
        with conn:
            conn.execute('INSERT OR REPLACE INTO diccionarios VALUES (?,datetime("now"),?)', (VERSION, json.dumps(result['_meta'], ensure_ascii=False)))
            tax.migrar_etiquetas(conn, VERSION)
            conn.execute('DELETE FROM etiquetas WHERE version_dicc=?', (VERSION,))
            labels = {}
            demographics = {}
            for r in all_rows:
                text = norm(r['titulo'] + '. ' + r['texto'])
                tags = defaultdict(list)
                for section, kind in [('temas', 'tema_salud'), ('emociones', 'emocion'), ('resultado', 'resultado')]:
                    for group, entries in result[section].items():
                        found = [e for e in entries if matches(e['termino'], text) and not (section in ('emociones', 'resultado') and negated(e['termino'], text))]
                        if found:
                            tags[kind].append((group, len(found)))
                product_hits = tax.operativos(text, result['temas_producto'])
                tags['tema_producto'] = [(group,len(terms)) for group,terms in product_hits.items()]
                tags['evidencia_producto'] = [(json.dumps(product_hits,ensure_ascii=False),1)]
                tags['queja_producto'] = [(group,1) for group in tax.quejas(text,product_hits)]
                # «love it» no prueba resultado de salud: mejora exige verbo explícito.
                improvement = ['helped', 'helps', 'works', 'worked', 'working', 'relief', 'relieved', 'improved', 'improvement', 'feeling better', 'noticed a difference']
                tags['resultado'] = [(g, n) for g, n in tags['resultado'] if g != 'mejora' or any(matches(t, text) and not negated(t, text) for t in improvement)]
                original = r['titulo'] + '. ' + r['texto']
                gen = demo.genero(r['nombre'], original)
                geo = demo.zona(original)
                demographics[r['id']] = {'genero': gen, 'zona': geo}
                gender_source = 'texto' if gen['evidencia'] else 'nombre'
                tags['genero'].append((gen['genero'], 1))
                tags['genero_confianza'].append((gen['confianza'], 1))
                tags['genero_evidencia'].append((json.dumps(gen, ensure_ascii=False), 1))
                tags['zona_detalle'].append((json.dumps(geo, ensure_ascii=False), 1))
                for kind, field in [('zona', 'region'), ('estado', 'estado'), ('division', 'division')]:
                    tags[kind] = [(v, 1) for v in sorted({m[field] for m in geo['menciones'] if m[field]})]
                tags['origen_cultural'] = [(v, 1) for v in sorted({m['origen'] for m in geo['cultural'] if m['tipo']=='autorreferencia'})]
                score = excel.vader.polarity_scores(text)['compound']
                tags['sentimiento'].append(('Positivo' if score >= .05 else 'Negativo' if score <= -.05 else 'Neutral', 1))
                for kind, values in tags.items():
                    values.sort(key=lambda x: (-x[1], x[0]))
                    for value, _ in values:
                        origin = 'VADER' if kind == 'sentimiento' else 'genero_estimado:' + gender_source if kind == 'genero' else 'reglas'
                        conn.execute('INSERT INTO etiquetas VALUES (?,?,?,?,?)', (r['id'], kind, value, origin, VERSION))
                labels[r['id']] = {k: '|'.join(v for v, _ in vals) for k, vals in tags.items()}
        source_ids = {r['id'] for r in reviews}
        assert source_ids <= {r['id'] for r in all_rows}
        corpus_rows = [r for r in all_rows if r['id'] in source_ids]
        rng = random.Random(20261025)
        quotas = {s: int(100*sum(r['estrellas']==s for r in corpus_rows)/len(reviews)) for s in range(1,6)}
        remainder = sorted(quotas, key=lambda s: (-(100*sum(r['estrellas']==s for r in corpus_rows)/len(reviews)-quotas[s]), s))
        for s in remainder[:100-sum(quotas.values())]: quotas[s] += 1
        sample = []
        for s in range(1,6):
            for r in rng.sample([r for r in corpus_rows if r['estrellas']==s], quotas[s]):
                sample.append({k:r[k] for k in ['id', 'estrellas', 'titulo', 'texto']} | {k:labels[r['id']].get(k, '') for k in ['tema_salud','tema_producto','evidencia_producto','queja_producto','emocion','resultado','zona','sentimiento','genero','genero_confianza','genero_evidencia','estado','division','zona_detalle','origen_cultural']} | {k:'' for k in ['temas_manual','temas_producto_manual','emociones_manual','resultado_manual','region_manual','sentimiento_manual','genero_manual','confianza_manual','notas_manual']})
        path = folder / 'validacion_100.csv'
        preservar_correcciones(path, sample)
        write_csv(path, sample, list(sample[0]))
        coverage = {kind:sum(bool(labels[r['id']].get(kind)) for r in corpus_rows) for kind in ['tema_salud','tema_producto','emocion']}
        coverage['temas_totales'] = sum(bool(labels[r['id']].get('tema_salud') or labels[r['id']].get('tema_producto')) for r in corpus_rows)
        topic_counts = Counter(t for r in corpus_rows for t in labels[r['id']].get('tema_salud','').split('|') if t)
        lines = ['# Cobertura del diccionario propio v1', '', f'Corpus: {len(reviews)} reseñas v3; base consolidada: {len(all_rows)}. Fuente SHA256: {result["_meta"]["sha256"]}.', '', f'Referencia: {baseline}. Log-odds con suavizado 0,5, por ocurrencias; vocabulario conjunto. N-gramas contiguos sin stopwords; referencia de frases escasa: interpretar su ranking con cautela.', '']
        for kind, n in coverage.items(): lines.append(f'- {kind}: {n}/{len(reviews)} ({100*n/len(reviews):.2f} %).')
        lines += ['', '## Temas (menciones, no resultados comprobados)', '']
        for topic in result['temas']:
            n = topic_counts[topic]
            lines.append(f'- {topic}: {n}' + (' — pocas menciones (<10)' if n<10 else ''))
        lines += ['', '## Operacion/Producto (menciones por tema)', '']
        for topic in result['temas_producto']:
            n = sum(topic in labels[r['id']].get('tema_producto','').split('|') for r in corpus_rows)
            lines.append(f'- {topic}: {n}')
        one_star = [r for r in corpus_rows if r['estrellas']==1]
        one_covered = sum(bool(labels[r['id']].get('tema_salud') or labels[r['id']].get('tema_producto')) for r in one_star)
        explained = sum(bool(labels[r['id']].get('queja_producto') or set(labels[r['id']].get('resultado','').split('|')) & {'sin_efecto','efecto_adverso'}) for r in one_star)
        lines += ['', '## Cobertura de resenas de 1 estrella', '',
                  f'- Con al menos un tema de salud o producto: {one_covered}/{len(one_star)} ({100*one_covered/len(one_star):.2f} %).',
                  f'- Explicadas por una senal de queja concreta o resultado sin_efecto/efecto_adverso: {explained}/{len(one_star)} ({100*explained/len(one_star):.2f} %).',
                  f'- Sin explicacion automatica concreta: {len(one_star)-explained}/{len(one_star)}.',
                  '- Explicadas es una aproximacion por reglas, no precision validada. Una simple mencion de bottle, taste o pedido no basta para explicar una estrella; se exige senal de queja del tema o resultado negativo. Las quejas pueden ser negadas o referidas a terceros y necesitan revision humana.',
                  '', '## Taxonomia y seleccion de terminos', '',
                  f'- {len(result["temas"])} temas de salud canonicos sin tildes y {len(result["temas_producto"])} de producto; las etiquetas activas se regeneran sin alias ingleses. Se conserva el mapa de alias en _meta.taxonomia.',
                  '- bloating_gas pasa a hinchazon_gases; sus disparadores de hinchazon/gas se retiran de digestion. La union de reseñas con salud se conserva.',
                  '- terminos_producto_top150.csv documenta los 150 terminos distintos presentes, sus frecuencias y asignacion. Seleccion entre candidatos utiles revisados del CSV de no clasificados y de las frecuencias completas; desempate alfabetico. Se suman las semillas pedidas aunque no entren en los 150. Procedencia corpus + revision manual.',
                  '- Ejemplos propuestos: plastic bottles, seal, leaking, customer service, replacement, watered down, formula, aftertaste, flavor, worth it. No se clasifican como producto palabras genericas como good, product o artefactos «se pudo cargar el archivo multimedia».',
                  '- Palabras ambiguas (came/different/real/quality/strong/open/etc.) requieren contexto local segun taxonomia_resenas.py. Las frecuencias del diccionario son literales; las etiquetas aplican ese filtro contextual.',
                  '- terminos_sin_clasificar.csv significa ahora sin tema de salud NI Operacion/Producto. Puede contener palabras ya cubiertas por emocion/resultado.',
                  f'- Region: BAJA COBERTURA, {sum(bool(labels[r["id"]].get("zona")) for r in corpus_rows)}/{len(reviews)}; se mantiene como mencion, sin inferir residencia.']
        lines += ['', '## Validacion pendiente', '', f'Muestra estratificada reproducible (semilla 20261025): {quotas}. 100 filas; columnas manuales preservadas por ID. La cobertura no mide precision ni recall; falta revision humana.', '', 'Se normalizan apostrofos y se usan limites de palabra. Negacion local solo para emociones y resultados; temas son menciones incluso negadas. Resultado puede ser multiple. Genero es estimado; region es mencion textual, nunca residencia. Riesgos: polisemia (regular, cold, gas), sarcasmo, negaciones lejanas y alusiones a terceros. No se infieren zonas por slang. Sentimiento VADER: ±0,05; emocion principal = mas expresiones distintas, desempate alfabetico.', '', '## C1: resumen consolidado', '']
        for key in ['estrellas','variante']:
            lines.append(f'- {key}: {dict(Counter(r[key] for r in all_rows))}')
        lines.append(f'- genero estimado: {dict(Counter(labels[r["id"]]["genero"] for r in all_rows))}')
        gender_counts = Counter(labels[r['id']]['genero_confianza'] for r in corpus_rows)
        known = sum(labels[r['id']]['genero'] in ('Hombre','Mujer') for r in corpus_rows)
        unisex = sum(labels[r['id']]['genero']=='unisex' for r in corpus_rows)
        with_region = sum(bool(labels[r['id']].get('zona')) for r in corpus_rows)
        with_cultural = sum(bool(labels[r['id']].get('origen_cultural')) for r in corpus_rows)
        with_mentions = sum(bool(demographics[r['id']]['zona']['menciones']) for r in corpus_rows)
        lines += ['', '## Genero y zona reforzados (v2)', '',
                  f'- Genero estimado Hombre/Mujer: {known}/{len(reviews)} ({100*known/len(reviews):.2f} %); unisex: {unisex}; No claro: {len(reviews)-known-unisex}.',
                  f'- Confianza (todas las resenas): {dict(gender_counts)}.',
                  f'- Genero por confianza: {dict(Counter((labels[r["id"]]["genero"], labels[r["id"]]["genero_confianza"]) for r in corpus_rows))}.',
                  f'- Region de EEUU mapeada: {with_region}/{len(reviews)} ({100*with_region/len(reviews):.2f} %); menciones geograficas incluyendo ambiguas: {with_mentions}.',
                  f'- Origen cultural autorreferido: {with_cultural}; menciones culturales sin autorreferencia no se infieren como origen.',
                  f'- Nombres: {demo.names_source}. Apodos manuales; inicial aislada no utiliza el apellido. Unisex se mantiene como categoria, sin forzar genero.',
                  '- Texto explicito gana al nombre (alta). Pista indirecta como my husband/my wife gana al nombre, pero solo es alta si coinciden; de otro modo baja. Ladies/sir son audiencia y no asignan genero. Dos pistas explicitas incompatibles dejan No claro. Las inferencias de pareja son heuristicas y requieren revision.',
                  '- Estado/region/division/evidencia se conservan por mencion en zona_detalle. Una resena puede mencionar varias ubicaciones. IN/OR/ME/OK/HI y otras siglas solo mayusculas con contexto locativo o postal. Tri-state, East Coast y Southwest quedan ambiguas sin asignacion censal unica. Gulf Coast: Sur, division indeterminada; no se inventa estado ni division.',
                  '- Washington State se distingue de DC; Portland sin estado no se asigna. Caribbean/Jamaica se conservan aparte de EEUU. No se deduce residencia por el nombre ni por el estilo de escritura.', '', '## Hasta 30 frases geograficas halladas para revision', '']
        evidence = []
        for r in corpus_rows:
            for mention in demographics[r['id']]['zona']['menciones']:
                evidence.append({'id':r['id'],**mention})
        evidence.sort(key=lambda e:(e['id'], e['inicio']))
        for i,e in enumerate(evidence[:30],1):
            quote=e['evidencia'].replace('|','/').replace('`',"'")
            lines.append(f"{i}. {e['id']} — {e['estado'] or 'sin estado'} / {e['region'] or 'ambigua'} / {e['division'] or 'sin division'}: {quote}")
        if len(evidence)<30:
            lines += ['', f'Solo se hallaron {len(evidence)} menciones geograficas en el corpus; se listan todas, sin completar con frases inventadas.']
        lines += ['', '## Ejecucion', '', 'Usar venv con openpyxl, nltk, vaderSentiment y gender-guesser; WordNet local en diccionarios_nlp/wordnet. Ejecutar con -I: construir_diccionario.py y exportar_excel.py. Pruebas: python -I -m unittest discover -s 02_Motor-edicion/tools/resenas/tests -p "test_*resenas.py". La validacion_100 conserva correcciones manuales por ID al regenerar.']
        (folder / 'reporte_cobertura.md').write_text('\n'.join(lines)+'\n')
        print(json.dumps({'base': len(all_rows), 'corpus':len(reviews), 'cobertura':coverage, 'muestra':len(sample), 'top20':[(r['termino'],r['frecuencia']) for r in unknown[:20]]},ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--carpeta', type=Path, default=DEFAULT)
    parser.add_argument('--db', type=Path, default=DEFAULT / 'resenas.db')
    args = parser.parse_args()
    build(args.carpeta, args.db)
