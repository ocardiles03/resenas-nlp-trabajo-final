"""Segmentos de comprador desde resenas.db (necesidades y conductas, no demografia).

Mide tamaño, estrellas, sesgo de genero y tendencia por semestre de cada segmento.
Uso: python3 -I segmentos_icp.py   (imprime una tabla; sin red). Regex por reglas.
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estudio_icp as E

SEG = {
    'hinchazon_barriga': r'bloat|flat(ter)? (stomach|belly|tummy)|pooch|belly|distend|gassy',
    'regularidad': r'\bregular|bowel movement|\bbms?\b|go(ing)? to the bathroom|constipat|backed up',
    'energia_ligereza': r'energ|sluggish|lighter|lightweight|less tired|fatigue',
    'rutina_wellness': r'wellness|routine|daily|every ?day|every morning|lifestyle|holistic|journey|staple|vitamin|moringa|sea moss|elderberry|turmeric|apple cider',
    'detox_limpieza': r'detox|cleanse|cleansing|flush|parasite',
    'peso_apetito': r'weight|appetite|cravings|slim|belly fat|pounds',
    'dolor_articular': r'joint|arthrit|\bpain\b|inflam|swell|gout',
    'condiciones_salud': r'diabet|blood sugar|a1c|blood pressure|hypertens|cholesterol|crohn|\bibs\b|colitis|diverticul|gerd|reflux|chemo|cancer|kidney|thyroid|fibroid|lupus',
    'probo_de_todo': r'miralax|dulcolax|metamucil|prescription|medication|meds\b|stool softener|laxative|magnesium|colace|tried (everything|so many|many|lots)|nothing (else )?(worked|helped)',
    'esceptico_convencido': r"skeptic|sceptic|wasn.t sure|didn.t believe|did not believe|hesitat|on the fence|doubt|too good to be true|pleasantly|didn.t expect|did not expect",
    'recompra': r'(2nd|second|third|3rd|fourth|4th|fifth|5th|another|next) (bottle|order|time)|reorder|re-order|buy(ing)? again|bought (it |them )?again|order(ed)? (it )?again|keep (buying|ordering)|stock up|repeat customer',
    'quemado_autenticidad': r'(used to|previous|before|last time|first (time|order)|earlier|prior).{0,80}(glass|plastic|watered|thick|taste|diluted|strong)|(glass).{0,60}(plastic)|changed (the |their )?(formula|bottle|packag|recipe)|not (the )?same (as|product|formula)|watered down',
    'sabor_intolerante': r"can.t (stand|stomach|drink|take|swallow)|gag|threw up|throw up|vomit|never again|impossible to (drink|take|swallow)|unbearable|worst (thing|taste)|disgust",
    'pareja_familia': r"my (husband|wife|hubby|boyfriend|partner)|(hubby|husband|wife) and (i|me)|whole (family|household)|(for|gave|giving|got|bought) (it |this |them )?(for |to )?(my )?(mom|mother|dad|father|daughter|son|grandma|grandmother|aunt|mama|parents)",
    'deporte_dieta': r'workout|gym|keto|carnivore|intermittent|fasting|vegan|plant.based|paleo|macro|athlet|runner|lifting|protein|bodybuild',
    'viaje_evento': r'vacation|holiday|cruise|trip|travel|thanksgiving|christmas|binge|after (eating|the holidays)|cheat',
}


def main():
    f = E.cargar()
    pats = {k: re.compile(v) for k, v in SEG.items()}
    for x in f:
        x['seg'] = {k for k, p in pats.items() if p.search(x['t'])}
    tot = len(f)
    print(f"{'segmento':24}{'n':>5}{'%':>6}{'4-5★':>6}{'1-2★':>6}{'%mujer':>8}")
    for k in SEG:
        sub = [x for x in f if k in x['seg']]
        n = len(sub)
        cl = [x for x in sub if x['genero'] in ('Mujer', 'Hombre')]
        mu = 100 * sum(x['genero'] == 'Mujer' for x in cl) / max(1, len(cl))
        print(f"{k:24}{n:5}{100 * n / tot:5.1f}%{100 * sum(x['est'] >= 4 for x in sub) / n:5.0f}%{100 * sum(x['est'] <= 2 for x in sub) / n:5.0f}%{mu:7.0f}%")
    u = [x for x in f if 'hinchazon_barriga' in x['seg'] or 'regularidad' in x['seg']]
    cl = [x for x in u if x['genero'] in ('Mujer', 'Hombre')]
    print(f"\nhinchazon ∪ regularidad: {len(u)} ({100 * len(u) / tot:.0f}%), mujeres {100 * sum(x['genero'] == 'Mujer' for x in cl) / len(cl):.0f}% de {len(cl)} clasificados")
    print('\ntendencia (% de reseñas por semestre)')
    g = defaultdict(list)
    for x in f:
        if x['anio'] and (x['anio'], 1 if x['mes'] <= 6 else 2) >= (2025, 1):
            g[(x['anio'], 1 if x['mes'] <= 6 else 2)].append(x)
    print(f"{'':10}{'n':>5} " + ' '.join(f'{k[:9]:>9}' for k in SEG))
    for p in sorted(g):
        v = g[p]
        print(f"{p[0]}-H{p[1]:<5}{len(v):5} " + ' '.join(f"{100 * sum(k in x['seg'] for x in v) / len(v):8.0f}%" for k in SEG))


if __name__ == '__main__':
    main()
