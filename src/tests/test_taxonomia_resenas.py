"""Fusion de aliases, contexto de producto y conciliacion de conteos."""
from collections import Counter
from contextlib import closing
import csv
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

TOOLS=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,TOOLS/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

tax=load('taxonomia_resenas')
builder=load('construir_diccionario')
base=load('base_resenas')


class TaxonomiaTests(unittest.TestCase):
    def test_fusion_no_duplica_frecuencia_ni_pierde_fuentes(self):
        def entry(source):return {'termino':'heartburn','frecuencia':4,'resenas':3,'fuentes':[source]}
        result=tax.fusionar({'acid_reflux_heartburn':{'heartburn':entry('mesh')},'acidez_reflujo':{'heartburn':entry('manual')}})
        self.assertEqual(set(result),{'acidez_reflujo'})
        self.assertEqual(result['acidez_reflujo']['heartburn']['frecuencia'],4)
        self.assertEqual(set(result['acidez_reflujo']['heartburn']['fuentes']),{'mesh','manual'})
        with self.assertRaises(ValueError):tax.canonical('nuevo_sin_canon')

    def test_migracion_idempotente_preserva_otras_versiones(self):
        with closing(sqlite3.connect(':memory:')) as conn:
            conn.executescript(base.SCHEMA)
            conn.executemany('INSERT INTO etiquetas VALUES (?,?,?,?,?)',[
                ('R1','tema_salud','constipation','mesh','propio_v1'),
                ('R1','tema_salud','estrenimiento','manual','propio_v1'),
                ('R1','tema_salud','constipation','manual','historico')])
            tax.migrar_etiquetas(conn,'propio_v1');tax.migrar_etiquetas(conn,'propio_v1')
            self.assertEqual(conn.execute("SELECT valor FROM etiquetas WHERE version_dicc='propio_v1'").fetchall(),[('estrenimiento',)])
            self.assertEqual(conn.execute("SELECT valor FROM etiquetas WHERE version_dicc='historico'").fetchall(),[('constipation',)])

    def test_contexto_y_queja_no_equivale_a_mencion(self):
        def dictionary(group,*terms):return {group:[{'termino':t} for t in terms]}
        self.assertFalse(tax.operativos('i came back feeling different.',dictionary('entrega_pedido','came','different')))
        self.assertFalse(tax.operativos('real good!',dictionary('dudas_autenticidad','real')))
        self.assertFalse(tax.operativos('this changed my life.',dictionary('dudas_autenticidad','changed')))
        self.assertFalse(tax.operativos('i used to be tired.',dictionary('dudas_autenticidad','used to')))
        self.assertFalse(tax.quejas('it is not fake.',{'dudas_autenticidad':['fake']}))
        self.assertFalse(tax.quejas('no leaks in the bottle.',{'envase_plastico_vidrio':['bottle']}))
        self.assertEqual(tax.quejas('no refund.',{'precio_valor':['refund']}),['precio_valor'])
        self.assertFalse(tax.operativos('i have a strong body.',dictionary('sabor','strong')))
        self.assertTrue(tax.operativos('the order came damaged.',dictionary('entrega_pedido','came','damaged')))
        hits=tax.operativos('glass bottle.',dictionary('envase_plastico_vidrio','glass','bottle'))
        self.assertTrue(hits)
        self.assertFalse(tax.quejas('glass bottle.',hits))
        self.assertEqual(tax.quejas('my bottle is leaking.',hits),['envase_plastico_vidrio'])

    def test_preserva_correcciones_y_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'validacion.csv'
            builder.write_csv(path,[{'id':'R1','tema_salud':'constipation','temas_manual':'estrenimiento','notas_manual':'corregido'}],['id','tema_salud','temas_manual','notas_manual'])
            sample=[{'id':'R1','tema_salud':'estrenimiento','temas_manual':'','notas_manual':''}]
            builder.preservar_correcciones(path,sample)
            self.assertEqual(sample[0]['temas_manual'],'estrenimiento')
            self.assertEqual(sample[0]['notas_manual'],'corregido')
            self.assertEqual(sample[0]['tema_salud'],'estrenimiento')
            with self.assertRaises(RuntimeError):builder.preservar_correcciones(path,[{'id':'R2'}])

    def test_diccionario_150_y_conciliacion_excel(self):
        from openpyxl import load_workbook
        folder=builder.DEFAULT
        dictionary=json.loads((folder/'diccionario_propio_v1.json').read_text())
        self.assertEqual(set(dictionary['temas']),tax.CANONICOS)
        self.assertEqual(set(dictionary['temas_producto']),set(tax.SEMILLAS))
        with (folder/'terminos_producto_top150.csv').open(encoding='utf-8-sig') as f: terms=list(csv.DictReader(f))
        self.assertEqual(len({e['termino'] for e in terms}),150)
        self.assertTrue(all(int(e['frecuencia'])>0 for e in terms))
        for e in terms:self.assertIn(e['termino'],{x['termino'] for x in dictionary['temas_producto'][e['tema']]})
        for theme,seeds in tax.SEMILLAS.items():self.assertTrue(set(seeds.split('|')) <= {e['termino'] for e in dictionary['temas_producto'][theme]})
        with closing(sqlite3.connect(folder/'resenas.db')) as conn:
            counts=Counter((kind,value,int(star)) for kind,value,star in conn.execute("SELECT tipo,valor,estrellas FROM etiquetas JOIN resenas ON id_resena=resenas.id WHERE asin='B0D4MPKGN6' AND version_dicc='propio_v1' AND tipo IN ('tema_salud','tema_producto')"))
        self.assertTrue({value for kind,value,_ in counts if kind=='tema_salud'} <= tax.CANONICOS)
        wb=load_workbook(folder/'resenas_bundle_serene_v2.xlsx',read_only=True)
        rows=wb['Temas'].iter_rows(values_only=True);next(rows)
        for group,theme,total,*stars in rows:
            kind='tema_salud' if group=='Salud' else 'tema_producto'
            self.assertEqual(list(stars),[counts[kind,theme,s] for s in range(1,6)])
            self.assertEqual(total,sum(stars))
        reviews=wb['Reseñas'].iter_rows(values_only=True);headers=next(reviews)
        for row in reviews:self.assertEqual(row[headers.index('Cobertura region')],'BAJA COBERTURA')
        wb.close()

if __name__=='__main__':unittest.main()
