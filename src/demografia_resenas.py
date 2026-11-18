"""Estimaciones explicables de genero y menciones geograficas; sin red."""
import re
from collections import Counter

# Lista manual complementaria US: no pretende representar frecuencia SSA.
NOMBRES_US = {
    'Mujer': 'mary patricia jennifer linda elizabeth barbara susan jessica sarah karen nancy lisa betty margaret sandra ashley kimberly emily donna michelle carol amanda dorothy melissa deborah stephanie rebecca sharon laura cynthia kathleen amy angela shirley anna brenda pamela nicole samantha katherine christine debra rachel catherine janet emma carolyn maria heather diane ruth julie olivia joyce virginia victoria kelly lauren christina joan evelyn judith megan andrea cheryl hannah jacqueline martha gloria teresa ann sara madison frances kathryn janice jean abigail alice judy sophia denise danielle marilyn amber theresa beverly'.split(),
    'Hombre': 'james robert john michael david william richard joseph thomas charles christopher daniel matthew anthony mark donald steven paul andrew joshua kenneth kevin brian george timothy ronald edward jason jeffrey ryan jacob gary nicholas eric jonathan stephen larry justin scott brandon benjamin samuel gregory alexander patrick frank raymond jack dennis jerry tyler aaron jose henry douglas adam peter nathan zachary walter kyle harold carl jeremy keith roger gerald ethan arthur terry christian sean lawrence austin joe noah jesse albert bryan billy bruce willie jordan dylan alan ralph roy eugene randy vincent russell louis philip bobby johnny bradley'.split(),
    'unisex': 'alex jordan taylor casey morgan riley avery jamie jessie pat chris sam robin leslie terry tracy shannon devon dakota drew quinn blair skyler cameron peyton sasha kim'.split(),
}
APODOS = {'bob':'robert','rob':'robert','bobby':'robert','bill':'william','billy':'william','jim':'james','jimmy':'james','mike':'michael','dave':'david','steve':'steven','liz':'elizabeth','beth':'elizabeth','lizzy':'elizabeth','sue':'susan','suzie':'susan','deb':'deborah','debbie':'deborah','kathy':'kathleen','kate':'katherine','jen':'jennifer','jenny':'jennifer','becky':'rebecca','rick':'richard','dick':'richard','tony':'anthony','tom':'thomas'}
PISTAS = {
    'Mujer': { 'explicita': ["i'm a woman", 'i am a woman', 'as a woman', "i'm female", 'i am female', 'as a mom', 'as a mother', "i'm a mom", 'i am a mom', 'as a wife', 'i am a grandmother', "i'm a grandma"], 'indirecta': ['my husband', 'my hubby', 'my period']},
    'Hombre': {'explicita': ["i'm a man", 'i am a man', 'as a man', "i'm male", 'i am male', 'as a dad', 'as a father', "i'm a dad", 'i am a dad', 'as a husband', 'i am a grandfather'], 'indirecta': ['my wife']},
    'No claro': {'audiencia': ['ladies', 'sir', 'gentlemen']},
}


def norm(s): return str(s or '').lower().replace('’', "'")


def pattern(s): return r'(?<![a-z0-9])' + re.escape(norm(s)) + r'(?![a-z0-9])'


