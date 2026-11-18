"""Carga de las dos bases, detectores del etiquetado automatico y acuerdo con la hoja manual (casos con respuesta conocida a mano)."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / (name + '.py'))
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod)
    return mod


class CorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cp = load('corpus_resenas')

    def test_dos_bases_disjuntas_y_con_texto(self):
        b1, b2 = self.cp.cargar_bundle(), self.cp.cargar_soursop()
        self.assertEqual({r['base'] for r in b1}, {'bundle'})
        self.assertEqual({r['base'] for r in b2}, {'soursop'})
        self.assertFalse({r['id'] for r in b1} & {r['id'] for r in b2})
        for r in b1 + b2:
            self.assertTrue(r['texto'].strip())
            self.assertRegex(r['fecha'], r'^\d{4}-\d{2}-\d{2}$')
            self.assertIn(r['estrellas'], (1, 2, 3, 4, 5))

    def test_semestre(self):
        self.assertEqual(self.cp.semestre('2026-06-30'), '2026-S1')
        self.assertEqual(self.cp.semestre('2026-07-01'), '2026-S2')


class DetectoresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ec = load('etiquetar_corpus')

    def test_recompra(self):
        d = self.ec.det_recompra
        self.assertEqual(d('I will definitely reorder this'), {'si'})
        self.assertEqual(d("I won't buy again"), {'no'})          # la negacion gana a 'buy again'
        self.assertEqual(d('tastes ok'), {'no_lo_dice'})

    def test_comprador(self):
        self.assertEqual(self.ec.det_comprador_tipo('This is my second bottle'), {'recompra'})
        self.assertEqual(self.ec.det_comprador_tipo('first time taking it'), {'nuevo'})
        self.assertEqual(self.ec.det_comprador_tipo('ok'), {'no_lo_dice'})
        self.assertEqual(self.ec.det_comprador_para('I bought this as a gift for my mom'), {'para_otra_persona'})
        self.assertEqual(self.ec.det_comprador_para('I take it every morning'), {'para_si_mismo'})
        self.assertEqual(self.ec.det_comprador_para('Great'), {'no_lo_dice'})

    def test_resultado_y_objecion(self):
        self.assertEqual(self.ec.det_resultado('It works great'), {'mejora'})
        self.assertEqual(self.ec.det_resultado('did not work at all'), {'sin_efecto'})   # 'work' no cuenta como mejora si esta negado
        self.assertEqual(self.ec.det_objecion('love it'), {'ninguna'})
        self.assertTrue({'envase_plastico_vidrio', 'sabor'} <= self.ec.det_objecion('It arrived leaking, nasty taste'))

    def test_razon_positiva_no_cuenta_recomendacion_negada(self):
        self.assertIn('recomienda_recompra', self.ec.det_razon_positiva('highly recommend'))
        self.assertEqual(self.ec.det_razon_positiva('I do not recommend'), {'ninguna'})

    def test_motivo_genero_region(self):
        self.assertTrue({'estrenimiento', 'hinchazon_gases'} <= self.ec.det_motivo('helped my constipation and bloating'))
        self.assertEqual(self.ec.det_genero('As a mom I love it'), {'mujer'})
        self.assertEqual(self.ec.det_region('I live in Texas'), {'sur'})
        self.assertEqual(self.ec.det_region('hi'), {'no_se_menciona'})


class AcuerdoYFrecuenciasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ec = load('etiquetar_corpus')

    def test_parsear_manual(self):
        self.assertIsNone(self.ec.parsear_manual(None))
        self.assertIsNone(self.ec.parsear_manual('  '))
        self.assertEqual(self.ec.parsear_manual('No lo dice'), {'no_lo_dice'})
        self.assertEqual(self.ec.parsear_manual('mejora|efecto_adverso'), {'mejora', 'efecto_adverso'})

    def test_acuerdo_a_mano(self):
        # 3 filas con recompra manual: 1) si/detecta si  2) si/no lo detecta  3) no_lo_dice/detecta si (falso positivo); 4) fila sin etiqueta: no cuenta
        hoja = [{'titulo': 't', 'texto': 'I will reorder', 'recompra': 'Si'},
                {'titulo': 't', 'texto': 'good stuff', 'recompra': 'Si'},
                {'titulo': 't', 'texto': 'I will reorder', 'recompra': 'No lo dice'},
                {'titulo': 't', 'texto': 'I will reorder', 'recompra': None}]
        r = self.ec.acuerdo(hoja)['recompra']
        self.assertEqual(r['n'], 3)
        si = r['etiquetas']['si']
        self.assertEqual((si['vp'], si['fp'], si['fn']), (1, 1, 1))
        self.assertAlmostEqual(si['precision'], 0.5); self.assertAlmostEqual(si['sensibilidad'], 0.5)
        self.assertAlmostEqual(r['exacta'], 1 / 3)                 # solo la fila 1 coincide exacto
        self.assertNotIn('genero', self.ec.acuerdo(hoja))          # campos sin ninguna etiqueta manual se omiten

    def test_frecuencias_cuentan_por_base_semestre_y_grupo(self):
        base = {'sentimiento_lexico': 'Positivo', 'sentimiento_knn': 'Positivo', **{c: 'no_lo_dice' for c in self.ec.DETECTORES}}
        filas = [{**base, 'base': 'bundle', 'semestre': '2025-S1', 'estrellas': 5, 'recompra': 'si'},
                 {**base, 'base': 'soursop', 'semestre': '2025-S1', 'estrellas': 1, 'recompra': 'no'},
                 {**base, 'base': 'soursop', 'semestre': '2025-S2', 'estrellas': 5, 'recompra': 'si'}]
        tabla = {(b, s, g, c, v): n for b, s, g, c, v, n, _ in self.ec.frecuencias(filas)}
        self.assertEqual(tabla[('todas', 'todos', 'todas', 'n_resenas', '')], 3)
        self.assertEqual(tabla[('todas', 'todos', 'todas', 'recompra', 'si')], 2)
        self.assertEqual(tabla[('soursop', 'todos', '4-5', 'recompra', 'si')], 1)
        self.assertEqual(tabla[('soursop', '2025-S1', '1-2', 'recompra', 'no')], 1)

    def test_etiquetar_todo_el_corpus(self):
        corpus = load('corpus_resenas').cargar_todo()
        filas, k = self.ec.etiquetar(corpus)
        self.assertEqual(len(filas), len(corpus))
        self.assertIn(k, self.ec.ac.KS)
        for f in filas[:50] + filas[-50:]:
            self.assertIn(f['sentimiento_lexico'], {'Positivo', 'Negativo', 'Neutro'})
            self.assertTrue(0 <= f['prob_positiva_knn'] <= 1)
            for campo in self.ec.DETECTORES:
                self.assertTrue(f[campo])                          # nunca vacio: siempre 'ninguna' / 'no_lo_dice' o una etiqueta
        with tempfile.TemporaryDirectory() as d:                   # el resumen se escribe sin tocar data/
            (Path(d) / 'r.md').write_text(self.ec.resumen_md(filas, k), encoding='utf-8')
            self.assertIn('## recompra', (Path(d) / 'r.md').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
