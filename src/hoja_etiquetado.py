#!/usr/bin/env python3
"""Arma la hoja de Excel para etiquetar a mano las resenas (sin mostrar estrellas ni etiquetas del lexico).

Uso (desde la raiz del proyecto):
  .venv/bin/python -I src/hoja_etiquetado.py                # hoja de las 100 de data/validacion_100.csv
  .venv/bin/python -I src/hoja_etiquetado.py --ampliar 200  # hoja con 200 resenas NUEVAS del bundle (no repite las 100)
  .venv/bin/python -I src/hoja_etiquetado.py --ampliar 200 --base soursop  # 200 NUEVAS del Soursop B0CYV4FCJS (2a base)
Nunca sobrescribe una hoja existente (para no perder etiquetas) salvo que se pase --forzar.
La hoja solo trae id, titulo, texto y las columnas a rellenar; las columnas *_manual del CSV no se tocan.
"""
import argparse, csv, importlib.util, json, math, random, re, sys
from collections import defaultdict
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

SRC = Path(__file__).resolve().parent
DATA = SRC.parent / 'data'

# Campos a rellenar: (columna, valores del desplegable, estricta, ancho, instruccion).
# estricta=False => acepta varios valores separados por | (como las columnas multivalor de validacion_100.csv: aviso, no bloqueo).
# Los valores reutilizan el vocabulario del proyecto (diccionario_cliente.py / validacion_100.csv) para poder comparar
# luego el etiquetado manual con el automatico.
NO_DICE = 'no_lo_dice'
CAMPOS = [
    ('sentimiento_manual', ['Positivo', 'Negativo', 'Neutro'], True, 16,
     'Positivo / Negativo / Neutro, segun lo que expresa el texto del cliente (no la nota).'),
    ('genero_manual', ['Hombre', 'Mujer', 'No claro', 'unisex'], True, 14,
     'Solo si el texto lo dice (p. ej. "as a mom", "my wife"); si no, "No claro".'),
    ('region_manual', ['Noreste', 'Medio Oeste', 'Sur', 'Oeste', 'Ambigua', 'No se menciona'], True, 16,
     'Solo si el texto menciona un estado, ciudad o region de EE. UU.; si no, "No se menciona".'),
    ('emociones_manual', ['alegria_satisfaccion', 'esperanza_confianza', 'decepcion_enojo', 'miedo_preocupacion', 'asco', 'alivio', 'gratitud'], False, 26,
     'Opcional; vocabulario de la columna `emocion`. Varias: separadas por | (ej. alegria_satisfaccion|gratitud).'),
    ('motivo_compra', ['estrenimiento', 'hinchazon_gases', 'digestion_estomago', 'acidez_reflujo', 'diarrea_nausea', 'dolor_inflamacion', 'azucar_presion',
                       'energia_fatiga', 'sueno_estres', 'peso_apetito', 'parasitos_detox', 'inmunidad', 'piel_cabello', 'higado_rinon_tiroides',
                       'cancer_enfermedad_grave', 'otro', NO_DICE], False, 24,
     'Para que (problema) lo compro o lo uso, segun el texto. Varios: separados por |.'),
    ('resultado_manual', ['mejora', 'sin_efecto', 'efecto_adverso', NO_DICE], False, 18,
     'Que dice que le paso al usarlo. Varios: separados por | (ej. mejora|efecto_adverso).'),
    ('objecion_principal', ['sabor', 'precio_valor', 'envase_plastico_vidrio', 'dudas_autenticidad', 'entrega_pedido', 'servicio_reembolso',
                            'efecto_adverso', 'no_funciona', 'ninguna'], True, 24,
     'La queja o duda MAS importante del texto (una sola); "ninguna" si no hay.'),
    ('razon_positiva', ['resultado', 'sabor_aceptable', 'buen_valor', 'recomienda_recompra', 'confianza_marca', 'entrega_servicio', 'ninguna'], False, 22,
     'Que argumento a favor da (por que lo recomienda o lo valora). Varios: separados por |; "ninguna" si no hay.'),
    ('recompra', ['Si', 'No', 'No lo dice'], True, 12,
     'Si dice que volvio a comprar / comprara de nuevo (Si), que no lo hara (No), o no lo dice.'),
    ('comprador_tipo', ['nuevo', 'recompra', 'No lo dice'], True, 14,
     'Primera vez (nuevo) o ya lo habia comprado (recompra), segun el texto.'),
    ('comprador_para', ['para_si_mismo', 'para_otra_persona', 'No lo dice'], True, 18,
     'Lo compra para si mismo o para otra persona (pareja, hijo/a, madre...), segun el texto.'),
]
# Significado de cada valor de los desplegables (hoja 'Guia de valores'): (columna, valor, que significa / cuando elegirlo).
# Las palabras en ingles entre comillas son ejemplos de lo que suele decir el cliente; no hace falta que aparezcan literal.
GUIA = {
    'sentimiento_manual': [
        ('Positivo', 'El texto expresa satisfaccion o una opinion favorable del producto.'),
        ('Negativo', 'El texto expresa queja, decepcion o una opinion desfavorable.'),
        ('Neutro', 'Mezcla de bueno y malo equilibrada, o no opina (solo describe, pregunta o dice algo sin valoracion).')],
    'genero_manual': [
        ('Hombre', 'El texto dice que quien escribe es hombre ("as a man", "my wife").'),
        ('Mujer', 'El texto dice que quien escribe es mujer ("as a mom", "my husband").'),
        ('No claro', 'El texto no lo dice.'),
        ('unisex', 'Hay pistas de ambos generos o el nombre sirve para los dos y el texto no lo aclara.')],
    'region_manual': [
        ('Noreste', 'Menciona un estado/ciudad del noreste de EE. UU. (p. ej. New York, Massachusetts, Pennsylvania).'),
        ('Medio Oeste', 'Menciona un estado/ciudad del medio oeste (p. ej. Illinois, Ohio, Michigan).'),
        ('Sur', 'Menciona un estado/ciudad del sur (p. ej. Texas, Florida, Georgia).'),
        ('Oeste', 'Menciona un estado/ciudad del oeste (p. ej. California, Washington, Arizona).'),
        ('Ambigua', 'Menciona un lugar pero no se sabe a que region corresponde.'),
        ('No se menciona', 'El texto no menciona ningun lugar.')],
    'emociones_manual': [
        ('alegria_satisfaccion', 'Contento, feliz, satisfecho con el producto.'),
        ('esperanza_confianza', 'Espera que funcione, confia en el producto o tiene ilusion.'),
        ('decepcion_enojo', 'Decepcionado, molesto o enojado.'),
        ('miedo_preocupacion', 'Preocupado, con miedo o inseguro (por seguridad, salud, efectos).'),
        ('asco', 'Repulsion por el sabor, olor o textura.'),
        ('alivio', 'Se sintio aliviado: le paso un sintoma o problema.'),
        ('gratitud', 'Agradece al producto, a la marca o al vendedor.')],
    'motivo_compra': [
        ('estrenimiento', 'No podia evacuar, heces duras, irregularidad ("constipated", "backed up").'),
        ('hinchazon_gases', 'Hinchazon, gases, vientre inflado ("bloated", "gassy").'),
        ('digestion_estomago', 'Digestion o malestar de estomago/intestino en general, sin algo mas especifico ("gut health", "stomach").'),
        ('acidez_reflujo', 'Acidez, reflujo, agruras ("acid reflux", "heartburn").'),
        ('diarrea_nausea', 'Diarrea, nauseas, vomito, colicos, estomago revuelto.'),
        ('dolor_inflamacion', 'Dolor, inflamacion, artritis, articulaciones, dolor de cabeza o migrana.'),
        ('azucar_presion', 'Azucar en la sangre, diabetes, presion arterial, colesterol.'),
        ('energia_fatiga', 'Falta de energia, cansancio, fatiga.'),
        ('sueno_estres', 'Sueno, insomnio, ansiedad, estres, calma.'),
        ('peso_apetito', 'Bajar de peso, apetito, antojos, grasa abdominal.'),
        ('parasitos_detox', 'Parasitos, lombrices, desintoxicacion o limpieza, candida, toxinas ("detox", "cleanse").'),
        ('inmunidad', 'Defensas, resfriados, gripe, infecciones.'),
        ('piel_cabello', 'Piel, acne, eczema, psoriasis, cabello, unas.'),
        ('higado_rinon_tiroides', 'Higado, rinon, tiroides, hormonas, menopausia.'),
        ('cancer_enfermedad_grave', 'Cancer, tumores, quimioterapia, quistes, fibromas u otra enfermedad grave.'),
        ('otro', 'Dice para que lo usa pero no encaja en ninguna de las anteriores (anotalo en notas_manual).'),
        (NO_DICE, 'El texto no dice para que lo compro o lo usa (p. ej. solo opina del sabor o de la entrega).')],
    'resultado_manual': [
        ('mejora', 'Dice que le funciono o que mejoro.'),
        ('sin_efecto', 'Dice que no noto nada / no le sirvio.'),
        ('efecto_adverso', 'Dice que le cayo mal (nauseas, diarrea fuerte, mareo, alergia, reaccion).'),
        (NO_DICE, 'El texto no cuenta que le paso al usarlo.')],
    'objecion_principal': [
        ('sabor', 'Se queja del sabor, olor o textura.'),
        ('precio_valor', 'Es caro o no vale lo que cuesta.'),
        ('envase_plastico_vidrio', 'Se queja del envase (plastico en vez de vidrio, roto, derrame, tapa).'),
        ('dudas_autenticidad', 'Duda de que sea original, de los ingredientes o de que venga sellado/legitimo.'),
        ('entrega_pedido', 'Problema de entrega: retraso, dano, producto equivocado o faltante.'),
        ('servicio_reembolso', 'Problema con atencion al cliente, devolucion o reembolso.'),
        ('efecto_adverso', 'Su queja principal es que le cayo mal.'),
        ('no_funciona', 'Su queja principal es que no le funciono.'),
        ('ninguna', 'No hay queja ni duda en el texto.')],
    'razon_positiva': [
        ('resultado', 'Lo valora porque le funciono o noto mejoria.'),
        ('sabor_aceptable', 'El sabor es agradable o tolerable.'),
        ('buen_valor', 'Buen precio o vale la pena lo que cuesta.'),
        ('recomienda_recompra', 'Lo recomienda o dice que volvera a comprarlo.'),
        ('confianza_marca', 'Confia en la marca, la calidad o los ingredientes.'),
        ('entrega_servicio', 'Llego rapido o buen servicio.'),
        ('ninguna', 'No da ningun argumento a favor.')],
    'recompra': [
        ('Si', 'Dice que volvio a comprar o que comprara de nuevo.'),
        ('No', 'Dice que no lo volvera a comprar.'),
        ('No lo dice', 'El texto no lo menciona.')],
    'comprador_tipo': [
        ('nuevo', 'Es la primera vez que lo compra.'),
        ('recompra', 'Ya lo habia comprado antes.'),
        ('No lo dice', 'El texto no lo aclara.')],
    'comprador_para': [
        ('para_si_mismo', 'Lo compra para uso propio.'),
        ('para_otra_persona', 'Lo compra para otra persona (pareja, hijo/a, madre, amigo...).'),
        ('No lo dice', 'El texto no lo aclara.')],
}
# Columnas de texto libre (sin desplegable): (columna, ancho, instruccion).
LIBRES = [
    ('frase_literal', 40, 'Copia la frase del cliente que mas serviria como gancho o argumento (tal cual, en ingles).'),
    ('notas_manual', 30, 'Libre: dudas, ironia, texto sin sentido, etc.'),
]
COLUMNAS = ['id', 'titulo', 'texto'] + [c[0] for c in CAMPOS] + [c[0] for c in LIBRES]
# Resenas que son solo un marcador de Amazon (sin texto real): no sirven para etiquetar.
TEXTO_VACIO = 'No se pudo cargar el archivo multimedia'
MESES = {m: i + 1 for i, m in enumerate('enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre'.split())}


