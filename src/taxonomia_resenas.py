"""Taxonomia C2: nombres canonicos y vocabulario de producto revisado localmente."""
import re

ALIASES = {
    'acid_reflux_heartburn':'acidez_reflujo', 'constipation':'estrenimiento',
    'digestion':'digestion', 'bloating_gas':'hinchazon_gases',
    'diarrhea_nausea_vomiting':'diarrea_nausea', 'energy_fatigue':'energia_fatiga',
    'sleep_stress_anxiety':'sueno_estres', 'weight_appetite_obesity':'peso_apetito',
    'parasites_detox_cleanse':'parasitos_limpieza',
    'inflammation_pain':'inflamacion_dolor', 'inflammation_pain_arthritis_headache':'inflamacion_dolor',
    'immune_infection':'inmunidad', 'skin_hair':'piel_cabello',
    'blood_sugar':'azucar_presion', 'blood_sugar_diabetes_pressure_cholesterol':'azucar_presion',
    'liver_kidney':'higado_rinon_tiroides', 'liver_kidney_thyroid_hormones_menopause':'higado_rinon_tiroides',
    'cancer':'cancer_enfermedad_grave', 'adverse_reaction':'efecto_adverso',
    'adverse_reaction_allergy':'efecto_adverso',
}
CANONICOS = set(ALIASES.values())
SEMILLAS = {
    'envase_plastico_vidrio':'plastic|bottle|glass|leaked|broken|packaging|cap',
    'entrega_pedido':'came|arrived|late|missing|wrong|damaged|different',
    'sabor':'taste|bitter|nasty|sweet|drink',
    'precio_valor':'price|expensive|worth|money|refund',
    'dudas_autenticidad':'fake|scam|real|counterfeit|different from before',
}
# Candidatos revisados en terminos_sin_clasificar.csv y en sus frecuencias completas.
# No se fuerzan nombres de marca, verbos generales ni artefactos de la interfaz.
CANDIDATOS = {
    'envase_plastico_vidrio': 'plastic|bottle|bottles|glass|leaked|leaking|broken|packaging|cap|package|box|container|containers|seal|sealed|unsealed|opened|open|empty|wrapped|wrap|bubble wrap|packed|packaged|lid|bottled|glass bottles|glass bottle|plastic bottle|plastic bottles|two bottles|one bottle|second bottle|first bottle|bottles instead|plastic bottles instead|broken glass|broken bottle|glass container|contents|spilled|spilling|leak|leaks|cracked|shattered|damaged bottle|damaged bottles|packing|leakage|safety seal|bottle cap|bottle caps|tampered|foil|bpa',
    'entrega_pedido': 'came|arrived|late|missing|wrong|damaged|different|order|orders|ordered|ordering|received|receive|delivery|shipping|shipped|shipment|delivered|ship|sent|send|replacement|customer service|service|customer|seller|vendor|return|returned|returnable|subscription|canceled|cancelled|cancel|return policy|reorder|first order|second order|last order|order came|product came|bottles arrived|arrived broken|came broken|wrong item|missing bottle|missing items|never received|never arrived|delivery time|fast shipping|fast delivery|on time|damaged package|not returnable|cannot return|no return|non returnable',
    'sabor': 'taste|tastes|tasted|tasting|bitter|bitterness|flavor|flavors|nasty|sweet|drink|drinking|drinks|drank|sour|strong|water|juice|orange juice|lemon|honey|tea|coffee|smoothie|mix|mixing|mixed|swallow|mouth|gag|gagged|aftertaste|unbearable|tolerable|unpleasant|earthy|spicy|throat|tongue|gross|disgusting|awful taste|bad taste|taste like|tastes like|bitter taste|taste good|horrible taste|tastes terrible|taste horrible|tastes horrible|taste bitter|taste different|different taste|taste bad|nasty taste|bitter tasting|extremely bitter|definitely bitter|herbal taste|acquired taste|smell|smells|delicious|pleasant|tolerate|chaser|chase|sip|shot|texture',
    'precio_valor': 'price|expensive|worth|money|refund|value|cost|overpriced|cheap|cheaper|paid|wasted|waste|waste of money|save|deal|great value|definitely worth|worth it|not worth|money back|refund policy|spent|affordable|pricing|dollars|penny|pennies|costly|costs|wasting|waste money|wasted money|full refund|partial refund|discount|premium|budget',
    'dudas_autenticidad': 'fake|scam|real|counterfeit|different from before|quality|ingredients|formula|changed|watered|watered down|diluted|watery|batch|original|originally|completely different|totally different|nothing like|version|brand|company|manufacturer|website|label|inconsistent|potency|strength|weak|color|clear|dark|thick|thicker|consistency|bad batch|product quality|different formula|authentic|authenticity|legit|knock off|knockoff|not the same|not original|used to|same product|changed formula|new formula|old formula|looks different|tastes different|darker|lighter color|dilution',
}


