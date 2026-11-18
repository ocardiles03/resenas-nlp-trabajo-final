#!/usr/bin/env python3
"""E: exporta la base etiquetada a un Excel organizado. No modifica la base."""
import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import sqlite3
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter

DEFAULT = Path(__file__).resolve().parents[1] / 'data'
VERSION = 'propio_v1'


def exportar(folder, db, output):
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute("SELECT * FROM resenas WHERE asin='B0D4MPKGN6' ORDER BY fecha DESC,id")  # solo el bundle; la base trae mas ASIN]
        labels = defaultdict(lambda: defaultdict(list))
        for r in conn.execute("SELECT * FROM etiquetas WHERE version_dicc=? AND id_resena IN (SELECT id FROM resenas WHERE asin='B0D4MPKGN6') ORDER BY tipo,valor", (VERSION,)):
            labels[r['id_resena']][r['tipo']].append(r['valor'])
    dictionary = json.loads((folder/'diccionario_propio_v1.json').read_text())
    wb = Workbook(); wb.remove(wb.active)
    def sheet(name, headers, data):
        ws = wb.create_sheet(name); ws.append(headers)
        for row in data:
            ws.append(row)
        for row in ws:
            for c in row:
                # Las reseñas son datos no confiables: nunca fórmulas Excel.
                if c.data_type == 'f': c.data_type = 's'
                c.alignment = Alignment(vertical='top', wrap_text=True)
        for c in ws[1]:
            c.fill = PatternFill('solid', fgColor='234E52'); c.font = Font(color='FFFFFF', bold=True)
        ws.row_dimensions[1].height = 30
        ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
        for i,h in enumerate(headers,1):
            ws.column_dimensions[get_column_letter(i)].width = 72 if h.lower()=='texto' else 38 if h in ('Titulo','Termino','Variante','Valor','temas_manual') else 24
        ws.sheet_view.showGridLines=False
        return ws
    summary = [['Total reseñas',len(rows)],['Estrellas promedio', round(sum(r['estrellas'] or 0 for r in rows)/len(rows),3)],['Compra verificada',sum(r['verificada'] for r in rows)],['Nota','Genero estimado; regiones mencionadas, no residencia. Etiquetas no validadas.'],['Diccionario', VERSION],['Corpus de entrenamiento',dictionary['_meta']['resenas']]]
    for title, kind in [('Estrellas','estrellas'),('Variante','variante'),('Mes','mes'),('Genero estimado','genero'),('Confianza genero','genero_confianza')]:
        counts=Counter((r['fecha'][:7] or 'Sin fecha') if kind=='mes' else '|'.join(labels[r['id']].get(kind,[])) or 'Sin dato' if kind in ('genero','genero_confianza') else r[kind] for r in rows)
        summary.append([title,'Conteo'])
        summary.extend([[k,n] for k,n in sorted(counts.items(),key=lambda x:str(x[0]))])
    summary += [['Region EEUU mapeada',sum(bool(labels[r['id']].get('zona')) for r in rows)],['Genero Hombre/Mujer',sum(any(v in ('Hombre','Mujer') for v in labels[r['id']].get('genero',[])) for r in rows)]]
    one_star=[r for r in rows if r['estrellas']==1]
    def has_topic(r):return bool(labels[r['id']].get('tema_salud') or labels[r['id']].get('tema_producto'))
    def explained(r):return bool(labels[r['id']].get('queja_producto') or set(labels[r['id']].get('resultado',[])) & {'sin_efecto','efecto_adverso'})
    summary += [['Con temas totales',sum(has_topic(r) for r in rows)],
                ['Con tema salud',sum(bool(labels[r['id']].get('tema_salud')) for r in rows)],
                ['Con tema operacion/producto',sum(bool(labels[r['id']].get('tema_producto')) for r in rows)],
                ['1 estrella con tema',sum(has_topic(r) for r in one_star)],
                ['1 estrella explicadas (reglas)',sum(explained(r) for r in one_star)],
                ['Base de 1 estrella',len(one_star)],
                ['Aviso region',f"BAJA COBERTURA: {sum(bool(labels[r['id']].get('zona')) for r in rows)}/{len(rows)}; menciones, no residencia."],
                ['Que significa explicadas','Senal de queja concreta o resultado negativo; no basta mencionar un tema. Pendiente de validacion humana.']]
    sheet('Resumen',['Indicador','Valor'],summary)
    def tag(r,kind):return ', '.join(labels[r['id']].get(kind,[]))
    def principal(r):
        import re
        text=(r['titulo']+'. '+r['texto']).lower().replace('’',"'")
        kinds=labels[r['id']].get('emocion',[])
        return min(kinds,key=lambda k:(-sum(bool(re.search(r'(?<![a-z0-9])'+re.escape(e['termino'])+r'(?![a-z0-9])',text)) for e in dictionary['emociones'][k]),k)) if kinds else ''
    def detail(r, kind):
        return json.loads(labels[r['id']].get(kind,['{}'])[0])
    def geo_evidence(r):
        return ' | '.join(m['evidencia'] for m in detail(r,'zona_detalle').get('menciones',[]))
    def gen_evidence(r):
        d=detail(r,'genero_evidencia')
        return f"nombre: {d.get('nombre_token','')} ({d.get('nombre_genero','')}); texto: " + ', '.join(e['pista'] for e in d.get('evidencia',[])) + ('; CONFLICTO' if d.get('conflicto') else '')
    headers=['ID','Fecha ISO','Estrellas','Titulo','Texto','Variante','Verificada','Util','Fotos','Nombre','Genero estimado','Sentimiento','Emocion principal','Temas de salud','Resultado','Region','Confianza genero','Evidencia genero','Estado','Division','Evidencia region','Origen cultural autorreferido','Menciones culturales','Temas operacion/producto','Evidencia temas producto','Quejas producto','Cobertura region']
    ws=sheet('Reseñas',headers,[[r['id'],r['fecha'],r['estrellas'],r['titulo'],r['texto'],r['variante'],r['verificada'],r['util'],r['fotos'],r['nombre'],tag(r,'genero'),tag(r,'sentimiento'),principal(r),tag(r,'tema_salud'),tag(r,'resultado'),tag(r,'zona'),tag(r,'genero_confianza'),gen_evidence(r),tag(r,'estado'),tag(r,'division'),geo_evidence(r),tag(r,'origen_cultural'),' | '.join(m['evidencia'] for m in detail(r,'zona_detalle').get('cultural',[])),tag(r,'tema_producto'),tag(r,'evidencia_producto'),tag(r,'queja_producto'),'BAJA COBERTURA'] for r in rows])
    region_col=headers.index('Region')+1
    ws.cell(1,region_col).comment=Comment(f"BAJA COBERTURA: {sum(bool(labels[r['id']].get('zona')) for r in rows)}/{len(rows)} reseñas mencionan una region mapeable. No interpretar como residencia ni como muestra representativa.",'Codex')
    ws.cell(1,region_col).fill=PatternFill('solid',fgColor='9C6500')
    colors={1:'F8D7DA',2:'FCE5CD',3:'FFF2CC',4:'E2F0D9',5:'C6E0B4'}
    for row in ws.iter_rows(min_row=2):
        row[2].fill=PatternFill('solid',fgColor=colors.get(int(row[2].value or 0),'FFFFFF'))
        ws.row_dimensions[row[0].row].height=46
    topic_data=[]
    for group,kind,section in [('Salud','tema_salud','temas'),('Operacion/Producto','tema_producto','temas_producto')]:
        for value in sorted(dictionary[section]):
            counts=Counter(int(r['estrellas']) for r in rows if value in labels[r['id']].get(kind,[]))
            topic_data.append([group,value,sum(counts.values())]+[counts[s] for s in range(1,6)])
    themes=sheet('Temas',['Grupo','Tema','Total','1 estrella','2 estrellas','3 estrellas','4 estrellas','5 estrellas'],topic_data)
    themes.column_dimensions['A'].width=26
    themes.column_dimensions['B'].width=34
    for row in themes.iter_rows(min_row=2):
        row[0].fill=PatternFill('solid',fgColor='E2F0D9' if row[0].value=='Salud' else 'DDEBF7')
    for name, kind, section in [('Emociones','emocion','emociones'),('Regiones','zona','regiones')]:
        categories=set(dictionary[section]) | {v for r in rows for v in labels[r['id']].get(kind,[])}
        data=[]
        for value in sorted(categories):
            counts=Counter(int(r['estrellas']) for r in rows if value in labels[r['id']].get(kind,[]))
            data.append([value,sum(counts.values())]+[counts[s] for s in range(1,6)])
        if name=='Regiones':
            for extra in ('estado','division'):
                for value in sorted({v for r in rows for v in labels[r['id']].get(extra,[])}):
                    counts=Counter(int(r['estrellas']) for r in rows if value in labels[r['id']].get(extra,[]))
                    data.append([extra+': '+value,sum(counts.values())]+[counts[s] for s in range(1,6)])
        sheet(name,['Categoria','Total','1 estrella','2 estrellas','3 estrellas','4 estrellas','5 estrellas'],data)
    sheet('Diccionario',['Capa','Categoria','Termino','Frecuencia','Reseñas','Fuentes'],[[section,group,e['termino'],e['frecuencia'],e['resenas'],', '.join(e['fuentes'])] for section,groups in dictionary.items() if section!='_meta' for group,entries in groups.items() for e in entries])
    with (folder/'validacion_100.csv').open(encoding='utf-8-sig',newline='') as f:
        reader=csv.reader(f); headers=next(reader); sheet('Validacion',headers,list(reader))
    wb.save(output)
    check=load_workbook(output,read_only=True,data_only=False)
    assert check.sheetnames==['Resumen','Reseñas','Temas','Emociones','Regiones','Diccionario','Validacion']
    assert check['Reseñas'].max_row==len(rows)+1 and check['Validacion'].max_row==101
    assert not any(c.data_type=='f' for ws in check for row in ws for c in row)
    check.close()
    print(f'{output}: {len(rows)} reseñas, 7 hojas; verificacion de filas y formulas OK')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--carpeta',type=Path,default=DEFAULT); p.add_argument('--db',type=Path,default=DEFAULT/'resenas.db'); p.add_argument('--salida',type=Path,default=DEFAULT/'resenas_bundle_serene_v2.xlsx'); a=p.parse_args(); exportar(a.carpeta,a.db,a.salida)