def cargar_modulo(nombre):
    """Importa un script hermano de src/ por ruta (src/ no es un paquete y `python -I` no lo agrega al path)."""
    spec = importlib.util.spec_from_file_location(nombre, SRC / (nombre + '.py'))
    mod = importlib.util.module_from_spec(spec); sys.modules[nombre] = mod; spec.loader.exec_module(mod)
    return mod


def semestre(fecha_iso):
    """'2025-03-14' -> '2025-S1' (ene-jun = S1, jul-dic = S2). Es el periodo del analisis de evolucion."""
    return fecha_iso[:4] + ('-S1' if int(fecha_iso[5:7]) <= 6 else '-S2')


def fechas_por_id():
    """id -> fecha ISO, de las DOS bases (bundle y soursop, ver corpus_resenas.py); respaldo: JSON v3 ('... el 6 de diciembre de 2024')."""
    fechas = {r['id']: r['fecha'] for r in cargar_modulo('corpus_resenas').cargar_todo()}
    for r in json.loads((DATA / 'serene_resenas_amazon_v3.json').read_text(encoding='utf-8')):
        m = re.search(r'(\d{1,2}) de (\w+) de (\d{4})', r.get('fecha') or '')
        if r['id'] not in fechas and m and m.group(2) in MESES:
            fechas[r['id']] = f'{m.group(3)}-{MESES[m.group(2)]:02d}-{int(m.group(1)):02d}'
    return fechas


