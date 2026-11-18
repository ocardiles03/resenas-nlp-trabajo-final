"""Hoja de etiquetado manual y medicion de acierto del sentimiento (casos pequenos con respuesta conocida a mano)."""
import importlib.util
import math
import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook

TOOLS = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / (name + '.py'))
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod)
    return mod


class HojaEtiquetadoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.he = load('hoja_etiquetado')

    def test_semestre(self):
        self.assertEqual(self.he.semestre('2025-06-30'), '2025-S1')
        self.assertEqual(self.he.semestre('2025-07-01'), '2025-S2')

    def test_reparto_proporcional(self):
        self.assertEqual(self.he.reparto_proporcional({'a': 50, 'b': 30, 'c': 20}, 10), {'a': 5, 'b': 3, 'c': 2})
        self.assertEqual(sum(self.he.reparto_proporcional({'a': 50, 'b': 30, 'c': 20}, 7).values()), 7)
        # nunca pide mas de lo que tiene un estrato
        self.assertEqual(self.he.reparto_proporcional({'a': 1, 'b': 1}, 5), {'a': 1, 'b': 1})

    def test_ampliacion_no_repite_y_es_reproducible(self):
        corpus = [{'id': f'R{i}', 'estrellas': 1 + i % 5, 'fecha': f'202{4 + i % 3}-0{1 + i % 9}-15', 'texto': 'texto bueno', 'titulo': 't'}
                  for i in range(120)]
        corpus.append({'id': 'RVACIO', 'estrellas': 1, 'fecha': '2025-01-01', 'texto': 'No se pudo cargar el archivo multimedia.', 'titulo': 't'})
        excluir = {f'R{i}' for i in range(10)}
        a = self.he.elegir_ampliacion(corpus, excluir, 30, 42)
        b = self.he.elegir_ampliacion(corpus, excluir, 30, 42)
        self.assertEqual([r['id'] for r in a], [r['id'] for r in b])
        self.assertEqual(len(a), 30)
        self.assertFalse({r['id'] for r in a} & excluir)
        self.assertNotIn('RVACIO', {r['id'] for r in a})

    def test_hoja_sin_estrellas_y_con_desplegables(self):
        filas = [{'id': f'R{i}', 'titulo': f'titulo {i}', 'texto': 'texto\ncon salto'} for i in range(5)]
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / 'hoja.xlsx'
            self.he.escribir_hoja(ruta, filas, 42)
            wb = load_workbook(ruta)
            ws = wb['Etiquetado']
            self.assertEqual([c.value for c in ws[1]], self.he.COLUMNAS)       # solo las columnas esperadas
            self.assertFalse([c for c in ws[1] if 'estrella' in str(c.value).lower() or 'lexico' in str(c.value).lower()])
            self.assertEqual(ws.max_row, 6)
            for fila in ws.iter_rows(min_row=2, min_col=4, max_col=8, values_only=True):
                self.assertEqual(set(fila), {None})                            # nada viene prellenado
            listas = [dv.formula1 for dv in ws.data_validations.dataValidation]
            self.assertEqual(len(listas), len(self.he.CAMPOS))                 # un desplegable por campo
            self.assertEqual(wb['Listas'].sheet_state, 'hidden')
            self.assertEqual([c.value for c in wb['Listas'][1]], [c[0] for c in self.he.CAMPOS])
            self.assertEqual([c.value for c in wb['Listas']['A'][1:4]], ['Positivo', 'Negativo', 'Neutro'])
            # cada desplegable apunta a una columna de Listas con tantos valores como tiene su campo
            for dv, (_, valores, _, _, _) in zip(ws.data_validations.dataValidation, self.he.CAMPOS):
                self.assertTrue(dv.formula1.endswith(str(len(valores) + 1)))
            self.assertEqual(ws.cell(1, 4).value, 'sentimiento_manual')         # el acierto de sentimiento lee la columna D


class AciertoSentimientoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ac = load('acierto_sentimiento')

    def test_metricas_caso_a_mano(self):
        # prediccion positiva si puntaje > 0 -> [1,1,1,0,0,0]: VP=2, FN=1, FP=1, VN=2
        m = self.ac.metricas([1, 1, 0, 0, 1, 0], [0.9, 0.2, 0.1, -0.5, -0.2, 0.0])
        self.assertEqual((m['vp'], m['fn'], m['fp'], m['vn']), (2, 1, 1, 2))
        for k in ('exactitud', 'sensibilidad', 'especificidad', 'precision', 'f1'):
            self.assertAlmostEqual(m[k], 2 / 3)
        self.assertAlmostEqual(m['auc'], 7 / 9)                                # 7 de 9 parejas (positiva, negativa) bien ordenadas

    def test_metricas_una_sola_clase(self):
        m = self.ac.metricas([1, 1], [0.5, 0.7])
        self.assertIsNone(m['auc'])
        self.assertTrue(math.isnan(m['especificidad']))

    def test_wilson(self):
        lo, hi = self.ac.wilson(5, 10)
        self.assertTrue(0 <= lo < 0.5 < hi <= 1)
        self.assertAlmostEqual((lo + hi) / 2, 0.5, places=6)
        self.assertTrue(all(math.isnan(x) for x in self.ac.wilson(0, 0)))

    def test_segunda_lectura_a_mano(self):
        # y = [+, -, -, +]; el lexico deja pasar la queja 1 (fp); el KNN la marca pero tambien marca el elogio 3 (falsa alarma)
        f = {x['regla']: x for x in self.ac.segunda_lectura([1, 0, 0, 1], [1, 1, -1, 1], [1, -1, -1, -1], [1, 1, -1, 1])}
        self.assertEqual((f['Léxico solo']['fp'], f['Léxico solo']['fn']), (1, 0))
        u = f['Léxico O KNN (segunda lectura)']
        self.assertEqual((u['fp'], u['fn']), (0, 1))
        self.assertAlmostEqual(u['pct_marcadas'], 0.75)                        # marca 3 de 4 reseñas
        self.assertEqual(u['costo_c3'], 3 * 0 + 1)                             # costo = c*fp + fn
        self.assertEqual((f['Léxico Y KNN']['fp'], f['Léxico Y KNN']['fn']), (1, 0))   # la interseccion marca solo la queja 2

    def test_c_equilibrio_a_mano(self):
        filas = [{'regla': 'X', 'fp': 1, 'fn': 26}, {'regla': 'Y', 'fp': 4, 'fn': 17}, {'regla': 'Z', 'fp': 12, 'fn': 24}]
        self.assertAlmostEqual(self.ac.c_equilibrio(filas, 'X'), 3.0)           # contra Y: 1c + 26 <= 4c + 17  ->  c >= 3
        self.assertIsNone(self.ac.c_equilibrio(filas, 'Y'))                     # X tiene menos fp: gana cuando c es grande
        self.assertEqual(self.ac.c_equilibrio([{'regla': 'X', 'fp': 0, 'fn': 4}, {'regla': 'Y', 'fp': 0, 'fn': 4}], 'X'), 0.0)   # empate total

    def test_perfil_y_semestres_de_grupos_a_mano(self):
        import numpy as np
        filas = [{'titulo': 'a', 'texto': 'plastic bottle', 'estrellas': 1, 'compra_verificada': 'Sí', 'semestre': '2025-S1'},
                 {'titulo': 'b', 'texto': 'switched to plastic', 'estrellas': 2, 'compra_verificada': 'No', 'semestre': '2025-S1'},
                 {'titulo': 'c', 'texto': 'great', 'estrellas': 5, 'compra_verificada': 'Sí', 'semestre': '2025-S2'},
                 {'titulo': 'd', 'texto': 'love it', 'estrellas': 4, 'compra_verificada': 'Sí', 'semestre': '2025-S2'}]
        et = np.array([1, 1, 0, 0])
        p = {x['grupo']: x for x in self.ac.perfil_grupos(filas, et)}
        self.assertEqual((p[1]['n'], p[1]['pct']), (2, 0.5))
        self.assertAlmostEqual(p[1]['estrellas_prom'], 1.5); self.assertAlmostEqual(p[0]['pct_4_5'], 1.0)
        self.assertAlmostEqual(p[1]['pct_verificada'], 0.5)
        self.assertAlmostEqual(p[1]['Cambio a botella de plastico'], 1.0)   # las dos mencionan plástico
        s = {x['semestre']: x for x in self.ac.grupos_por_semestre(filas, et)}
        self.assertEqual((s['2025-S1']['grupo_1'], s['2025-S2']['grupo_0']), (1.0, 1.0))

    def test_lectura_lexico(self):
        self.assertEqual([self.ac.lectura_lexico(s) for s in (3, 0, -2)], ['Positivo', 'Neutro', 'Negativo'])

    def test_leer_hojas_alias_y_pendientes(self):
        he = load('hoja_etiquetado')
        filas = [{'id': f'R{i}', 'titulo': 't', 'texto': 'x'} for i in range(4)]
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / 'h.xlsx'
            he.escribir_hoja(ruta, filas, 1)
            wb = load_workbook(ruta); ws = wb['Etiquetado']
            ws['D2'], ws['D3'], ws['D4'] = 'Neutral', 'Positivo', 'valor raro'   # D5 queda vacia
            wb.save(ruta)
            leidas, pendientes = self.ac.leer_hojas([ruta])
        self.assertEqual(sorted(r['manual'] for r in leidas), ['Neutro', 'Positivo'])
        self.assertEqual(len(pendientes), 2)

    def test_evaluar_de_punta_a_punta_con_etiquetas_en_memoria(self):
        # Etiquetas derivadas de las estrellas SOLO en memoria (no se lee ni escribe ningun dato del proyecto).
        corpus = self.ac.dc.cargar(self.ac.dc.XLSX)
        muestra = corpus[:90]
        filas = [{'id': r['id'], 'titulo': r['titulo'], 'texto': r['texto'], 'semestre': self.ac.he.semestre(r['fecha']),
                  'manual': 'Positivo' if r['estrellas'] >= 4 else ('Negativo' if r['estrellas'] <= 2 else 'Neutro')} for r in muestra]
        res = self.ac.evaluar(filas, corpus)
        self.assertEqual(res['n_train'] + res['n_test'], 90)
        self.assertEqual(res['n_test'], 18)                                    # 20 %
        self.assertEqual(set(res['prueba']), {'Lexico del proyecto', 'Lexico sin la muestra', 'KNN con estrellas', 'Naive Bayes con estrellas', 'KNN con etiquetas manuales'})
        self.assertIn(res['k_manual'], self.ac.KS)
        self.assertEqual(int(res['m3'].sum()), 90)                              # la matriz de 3 clases cuenta toda la muestra
        self.assertEqual(sum(e['n'] for e in res['evol']), 90)
        again = self.ac.evaluar([dict(f) for f in filas], corpus)               # semilla fija: mismo resultado
        self.assertEqual(res['k_manual'], again['k_manual'])
        self.assertEqual(res['prueba']['KNN con etiquetas manuales'], again['prueba']['KNN con etiquetas manuales'])


if __name__ == '__main__':
    unittest.main()