def canonical(group):
    value=ALIASES.get(group,group)
    if value not in CANONICOS:
        raise ValueError(f'Tema de salud sin canon: {group}')
    return value


def fusionar(groups):
    """Union por termino y procedencia, sin sumar dos veces frecuencias del corpus."""
    result={}
    for group,entries in groups.items():
        dest=result.setdefault(canonical(group),{})
        for term,entry in entries.items():
            if term in dest:
                dest[term]['fuentes']=sorted(set(dest[term]['fuentes']) | set(entry['fuentes']))
            else:
                dest[term]={**entry,'fuentes':list(entry['fuentes'])}
    # La hinchazon es un subtema propio: no conservar sus mismos disparadores
    # dentro de digestion cuando provienen del manual original.
    for term in list(result.get('digestion',{})):
        if re.search(r'\b(?:bloat\w*|gas|gassy|flatulen\w*)\b',term):
            entry=result['digestion'].pop(term)
            target=result.setdefault('hinchazon_gases',{})
            if term in target:target[term]['fuentes']=sorted(set(target[term]['fuentes'])|set(entry['fuentes']))
            else:target[term]=entry
    return result


def _near(text,match,regex):
    # Contexto local: no propagar un tema por toda una resena larga.
    start=max(text.rfind('.',0,match.start()),text.rfind('!',0,match.start()),text.rfind('?',0,match.start()))+1
    ends=[p for p in (text.find(c,match.end()) for c in '.!?') if p>=0]
    end=min(ends) if ends else len(text)
    return bool(re.search(regex,text[max(start,match.start()-65):min(end,match.end()+65)]))


ENVASE = r'\b(?:bottles?|plastic|glass|packag\w*|containers?|seal\w*|caps?|lids?|box)\b'
PEDIDO = r'\b(?:order\w*|deliver\w*|ship\w*|packag\w*|receiv\w*|arriv\w*|sent|bottles?|items?|products?|seller|amazon)\b'
SABOR = r'\b(?:tast\w*|flavou?r\w*|drink\w*|bitter\w*|swallow\w*|mix\w*|smell\w*|mouth|tongue)\b'
AUTENTICO = r'\b(?:fake|scam|counterfeit|dilut\w*|watered|watery|changed|inconsistent|authentic\w*|original)\b|not the same|different from|used to|nothing like'