def leer_csv(ruta):
    """Lee un CSV con campos entre comillas que contienen saltos de linea (por eso newline='' y el modulo csv)."""
    with open(ruta, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def reparto_proporcional(tam_estratos, n):
    """Reparte n entre estratos en proporcion a su tamano (metodo del mayor resto); nunca pide mas de lo que hay."""
    total = sum(tam_estratos.values())
    base = {e: int(n * t / total) for e, t in tam_estratos.items()}
    resto = sorted(tam_estratos, key=lambda e: (n * tam_estratos[e] / total - base[e], e), reverse=True)
    for e in resto[:n - sum(base.values())]:
        base[e] += 1
    return {e: min(c, tam_estratos[e]) for e, c in base.items()}


def elegir_ampliacion(corpus, excluir_ids, n, semilla):
    """Elige n resenas nuevas estratificadas por semestre x estrellas (proporcional al corpus), sin repetir `excluir_ids`.
    Estratificar por semestre protege la evolucion por periodo; por estrellas, el balance positivas/negativas."""
    pool = [r for r in corpus if r['id'] not in excluir_ids and TEXTO_VACIO not in r['texto']]
    estratos = defaultdict(list)
    for r in pool:
        estratos[(semestre(r['fecha']), r['estrellas'])].append(r)
    cupos = reparto_proporcional({e: len(v) for e, v in estratos.items()}, n)
    rng = random.Random(semilla)  # semilla fija: la misma ampliacion cada vez que se corra
    elegidas = []
    for e in sorted(estratos):
        elegidas += rng.sample(sorted(estratos[e], key=lambda r: r['id']), cupos[e])
    return elegidas


def altura_fila(texto, ancho=95):
    """Altura aproximada de la fila segun la longitud del texto (openpyxl no autoajusta la altura)."""
    lineas = sum(max(1, math.ceil(len(p) / ancho)) for p in texto.split('\n'))
    return min(409, max(32, 15 * lineas + 6))


def agregar_validaciones(ws, ultima):
    """Crea los desplegables de la hoja 'Etiquetado' (apuntan a la hoja oculta 'Listas'). Se usa al armar la hoja y para
    restaurarlos cuando Excel los guardo en un formato (extension x14) que openpyxl no lee y descarta al volver a guardar."""
    for j, (nombre, valores, estricta, _, _) in enumerate(CAMPOS, start=1):
        col = get_column_letter(3 + j)                         # los campos empiezan en la columna D
        lc = get_column_letter(j)
        dv = DataValidation(type='list', formula1=f'Listas!${lc}$2:${lc}${len(valores) + 1}', allow_blank=True)
        dv.errorStyle = 'stop' if estricta else 'warning'
        dv.errorTitle = 'Valor fuera de la lista'; dv.error = 'Elige un valor de la lista' + ('' if estricta else ' (o varios separados por |)')
        ws.add_data_validation(dv); dv.add(f'{col}2:{col}{ultima}')


def restaurar_validaciones(wb):
    """Si la hoja 'Etiquetado' perdio sus desplegables al cargarla con openpyxl, los vuelve a crear."""
    ws = wb['Etiquetado']
    if not ws.data_validations.dataValidation:
        agregar_validaciones(ws, ws.max_row)


def agregar_guia(wb):
    """Agrega (o reemplaza) la hoja visible 'Guia de valores': que significa cada valor de cada desplegable."""
    if 'Guia de valores' in wb.sheetnames:
        del wb['Guia de valores']
    g = wb.create_sheet('Guia de valores', 2)
    g.append(['columna', 'valor del desplegable', 'que significa / cuando elegirlo'])
    for c in g[1]:
        c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='305496')
    for columna, _, _, _, instruccion in CAMPOS:
        g.append([columna, '', instruccion])
        for c in g[g.max_row]:
            c.font = Font(bold=True); c.fill = PatternFill('solid', fgColor='D9E1F2')
        for valor, sig in GUIA[columna]:
            g.append(['', valor, sig])
    for fila in g.iter_rows(min_row=2):
        for c in fila:
            c.alignment = Alignment(wrap_text=True, vertical='top')
    for letra, ancho in zip('ABC', (22, 28, 110)):
        g.column_dimensions[letra].width = ancho
    g.freeze_panes = 'A2'


