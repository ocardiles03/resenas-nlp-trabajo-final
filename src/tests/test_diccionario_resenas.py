"""Pruebas pequeñas: negación, límites y reconciliación de entregables C/E."""
import importlib.util
import json
from pathlib import Path
import sqlite3
import unittest
import csv
from contextlib import closing

TOOLS=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('construir_diccionario',TOOLS/'construir_diccionario.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class DiccionarioTests(unittest.TestCase):
    def test_limites_y_negacion(self):
        self.assertFalse(m.matches('gas','vegas'))
        self.assertTrue(m.matches("ain't", "This ain’t bad"))
        self.assertTrue(m.negated('work', "It doesn't work"))
        self.assertFalse(m.negated('worked', 'It worked'))

    def test_entregables(self):
        folder=m.DEFAULT
        source=json.loads((folder/'serene_resenas_amazon_v3.json').read_text())
        dictionary=json.loads((folder/'diccionario_propio_v1.json').read_text())
        self.assertEqual(dictionary['_meta']['resenas'],len(source))
        with closing(sqlite3.connect(folder/'resenas.db')) as c:
            self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            ids={x[0] for x in c.execute('SELECT id FROM resenas')}
            self.assertTrue({r['id'] for r in source} <= ids)
            self.assertEqual(c.execute("SELECT COUNT(DISTINCT id_resena) FROM etiquetas WHERE tipo='sentimiento' AND version_dicc=?",(m.VERSION,)).fetchone()[0],len(ids))
        with (folder/'validacion_100.csv').open(encoding='utf-8-sig') as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),100)
        self.assertEqual(len({r['id'] for r in rows}),100)
        self.assertEqual({int(float(r['estrellas'])) for r in rows},set(range(1,6)))
        self.assertTrue(all('temas_manual' in r and 'temas_producto_manual' in r for r in rows))

    def test_excel_demografia_reconcilia_base(self):
        from openpyxl import load_workbook
        with closing(sqlite3.connect(m.DEFAULT/'resenas.db')) as conn:
            expected = {(rid,kind):value for rid,kind,value in conn.execute("SELECT id_resena,tipo,valor FROM etiquetas WHERE version_dicc=? AND tipo IN ('genero','genero_confianza','zona_detalle')", (m.VERSION,))}
        wb=load_workbook(m.DEFAULT/'resenas_bundle_serene_v2.xlsx',read_only=True)
        rows=wb['Reseñas'].iter_rows(values_only=True)
        headers=next(rows)
        seen=set()
        for row in rows:
            record=dict(zip(headers,row)); rid=record['ID']; seen.add(rid)
            self.assertEqual(record['Genero estimado'],expected[rid,'genero'])
            self.assertEqual(record['Confianza genero'],expected[rid,'genero_confianza'])
            geo=json.loads(expected[rid,'zona_detalle'])
            regions=', '.join(sorted({x['region'] for x in geo['menciones'] if x['region']}))
            self.assertEqual(record['Region'] or '',regions)
            if regions:self.assertTrue(record['Evidencia region'])
        self.assertEqual(len(seen),1226)
        wb.close()

if __name__=='__main__': unittest.main()
