#!/usr/bin/env python3
"""Candidatos léxicos, sin etiquetar reseñas (fase A).

Ejecutar con python3 -I filtrar_diccionarios.py [DIRECTORIO] [--salida RUTA].
Solo stdlib; WordNet se lee como texto desde su ZIP, sin cargar código, pickle,
ni extraer archivos. XML ElementTree no descarga DTD externos.
La cercanía es léxica: exacto, frase y solapamiento; no es validación médica.
Fuente principal por orden medlineplus > hpo > mesh > wordnet. Los conceptos
con nombres/sinónimos iguales se fusionan globalmente, conservando procedencias.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / 'data/diccionario_candidatos.json'
SEMILLAS = {
 'digestion': 'digestion|digestive|indigestion|stomach|gut|bowel',
 'bloating_gas': 'bloating|bloated|flatulence|intestinal gas|abdominal distension',
 'constipation': 'constipation|constipated',
 'diarrhea_nausea_vomiting': 'diarrhea|diarrhoea|nausea|vomiting',
 'acid_reflux_heartburn': 'acid reflux|heartburn|gastroesophageal reflux',
 'parasites_detox_cleanse': 'parasite|parasites|parasitic|detox|detoxification|cleanse',
 'weight_appetite_obesity': 'weight|appetite|obesity|obese|overweight',
 'energy_fatigue': 'fatigue|tiredness|tired|low energy|lethargy',
 'sleep_stress_anxiety': 'sleep|insomnia|stress|anxiety|anxious',
 'blood_sugar_diabetes_pressure_cholesterol': 'blood sugar|blood glucose|diabetes|diabetic|blood pressure|hypertension|cholesterol',
 'inflammation_pain_arthritis_headache': 'inflammation|inflammatory|pain|arthritis|headache',
 'immune_infection': 'immune|immunity|infection|infections',
 'skin_hair': 'skin|hair|rash|itching|acne|alopecia',
 'liver_kidney_thyroid_hormones_menopause': 'liver|kidney|thyroid|hormone|hormones|hormonal|menopause|menopausal',
 'cancer': 'cancer|tumor|tumour|neoplasm|malignancy',
 'adverse_reaction_allergy': 'adverse reaction|adverse effects|side effects|allergy|allergic|hypersensitivity',
}
SEEDS = {k: v.split('|') for k, v in SEMILLAS.items()}
# Filtro conservador: no pretende decidir automáticamente qué vocabulario usa el ICP.
RARE = re.compile(r'\b(gene|genes|protein|proteins|chromosome|chromosomal|syndrome|congenital|receptor|kinase|allele|mutation|enzyme|carcinoma|sarcoma|dysplasia)\b')


def limpiar(s):
    return re.sub(r'\s+', ' ', s.replace('_', ' ').lower()).strip()


# Vocabulario paciente conservador: excluye taxones, técnicas y subtipos raros
# aunque contengan una semilla. La revisión/expansión del corpus queda para C.
COMUNES = set("""abdominal abdomen abnormal abnormality absence absent ache aches aching acute
adult adults age aging alcohol allergic allergies allergy alopecia anal anemia ankle
anorexia antibiotic antibiotics arm arms attack autoimmune back bacterial bad bald
baldness belly benign bleeding blockage blood bloody body bone bones bowel brain breast
breathing brittle burning buttock calf cell cells chest childhood children chronic cold
colon colonic colorectal common complication complications condition congenital contact
cough cramps cramping cutaneous damage decreased deficiency dehydration delayed dental
depressed depression dermatitis digestive disease diseases disorder disorders discomfort
dizziness dry dryness eating elevated emotional enlarged enlargement excessive exercise
eye eyes face facial familial fatty feet female fever fibromyalgia finger fingers fluid
food foot frequent function gallbladder gastric gastrointestinal generalized genital gum
hand hands head hearing heart heat high hip hips hot human increased infant infantile
intestinal irritable irregular joint joints knee knees lack leg legs loose loss low lower
lung male metabolic mild mouth movement movements muscle muscular nail nails neck nerve
nervous night nonalcoholic oral overweight pelvic persistent physical poor post pregnancy
pregnant primary problem problems prolonged psychological recurrent reduced reduction
related renal respiratory restless retention scalp severe sexual shoulder sick sickness
slow small sore spasms spinal stomach swelling swollen symptom symptoms tenderness
throat tingling tooth toxic toxicity urinary urine vaginal viral vitamin weakness women
wound wrist upper tract tension tension-type migraine morning motion sickness seasonal
sensitivity sensitive intolerance intolerant lactose gluten celiac bowel syndrome
failure falling thinning total patchy pattern premature essential type two one mellitus
insulin resistance resistant level levels elevated low-grade premature inflammatory
vulgaris reflux gastroesophageal esophageal dyspepsia dyspeptic indigestion gas bloated
bloating distension distention burping belching flatulence fecal faecal stool stools
hard painful painless benign malignant neoplasms tumors tumours nausea nauseous vomiting
vomit diarrhea diarrhoea constipation constipated tired tiredness fatigue fatigability
lethargy lethargic drowsiness insomnia sleeplessness sleepiness heartburn skin hair
liver kidney kidneys thyroid hormone hormones hormonal menopause menopausal perimenopause
perimenopausal infection infections immunity immune cancer pain arthritis headache
stress anxiety anxious appetite digestion weight obesity obese detox detoxification
cleanse parasites parasite parasitic sugar glucose pressure cholesterol reaction reactions
adverse effect effects side gain losing gaining energy exhaustion exhausted nervousness
intestine intestines gut allergic hypersensitivity systemic local recurrent dysfunction
balance imbalance trouble slow transit fecal incontinence retention evacuation
""".split())
COMUNES.update(w for seeds in SEEDS.values() for seed in seeds for w in seed.split())


def valido(s):
    return bool(s and len(s.split()) <= 4 and re.fullmatch(r"[a-z][a-z '\-]*", s)
                and not RARE.search(s) and all(w in COMUNES for w in re.findall(r'[a-z]+', s)))


def cercania(nombre, seeds):
    best = 0
    for seed in seeds:
        if nombre == seed:
            best = max(best, 100)
        elif re.search(r'(?<![a-z])' + re.escape(seed) + r'(?![a-z])', nombre):
            best = max(best, 80 - len(nombre.split()))
    return best


def xml_records(path, tag):
    # Vaciar también la raíz mantiene acotada la memoria para MeSH (~300 MB).
    context = ET.iterparse(path, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag == tag:
            yield elem
            elem.clear()
            root.clear()


def fuentes(base):
    files = sorted((base / 'medlineplus').glob('mplus_topics_*.xml'))
    if not files:
        raise FileNotFoundError('No hay XML MedlinePlus')
    for e in xml_records(files[-1], 'health-topic'):
        if e.get('language') == 'English':
            yield 'medlineplus', e.get('id'), [e.get('title', '')] + [x.text or '' for x in e.findall('also-called')]
    block = []
    with (base / 'hpo/hp.obo').open(encoding='utf-8') as f:
        for line in f:
            if line.startswith('['):
                if block:
                    yield from hpo_record(block)
                block = [] if line.strip() == '[Term]' else None
            elif block is not None:
                block.append(line.rstrip())
        if block:
            yield from hpo_record(block)
    for e in xml_records(base / 'mesh_2026/desc2026.xml', 'DescriptorRecord'):
        yield 'mesh', e.findtext('DescriptorUI'), [e.findtext('DescriptorName/String', '')] + [x.text or '' for x in e.findall('.//TermList/Term/String')]
    with ZipFile(base / 'wordnet/corpora/wordnet.zip') as z:
        for pos in ('noun', 'verb', 'adj', 'adv'):
            with z.open('wordnet/data.' + pos) as f:
                for raw in f:
                    line = raw.decode('utf-8')
                    if not line or not line[0].isdigit():
                        continue
                    fields = line.split('|', 1)[0].split()
                    count = int(fields[3], 16)
                    words = [fields[4 + i * 2] for i in range(count)]
                    # Solo sentidos con ancla explícita; no expansión recursiva polisémica.
                    gloss = line.split('|', 1)[1].lower()
                    health = re.search(r'health|body|bodily|disease|symptom|medical|illness|stomach|intestin|bowel|sleep|anxious|anxiety|mental|emotion|tired|fatigue|eat|food|skin|hair|hormone|blood|allerg|tumor|cancer|pain', gloss)
                    if health and any(limpiar(w) in {s for ss in SEEDS.values() for s in ss} for w in words):
                        yield 'wordnet', f'{pos}:{fields[0]}', words


def hpo_record(lines):
    if 'is_obsolete: true' in lines:
        return
    rid = next((s[4:] for s in lines if s.startswith('id: ')), '')
    names = [s[6:] for s in lines if s.startswith('name: ')]
    for s in lines:
        m = re.match(r'synonym: "((?:[^"\\]|\\.)*)" EXACT', s)
        if m:
            names.append(m[1].replace('\\"', '"'))
    if rid and names:
        yield 'hpo', rid, names


def construir(base, limite):
    concepts, alias = {}, {}
    for source, rid, names in fuentes(base):
        names = list(dict.fromkeys(limpiar(s) for s in names))
        names = [s for s in names if valido(s)]
        if not names or not any(cercania(s, seeds) for s in names for seeds in SEEDS.values()):
            continue
        matches = {alias[s] for s in names if s in alias}
        key = min(matches) if matches else len(alias)
        if not matches:
            concepts[key] = {'names': set(), 'refs': []}
        for other in sorted(matches - {key}):
            old = concepts.pop(other)
            concepts[key]['names'].update(old['names'])
            concepts[key]['refs'].extend(old['refs'])
            for s in old['names']:
                alias[s] = key
        concepts[key]['names'].update(names)
        concepts[key]['refs'].append((source, rid))
        for s in names:
            alias[s] = key
    out = {}
    for tema, seeds in SEEDS.items():
        candidatos = []
        for c in concepts.values():
            ranked = sorted(c['names'], key=lambda s: (-cercania(s, seeds), len(s.split()), s))
            score = cercania(ranked[0], seeds)
            if not score:
                continue
            refs = list(dict.fromkeys(c['refs']))
            source, rid = refs[0]
            candidatos.append((score, {'termino': ranked[0], 'fuente': source,
                'id_fuente': rid, 'sinonimos': sorted(c['names'] - {ranked[0]}),
                'procedencias': [{'fuente': s, 'id_fuente': i} for s, i in refs]}))
        candidatos.sort(key=lambda x: (-x[0], x[1]['termino']))
        out[tema] = {'terminos': [c for _, c in candidatos[:limite]]}
    return out


def resumen(out):
    principales = Counter()
    for tema, data in out.items():
        counts = Counter(r['fuente'] for r in data['terminos'])
        principales.update(counts)
        print(f'{tema}: {len(data["terminos"])} (' + ', '.join(f'{s}={counts[s]}' for s in ('medlineplus', 'hpo', 'mesh', 'wordnet')) + ')')
    print('Total asignaciones tema-término:', sum(principales.values()))
    print('Por fuente principal:', ', '.join(f'{s}={principales[s]}' for s in ('medlineplus', 'hpo', 'mesh', 'wordnet')))
    print('Conceptos únicos:', len({tuple((p['fuente'], p['id_fuente']) for p in r['procedencias']) for d in out.values() for r in d['terminos']}))
    print('Las procedencias fusionadas se conservan; los totales cuentan la fuente principal.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directorio', type=Path, nargs='?', default=Path(__file__).resolve().parents[1] / 'diccionarios_nlp')
    p.add_argument('--salida', type=Path, default=DEFAULT_OUT)
    p.add_argument('--limite', type=int, default=400)
    args = p.parse_args()
    if not 1 <= args.limite <= 400:
        p.error('--limite debe estar entre 1 y 400')
    out = construir(args.directorio, args.limite)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    resumen(out)


if __name__ == '__main__':
    main()