def operativos(text,dictionary):
    hits={}
    for group,entries in dictionary.items():
        terms=[]
        for e in entries:
            term=e['termino']
            for match in re.finditer(r'(?<![a-z0-9])'+re.escape(term)+r'(?![a-z0-9])',text):
                accepted=True
                if group=='dudas_autenticidad' and term=='used to':
                    accepted=_near(text,match,r'\b(?:bottles?|formula|batch|color|taste|flavou?r|brand|original|watered|dilut\w*)\b')
                elif group=='dudas_autenticidad' and term=='changed':
                    accepted=not re.match(r'\s+(?:my|our|his|her|their)\s+(?:life|diet|routine)\b',text[match.end():]) and _near(text,match,r'\b(?:bottles?|formula|batch|color|taste|flavou?r|packaging|label|ingredients|version|brand)\b')
                elif group=='entrega_pedido' and term=='different':
                    accepted=_near(text,match,r'\b(?:order\w*|deliver\w*|ship\w*|receiv\w*|arriv\w*|sent|wrong|items?)\b')
                elif group=='entrega_pedido' and term in {'came','different','late','missing','wrong','sent','send','service','customer','return','returned'}:
                    accepted=_near(text,match,PEDIDO)
                elif group=='envase_plastico_vidrio' and term in {'open','opened','empty','contents','wrapped','wrap','broken','leaked','leaking'}:
                    accepted=_near(text,match,ENVASE)
                elif group=='sabor' and term in {'water','strong','mouth','throat','tongue','unbearable','unpleasant','tolerable','texture','pleasant'}:
                    accepted=_near(text,match,SABOR)
                elif group=='precio_valor' and term in {'save','premium','deal','wasted','waste'}:
                    accepted=_near(text,match,r'\b(?:money|dollars?|price|cost|worth|refund|value|paid)\b')
                elif group=='dudas_autenticidad' and term in {'real','quality','ingredients','brand','company','manufacturer','website','label','potency','strength','weak','color','clear','dark','thick','thicker','consistency','originally','version','formula','batch','same product'}:
                    accepted=_near(text,match,AUTENTICO)
                if accepted:
                    terms.append(term);break
        if terms:hits[group]=terms
    return hits


QUEJAS = {
    'envase_plastico_vidrio': r'\b(?:leak\w*|broke\w*|crack\w*|shatter\w*|unsealed|spilled|tamper\w*)\b|plastic (?:bottle|container)|instead of glass|glass instead of plastic',
    'entrega_pedido': r'\b(?:missing|damaged|wrong|late|never arrived|never received)\b|cannot return|not returnable|no return|only (?:one|1) (?:bottle|item)|not (?:received|delivered)',
    'sabor': r'\b(?:nasty|disgusting|gross|gag\w*|unbearable|undrinkable|unpleasant|awful|horrible|terrible|bad)\b|too bitter|too strong|can.t (?:drink|stand|swallow)|cannot (?:drink|stand|swallow)',
    'precio_valor': r'\b(?:refund|overpriced|expensive)\b|waste (?:of )?money|wasted (?:my )?money|not worth|money back|too much',
    'dudas_autenticidad': r'\b(?:fake|scam|counterfeit|dilut\w*|watered|watery|inconsistent)\b|not the same|nothing like|different from before|changed formula',
}


def quejas(text,hits):
    """Senales de queja; diferentes de simples menciones de tema."""
    result=[]
    for group in hits:
        for match in re.finditer(QUEJAS[group],text):
            prefix=text[max(0,match.start()-25):match.start()]
            # 'no refund' es queja; 'not fake/no leaks/not bad' no lo son.
            if match.group()!='refund' and re.search(r"\b(?:no|not|never|isn't|wasn't)\s+(?:\w+\s+)?$",prefix):
                continue
            result.append(group);break
    return result


def migrar_etiquetas(conn,version):
    """Migra alias de la version activa; preserva las otras versiones/fuentes."""
    for old,new in ALIASES.items():
        if old==new:continue
        conn.execute('''INSERT OR IGNORE INTO etiquetas
            SELECT id_resena,tipo,?,fuente,version_dicc FROM etiquetas
            WHERE tipo='tema_salud' AND valor=? AND version_dicc=?''',(new,old,version))
        conn.execute("DELETE FROM etiquetas WHERE tipo='tema_salud' AND valor=? AND version_dicc=?",(old,version))