def escribir_hoja(ruta, filas, semilla):
    """Escribe el .xlsx: hoja 'Etiquetado' (id, titulo, texto + columnas a rellenar con desplegables) y hoja 'Instrucciones'.
    `filas` = lista de dicts con id/titulo/texto. Se baraja con semilla fija para que el orden no insinue nada."""
    filas = sorted(filas, key=lambda r: r['id'])
    random.Random(semilla).shuffle(filas)
    wb = Workbook()
    ws = wb.active; ws.title = 'Etiquetado'
    ws.append(COLUMNAS)
    n_col = len(COLUMNAS)
    for c in ws[1]:
        c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='305496')
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[1].height = 32
    for i, r in enumerate(filas, start=2):
        ws.append([r['id'], r['titulo'], r['texto']] + [None] * (n_col - 3))
        ws.row_dimensions[i].height = altura_fila(r['titulo'] + '\n' + r['texto'])
        for j in range(1, n_col + 1):
            ws.cell(i, j).alignment = Alignment(wrap_text=True, vertical='top')
    ultima = len(filas) + 1
    anchos = [17, 32, 90] + [c[3] for c in CAMPOS] + [c[1] for c in LIBRES]
    for j, ancho in enumerate(anchos, start=1):
        ws.column_dimensions[get_column_letter(j)].width = ancho
    ws.freeze_panes = 'D2'  # id, titulo y texto siempre visibles al desplazarse
    # Las listas viven en una hoja oculta 'Listas' (una columna por campo): asi no hay limite de 255 caracteres por lista.
    listas = wb.create_sheet('Listas')
    for j, (nombre, valores, _, _, _) in enumerate(CAMPOS, start=1):
        listas.cell(1, j, nombre)
        for i, v in enumerate(valores, start=2):
            listas.cell(i, j, v)
    listas.sheet_state = 'hidden'
    agregar_validaciones(ws, ultima)
    # Celdas por rellenar en amarillo claro; al llenarlas pierden el color (formato condicional).
    amarillo = PatternFill('solid', bgColor='FFF2CC', fgColor='FFF2CC')
    ultimo_campo = get_column_letter(3 + len(CAMPOS))
    ws.conditional_formatting.add(f'D2:{ultimo_campo}{ultima}', FormulaRule(formula=['D2=""'], fill=amarillo))
    ins = wb.create_sheet('Instrucciones', 1)
    texto = ['Etiquetado manual de resenas', '',
             'Lee cada texto y llena las columnas de la hoja Etiquetado (listas desplegables). No hay estrellas ni etiquetas del lexico a proposito.',
             'La columna obligatoria para medir el acierto de sentimiento es sentimiento_manual; las demas sirven para entender al cliente (se pueden dejar vacias).', '']
    texto += [f'- {c[0]}: {c[4]}' for c in CAMPOS] + [f'- {c[0]}: {c[2]}' for c in LIBRES]
    texto += ['', 'No cambies id, titulo ni texto. Guarda el archivo como .xlsx en la misma carpeta (data/).',
              'Despues corre: .venv/bin/python -I src/acierto_sentimiento.py --hoja <este archivo>', '', 'Sentimiento etiquetado:']
    texto.insert(5, 'Que significa cada valor de los desplegables: mira la hoja "Guia de valores".')
    for t in texto:
        ins.append([t])
    ins.append([f'=COUNTA(Etiquetado!D2:D{ultima})&" de {len(filas)}"'])
    ins['A1'].font = Font(bold=True, size=14); ins[f'A{len(texto)}'].font = Font(bold=True)
    ins.column_dimensions['A'].width = 120
    agregar_guia(wb)
    wb.save(ruta)


