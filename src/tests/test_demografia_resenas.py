"""Casos limite de genero y regiones, con fuentes y evidencia verificables."""
import importlib.util
from pathlib import Path
import sys
import unittest

TOOLS=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,TOOLS/(name+'.py'))
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod)
    return mod

class DemografiaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.demo=load('demografia_resenas').Demografia(load('resenas_amazon_excel'))

    def test_nombre_apodo_inicial_unisex(self):
        self.assertEqual(self.demo.genero('Bob Smith','')['genero'],'Hombre')
        self.assertEqual(self.demo.genero('J. Smith','')['genero'],'No claro')
        self.assertEqual(self.demo.genero('Taylor Jones','')['genero'],'unisex')
        self.assertEqual(self.demo.genero('Dr. Mary Smith','')['confianza'],'media')

    def test_texto_gana_y_confianza(self):
        result=self.demo.genero('John Smith',"I'm a woman and this helped")
        self.assertEqual((result['genero'],result['confianza'],result['conflicto']),('Mujer','alta',True))
        result=self.demo.genero('Mary','My husband loves it')
        self.assertEqual((result['genero'],result['confianza']),('Mujer','alta'))
        result=self.demo.genero('Mary','My wife loves it')
        self.assertEqual((result['genero'],result['confianza']),('Hombre','baja'))

    def test_audiencia_no_es_genero(self):
        self.assertEqual(self.demo.genero('J.','Ladies, try it. Yes sir!')['genero'],'No claro')
        self.assertEqual(self.demo.genero('John','As a mom I like it')['confianza'],'alta')
        self.assertEqual(self.demo.genero('Mary',"I am a woman. I am a man.")['genero'],'No claro')

    def test_abreviaturas(self):
        self.assertFalse(self.demo.zona('IN OR ME OK HI. Works, OK! I put it IN my drink.')['menciones'])
        for ab,state in [('IN','Indiana'),('OR','Oregon'),('ME','Maine'),('OK','Oklahoma'),('HI','Hawaii')]:
            hits=self.demo.zona('I live in '+ab+'.')['menciones']
            self.assertEqual(hits[0]['estado'],state)
        self.assertEqual(self.demo.zona('Portland, OR 97201')['menciones'][0]['estado'],'Oregon')

    def test_geografia_evidencia_division(self):
        result=self.demo.zona('Back home in Texas, I liked it.')['menciones'][0]
        self.assertEqual((result['estado'],result['region'],result['division']),('Texas','Sur','Oeste Sur Central'))
        self.assertIn('Back home in Texas',result['evidencia'])
        self.assertEqual(self.demo.zona('I live in the Bay Area')['menciones'][0]['estado'],'California')
        self.assertFalse(self.demo.zona('I live in Portland')['menciones'])

    def test_regiones_ambiguas_culturales(self):
        r=self.demo.zona("I'm Jamaican, now in the Midwest. Tri-state is different.")
        self.assertEqual(r['cultural'][0]['tipo'],'autorreferencia')
        self.assertEqual(r['menciones'][0]['region'],'Medio Oeste')
        self.assertEqual(r['menciones'][1]['region'],'')
        self.assertEqual(self.demo.zona("I'm excited to try Jamaican herbs")['cultural'][0]['tipo'],'mencion_cultural')
        self.assertEqual(self.demo.zona('I am from the Caribbean')['cultural'][0]['tipo'],'autorreferencia')
        self.assertFalse(self.demo.zona('Jamaica and Caribbean herbs')['menciones'])
        self.assertEqual(self.demo.zona('Jamaica and Caribbean herbs')['cultural'][0]['tipo'],'mencion_cultural')

    def test_censo_cobertura(self):
        self.assertEqual(len(self.demo.states),51)
        self.assertEqual(len({d for _,d in self.demo.states.values()}),9)
        self.assertEqual(len({r for r,_ in self.demo.states.values()}),4)

if __name__=='__main__':unittest.main()
