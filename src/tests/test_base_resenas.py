"""Pruebas de almacenamiento en una base temporal; ejecutar con python3 -I."""
import ast
from contextlib import closing
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('base_resenas', TOOLS / 'base_resenas.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


class BaseTests(unittest.TestCase):
    def test_parseo_equivalente_excel(self):
        tree = ast.parse((TOOLS / 'resenas_amazon_excel.py').read_text())
        names = {'MESES', 'MONTHS', 'parsear_fecha', 'votos'}
        nodes = [n for n in tree.body if
                 (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in n.targets)) or
                 (isinstance(n, ast.FunctionDef) and n.name in names)]
        ns = {'re': base.re}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), '<parseadores Excel>', 'exec'), ns)
        for s in ['Calificado en Estados Unidos el 21 de octubre de 2026',
                  'Reviewed in the United States on January 2, 2025', '', 'desconocida']:
            self.assertEqual(base.parsear_fecha(s), ns['parsear_fecha'](s))
        for s in ['', 'Una persona encontró esto útil', 'One person found this helpful', '1,234 people']:
            self.assertEqual(base.votos(s), ns['votos'](s))

    def test_idempotencia_transaccion_y_exportacion(self):
        with tempfile.TemporaryDirectory() as tmp, closing(sqlite3.connect(':memory:')) as conn:
            conn.executescript(base.SCHEMA)
            p = Path(tmp) / 'entrada.json'
            p.write_text(json.dumps({'R1': {'id': 'R1', 'estrellas': '4.0 de 5', 'verificada': True}}))
            base.importar(conn, p)
            original = conn.execute('SELECT * FROM resenas').fetchone()
            conn.execute("INSERT INTO etiquetas VALUES ('R1','tema_salud','digestion','manual','v0')")
            conn.commit()
            base.importar(conn, p)
            self.assertEqual(conn.execute('SELECT * FROM resenas').fetchall(), [original])
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM etiquetas').fetchone()[0], 1)
            p.write_text(json.dumps([{'id': 'R2'}, {'estrellas': '5'}]))
            with self.assertRaises(ValueError):
                base.importar(conn, p)
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM resenas').fetchone()[0], 1)
            columns = [r[1] for r in conn.execute('PRAGMA table_info(resenas)')]
            p.write_text(json.dumps({'R1': dict(zip(columns, original))}))
            with closing(sqlite3.connect(':memory:')) as other:
                other.executescript(base.SCHEMA)
                base.importar(other, p)
                exported = other.execute('SELECT * FROM resenas').fetchone()
                self.assertEqual(exported[:-1], original[:-1])


if __name__ == '__main__':
    unittest.main()