def main():
    ap = argparse.ArgumentParser(description='Hoja de etiquetado manual de resenas')
    ap.add_argument('--ampliar', type=int, default=0, help='N resenas NUEVAS estratificadas (semestre x estrellas), en otra hoja; no repite validacion_100')
    ap.add_argument('--base', choices=['bundle', 'soursop'], default='bundle', help='de que base se sacan las resenas de --ampliar')
    ap.add_argument('--semilla', type=int, default=42)
    ap.add_argument('--solo-guia', action='store_true', help='agrega/actualiza la hoja "Guia de valores" en las hojas .xlsx existentes sin tocar sus etiquetas')
    ap.add_argument('--forzar', action='store_true', help='permite sobrescribir una hoja existente (perderia sus etiquetas)')
    a = ap.parse_args()
    if a.solo_guia:
        from openpyxl import load_workbook
        for ruta in sorted(DATA.glob('etiquetado_manual_*.xlsx')):
            wb = load_workbook(ruta); restaurar_validaciones(wb); agregar_guia(wb); wb.save(ruta); print(f'guia agregada -> {ruta}')
        return
    base = leer_csv(DATA / 'validacion_100.csv')
    if a.ampliar:
        cp = cargar_modulo('corpus_resenas')
        corpus = cp.cargar_bundle() if a.base == 'bundle' else cp.cargar_soursop()
        elegidas = elegir_ampliacion(corpus, {r['id'] for r in base}, a.ampliar, a.semilla)
        filas = [{'id': r['id'], 'titulo': r['titulo'], 'texto': r['texto']} for r in elegidas]
        nombre = f'ampliacion_{a.ampliar}' if a.base == 'bundle' else f'soursop_{a.ampliar}'   # el nombre de la ampliacion del bundle no cambia
        ruta = DATA / f'etiquetado_manual_{nombre}.xlsx'
        if ruta.exists() and not a.forzar:
            raise SystemExit(f'{ruta} ya existe; no se sobrescribe (usa --forzar si de verdad quieres rehacerla).')
        # Registro de la muestra (con estrellas y estrato) para poder auditarla; NO se le muestra al etiquetador.
        reg = DATA / f'validacion_{nombre}.csv'
        with reg.open('w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f); w.writerow(['id', 'estrellas', 'fecha', 'semestre'])
            w.writerows([(r['id'], r['estrellas'], r['fecha'], semestre(r['fecha'])) for r in elegidas])
    else:
        filas = [{'id': r['id'], 'titulo': r['titulo'], 'texto': r['texto']} for r in base]
        ruta = DATA / 'etiquetado_manual_100.xlsx'
    if ruta.exists() and not a.forzar:
        raise SystemExit(f'{ruta} ya existe; no se sobrescribe (usa --forzar si de verdad quieres rehacerla).')
    escribir_hoja(ruta, filas, a.semilla)
    print(f'{len(filas)} resenas -> {ruta}')


if __name__ == '__main__':
    main()