class Demografia:
    def __init__(self, legacy):
        self.detector = legacy.gd
        self.names = {k:set(v) for k,v in NOMBRES_US.items()}
        try:
            from nltk.corpus import names
            male={n.lower() for n in names.words('male.txt')}
            female={n.lower() for n in names.words('female.txt')}
            self.names['unisex'] |= male & female
            self.names['Hombre'] |= male-female
            self.names['Mujer'] |= female-male
            self.names_source='manual US + nltk names + gender-guesser'
        except LookupError:
            self.names_source='manual US + gender-guesser; nltk names/SSA no disponibles'
        self.states=dict(legacy.ESTADOS)
        # Nombres coherentes de las 9 divisiones censales.
        self.states={s:(r, {'Montana':'Montaña','Pacifico':'Pacífico','Atlantico Sur':'Atlántico Sur','Atlantico Medio':'Atlántico Medio'}.get(d,d)) for s,(r,d) in self.states.items()}
        self.abbrev=dict(legacy.ABREV)
        self.cities=dict(legacy.CIUDADES) | {'washington, dc':'Washington DC','washington d.c.':'Washington DC','washington, d.c.':'Washington DC','fort worth':'Texas','san jose':'California','el paso':'Texas','oklahoma city':'Oklahoma','tucson':'Arizona','fresno':'California','honolulu':'Hawaii','anchorage':'Alaska'}
        self.cities.pop('portland',None) # Oregon/Maine: requiere desambiguacion.
        self.regions={
            'the south':('Sur',''), 'down south':('Sur',''), 'midwest':('Medio Oeste',''), 'mid-west':('Medio Oeste',''),
            'northeast':('Noreste',''), 'new england':('Noreste','Nueva Inglaterra'),
            'west coast':('Oeste','Pacífico'), 'bay area':('Oeste','Pacífico'),
            'gulf coast':('Sur',''), 'deep south':('Sur',''),
            'tri-state':('',''), 'tristate':('',''), 'east coast':('',''),
            'pacific northwest':('Oeste','Pacífico'), 'southwest':('',''),
        }
        self.culture={'jamaica':'Jamaica','jamaican':'Jamaica','caribbean':'Caribe','west indies':'Caribe','west indian':'Caribe'}

    def genero(self, name, text):
        tokens=re.findall(r"[a-z]+",norm(name))
        while tokens and tokens[0] in {'mr','mrs','ms','miss','dr'}:tokens.pop(0)
        first=tokens[0] if tokens else ''
        initial=len(first)==1
        canonical=APODOS.get(first,first)
        guess=self.detector.get_gender(canonical) if canonical and not initial else 'unknown'
        if canonical in self.names['unisex'] or guess=='andy': ng='unisex'
        elif initial: ng='No claro'
        elif canonical in self.names['Mujer']: ng='Mujer'
        elif canonical in self.names['Hombre']: ng='Hombre'
        else: ng={'female':'Mujer','mostly_female':'Mujer','male':'Hombre','mostly_male':'Hombre'}.get(guess,'No claro')
        evidence=[]; explicit=set(); indirect=set()
        for g,levels in PISTAS.items():
            for level,terms in levels.items():
                for term in terms:
                    for m in re.finditer(pattern(term),norm(text)):
                        evidence.append({'pista':term,'genero':g,'tipo':level})
                        if level=='explicita': explicit.add(g)
                        elif level=='indirecta':indirect.add(g)
        active=explicit or indirect
        if len(active)>1: value,confidence='No claro','baja'
        elif active:
            value=next(iter(active)); confidence='alta' if explicit or value==ng else 'baja'
        else: value,confidence=ng, 'media' if ng in {'Mujer','Hombre'} else 'baja'
        return {'genero':value,'confianza':confidence,'nombre_genero':ng,'nombre_token':first,'nombre_canonico':canonical,'evidencia':evidence,'conflicto':bool(active and ng in {'Mujer','Hombre'} and ng not in active),'fuente_nombres':self.names_source}

    def zona(self,text):
        found=[]; culture=[]; lower=norm(text)
        def add(m,state='',region='',division='',kind='estado'):
            if state: region,division=self.states[state]
            start=max(0,m.start()-45); end=min(len(text),m.end()+65)
            found.append({'estado':state,'region':region,'division':division,'termino':text[m.start():m.end()],'evidencia':text[start:end].replace('\n',' '),'tipo':kind,'inicio':m.start()})
        # Washington solo con estado explicito; Georgia con contexto locativo.
        for state in self.states:
            term=state
            for m in re.finditer(pattern(term),lower):
                if state=='Georgia' and not re.search(r'\b(?:in|from|to|live in|back home in)\s+$',lower[max(0,m.start()-25):m.start()]):continue
                add(m,state)
        for term,state in self.cities.items():
            for m in re.finditer(pattern(term),lower):add(m,state,kind='ciudad')
        for ab,state in self.abbrev.items():
            # Dos letras siempre mayusculas y contexto postal/locativo; no «OK!».
            for m in re.finditer(r'(?<![A-Za-z])'+ab+r'(?![A-Za-z])',text):
                before=text[max(0,m.start()-40):m.start()]
                after=text[m.end():m.end()+10]
                locative=re.search(r'\b(?:[Ii]n|[Ff]rom|[Tt]o|[Nn]ear|live in|back home in)\s+$',before)
                postal = bool(re.match(r'\s+\d{5}(?:-\d{4})?\b',after)) or any(re.search(pattern(city)+r',\s*$', norm(before)) for city in self.cities)
                if locative or postal:add(m,state,kind='abreviatura_contextual')
        for term,(region,division) in self.regions.items():
            for m in re.finditer(pattern(term),lower):
                state='California' if term=='bay area' else ''
                add(m,state,region,division,'region_coloquial' if region else 'region_ambigua')
        for term,origin in self.culture.items():
            for m in re.finditer(pattern(term),lower):
                before=lower[max(0,m.start()-50):m.start()]
                self_origin=bool(re.search(r"\b(?:i am|i'm|im|we are|we're|i grew up in|i was born in|i come from|i'm from|i am from|back home in|my roots are in|as a|being)\s+(?:the\s+)?$",before))
                culture.append({'origen':origin,'tipo':'autorreferencia' if self_origin else 'mencion_cultural','evidencia':text[max(0,m.start()-40):m.end()+60]})
        # Una referencia larga a New York no duplica la misma mencion como ciudad.
        unique=[]
        for item in sorted(found,key=lambda x:(x['inicio'],-len(x['termino']))):
            if not any(x['inicio']==item['inicio'] and x['estado']==item['estado'] for x in unique):unique.append(item)
        return {'menciones':unique,'cultural':culture}

    def agregar_diccionario(self,result,texts):
        def entry(term,**extra):
            return {'termino':term,'fuentes':['manual'],'frecuencia':sum(len(re.findall(pattern(norm(term)),t)) for t in texts),'resenas':sum(bool(re.search(pattern(norm(term)),t)) for t in texts),**extra}
        result['genero_pistas']={g:[entry(t,tipo=level) for level,terms in levels.items() for t in terms] for g,levels in PISTAS.items()}
        result['genero_nombres']={g:[entry(t,tipo='nombre_us_manual') for t in terms] for g,terms in NOMBRES_US.items()}
        # Frecuencias de nombres se completan en el constructor desde el campo nombre.
        result['regiones']={r:[] for r in ['Noreste','Medio Oeste','Sur','Oeste','Ambigua']}
        for state,(region,division) in self.states.items():result['regiones'][region].append(entry(state.lower(),estado=state,region=region,division=division,tipo='estado'))
        for term,state in self.cities.items():
            region,division=self.states[state];result['regiones'][region].append(entry(term,estado=state,region=region,division=division,tipo='ciudad'))
        for term,(region,division) in self.regions.items():result['regiones'][region or 'Ambigua'].append(entry(term,estado='California' if term=='bay area' else '',region=region,division=division,tipo='region_coloquial'))
        for ab,state in self.abbrev.items():
            region,division=self.states[state];result['regiones'][region].append(entry(ab,estado=state,region=region,division=division,tipo='abreviatura_contextual',nota='Frecuencia literal sin contexto; solo se etiqueta con contexto postal/locativo'))
        result['origen_cultural']={origin:[entry(t,tipo='mencion_no_residencia') for t,o in self.culture.items() if o==origin] for origin in set(self.culture.values())}
