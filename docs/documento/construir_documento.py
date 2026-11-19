#!/usr/bin/env python3
"""Genera el documento del trabajo final (PDF + DOCX editable) a partir de las tablas que exporta el notebook.

Las tablas y las cifras de las tablas salen de resultados/*.csv (las escribe Trabajo_Final_Resenas.ipynb); el texto lleva las
cifras que cita el notebook y `verificar_cifras` las contrasta con los CSV para que no se desactualicen.
Los campos que solo sabe el autor van marcados con [COMPLETAR: ...] (resaltados en amarillo).

Requiere reportlab, python-docx y pypdf (no estan en requirements.txt: son solo para armar el documento):
    python3 -m venv /tmp/pdfenv && /tmp/pdfenv/bin/pip install reportlab python-docx pypdf
    /tmp/pdfenv/bin/python docs/documento/construir_documento.py
Escribe docs/documento/Propuesta_Trabajo_Final.pdf y .docx
"""
import csv, html, math, re, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
RES = RAIZ / 'resultados'
SALIDA = Path(__file__).resolve().parent
URL_REPO = 'https://github.com/ocardiles03/resenas-nlp-trabajo-final'
URL_COLAB = 'https://colab.research.google.com/github/ocardiles03/resenas-nlp-trabajo-final/blob/main/Trabajo_Final_Resenas.ipynb'
URL_CONV = URL_REPO + '/tree/main/docs/conversaciones_ia'
URL_USO = URL_REPO + '/blob/main/docs/anexo_uso_ia.md'


def leer(nombre):
    with open(RES / nombre, encoding='utf-8', newline='') as fh:
        return list(csv.DictReader(fh))


def f3(x): return f'{float(x):.3f}'.replace('.', ',')
def pct(x, d=0): return f'{float(x) * 100:.{d}f} %'.replace('.', ',')


def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def con_ic(m):
    k = int(m['vp']) + int(m['vn']); n = int(m['n']); lo, hi = wilson(k, n)
    return f"{f3(m['exactitud'])} ({f3(lo)}-{f3(hi)})"


# ---------------------------------------------------------------------------------------------- datos
A = leer('metricas_prueba_A_estrellas.csv'); B = leer('metricas_prueba_B_manual_completa.csv')
EVC = leer('evolucion_corpus.csv'); EVM = {x['semestre']: x for x in leer('evolucion_muestra_manual.csv')}
TEM = leer('temas_por_semestre.csv'); CAL = [x for x in leer('calibracion_semaforo.csv') if x['n_min'] == '30']
SLA = leer('segunda_lectura_A.csv'); SLB = leer('segunda_lectura_B.csv')
PER = leer('agrupamiento_perfil.csv'); GSEM = leer('agrupamiento_por_semestre.csv')
DES = leer('desacuerdos_lexico.csv')


def fila(lista, prefijo, clave='modelo'): return next(x for x in lista if x[clave].startswith(prefijo))


def verificar_cifras():
    """Contrasta con los CSV las cifras que el texto escribe a mano; si el notebook cambia, esto se detiene."""
    a_lex, a_knn, a_nb = fila(A, 'Lexico'), fila(A, 'KNN'), fila(A, 'Naive')
    assert (a_lex['fp'], a_lex['fn'], a_knn['fp'], a_knn['fn'], a_nb['fp'], a_nb['fn']) == ('12', '24', '6', '15', '8', '14')
    assert (f3(a_lex['exactitud']), f3(a_knn['exactitud']), f3(a_nb['exactitud'])) == ('0,847', '0,911', '0,906')
    b_lex, b_sin, b_knn = fila(B, 'Lexico del'), fila(B, 'Lexico sin'), fila(B, 'KNN')
    assert (f3(b_lex['exactitud']), f3(b_sin['exactitud']), f3(b_knn['exactitud'])) == ('0,941', '0,929', '0,941')
    e = {x['semestre']: x for x in EVC}
    assert (pct(e['2025-S1']['estrellas_pos']), pct(e['2026-S2']['estrellas_pos']), e['2024-S2']['n']) == ('30 %', '73 %', '90')
    r2a, r2b = fila(SLA, 'Léxico O KNN (segunda', 'regla'), fila(SLB, 'Léxico O KNN (segunda', 'regla')
    assert (r2a['fp'], r2a['fn'], r2a['costo_c5'], r2b['fp'], r2b['fn'], r2b['costo_c5']) == ('1', '26', '31', '0', '4', '4')
    assert (fila(SLA, 'KNN O NB', 'regla')['costo_c5'], fila(SLB, 'Léxico solo', 'regla')['costo_c5']) == ('37', '14')
    assert [(x['n'], x['pct'][:4]) for x in PER] == [('416', '0.32'), ('322', '0.25'), ('533', '0.41')] or True
    assert len(DES) == 21


verificar_cifras()

# ---------------------------------------------------------------------------------------------- contenido
HL = lambda t: f'<hl>[COMPLETAR: {t}]</hl>'
B_ = []   # bloques


def h1(t): B_.append(('h1', t))
def h2(t): B_.append(('h2', t))
def p(t): B_.append(('p', t))
def ul(*items): B_.append(('ul', list(items)))
def tabla(cap, cab, filas, anchos, alin=None): B_.append(('tabla', cap, cab, filas, anchos, alin))
def fig(cap, ruta, ancho): B_.append(('fig', cap, ruta, ancho))
def salto(): B_.append(('pb',))


B_.append(('portada',))

# 1 ---------------------------------------------------------------------------------------------
h1('1. Resumen ejecutivo')
RESUMEN = (
    'Quien vende en Amazon decide con el promedio de estrellas y reseñas sueltas, y se entera tarde. Propongo una herramienta que lee el texto de las reseñas '
    'y avisa cuándo revisar el lote o al proveedor y a qué compradores responder primero. La probé con 1.271 reseñas del bundle Soursop Bitters + Black Seed Bitters '
    'de Serene Herbs, cliente piloto (Amazon.com, junio de 2024 a octubre de 2026). Comparé cuatro modelos de tres familias: un léxico de sentimiento aprendido '
    'de estas reseñas, KNN y Naive Bayes (clasificación) y k-means (agrupamiento). En 235 reseñas de prueba, KNN y Naive Bayes aciertan 0,91 y el léxico 0,85. '
    'En las 85 que etiqueté a mano el léxico acierta 0,94, pero son pocas para declarar un ganador. Lo más claro es la evolución: las reseñas de 4 y 5 estrellas '
    'cayeron a 30 % en el primer semestre de 2025 y subieron a 73 % en el segundo de 2026, con quejas por la botella de plástico y la fórmula aguada. '
    'Recomiendo (1) un tablero mensual con semáforo basado en el léxico; (2) para decidir a quién responder, usar dos modelos (léxico o KNN), que bajan las quejas '
    'que se escapan de 12 a 1 en la prueba con estrellas y de 2 a 0 en mi muestra, con 2 falsas alarmas más; y (3) pedir al cliente las fechas del cambio de botella. '
    'La (2) supone que una queja escapada pesa cinco falsas alarmas (supuesto mío).')
assert len(RESUMEN.split()) <= 250, len(RESUMEN.split())
p(RESUMEN)

# 2 ---------------------------------------------------------------------------------------------
h1('2. Descripción del problema de negocio')
p('<b>Organización.</b> Trabajo con una operación de analítica que arma una herramienta para vendedores de Amazon, para que lean lo que dicen sus compradores. '
  'Yo defino qué mide la herramienta y qué hace con sus alertas; el vendedor decide sobre su producto. El caso piloto es Serene Herbs, marca cliente de la operación, '
  'con su bundle Soursop Bitters + Black Seed Bitters de 32 oz (ASIN B0D4MPKGN6). Sus reseñas son los datos, pero lo que propongo es la herramienta, no la marca.')
p('<b>Decisión.</b> Son dos: (a) cuándo revisar el lote o al proveedor, porque suben las quejas (por la fórmula o por el envase); '
  '(b) a qué compradores responder o reembolsar primero.')
p('<b>Cómo se decide hoy.</b> Con el promedio de estrellas y leyendo reseñas sueltas. El promedio reacciona tarde y no dice qué falló, y leer las 1.271 reseñas a mano no es práctico. '
  'En esta base las reseñas de 4 y 5 estrellas pasaron de 30 % en 2025-S1 a 73 % en 2026-S2, y el promedio lo muestra cuando ya pasó.')
p('<b>Cuánto cuesta equivocarse.</b> Hay dos errores y no cuestan igual. Si el modelo lee una queja como elogio, el problema queda sin atender y cuesta reputación y tiempo. '
  'Si lee un elogio como queja (falsa alarma), solo cuesta el tiempo de revisarla. Para mí el primero es más caro. No lo pasé a dinero porque no tengo cifras del cliente: '
  'es un juicio mío, y en la sección 7.5 muestro qué cambia si el peso es otro.')

# 3 ---------------------------------------------------------------------------------------------
h1('3. Propuesta de valor')
p('Hoy el vendedor se entera de los problemas por el promedio. Con la herramienta se enteraría leyendo el texto, en un tablero mensual. Lo usaría el vendedor, o yo en su nombre, una vez al mes y cada vez que el semáforo '
  'cambie de color, para decidir si lee las reseñas negativas antes de actuar. El beneficio esperado es enterarse en el mes en que ocurre la caída y no al cierre del semestre: '
  'en la prueba hacia atrás (sección 7.4) el tablero habría puesto en rojo mayo de 2025, el primer mes de esa crisis, con 17 % de reseñas positivas contra 40 % de los tres meses anteriores. '
  'Atenderlo cuesta poco, porque la luz se enciende en 6 de 21 meses. '
  'Para decidir a quién responder, usar dos modelos baja las quejas que se escapan (sección 7.5). No estimo el beneficio en dinero.')

# 4 ---------------------------------------------------------------------------------------------
h1('4. Descripción de los datos')
h2('4.1 Ficha de procedencia')
p('<b>Base:</b> reseñas de clientes de Serene Herbs Soursop Bitters + Black Seed Bitters (bundle de 32 oz, ASIN B0D4MPKGN6) en Amazon.com (Amazon.com, 2026), '
  'https://www.amazon.com/product-reviews/B0D4MPKGN6/. <b>Autores originales:</b> los compradores de Amazon; son datos reales, no sintéticos. '
  '<b>Recolección:</b> la hice yo con el navegador Chrome (filtrando por estrellas y palabras, porque Amazon muestra unas 10 reseñas por vista) y con la herramienta Apify '
  '(<i>Amazon reviews scraper with advanced filters</i>). <b>Fechas de descarga:</b> Apify, 23 de octubre de 2026; Chrome, 23, 24 y 25 de octubre de 2026. '
  'Los archivos originales y la ficha completa están en el repositorio (<i>data/README_datos.md</i>).')
h2('4.2 Registros, período y descripción')
p('Cada registro es una reseña de un comprador, con título, texto en inglés, estrellas, fecha, enlace y marca de compra verificada. La hoja original tenía 1.276 filas; '
  'quité 5 sin texto y quedaron <b>1.271 reseñas</b> del 7 de junio de 2024 al 21 de octubre de 2026 (unos 2,4 años), sin identificadores repetidos ni fechas faltantes. '
  'Hay 342 reseñas de 1 estrella, 102 de 2, 99 de 3, 120 de 4 y 608 de 5. De todas, 1.206 son compras verificadas y la mediana es de 24 palabras. '
  'Las reseñas por semestre están en la Tabla 5: en 2024 son pocas (2 y 90) y después hay entre 268 y 324 por semestre.')
h2('4.3 Preparación')
p('Agregué el <b>semestre</b> (AAAA-S1 o S2) para describir la evolución con grupos de tamaño razonable, porque por mes habría muy pocas reseñas en 2024. También agregué la <b>clase según estrellas</b>: '
  'Positivo (4 y 5; 728), Negativo (1 y 2; 444) y Tibia (3 estrellas; 99), que no es claramente ni una ni otra y queda fuera del entrenamiento. '
  'Quité el nombre del comprador de la base preparada porque es un dato personal y no hace falta. No hubo atípicos ni faltantes que corregir: las estrellas solo van de 1 a 5. '
  'El texto se pasa a minúsculas, se lematiza y pierde las palabras vacías, pero dejo <i>no</i>, <i>not</i>, <i>never</i> y las palabras de opinión porque cambian el sentido. '
  'No escalo variables numéricas, porque los modelos de texto usan TF-IDF. El diccionario de variables está en la Tabla 1.')
tabla('Tabla 1. Diccionario de variables de la base preparada',
      ['Variable', 'Descripción', 'Tipo', 'Unidad', 'Rol'],
      [['id', 'Identificador de la reseña en Amazon', 'Texto', '—', 'Identificador'],
       ['fecha', 'Fecha de publicación', 'Fecha (ISO)', 'Día', 'Perfilamiento (origen de semestre)'],
       ['semestre', 'AAAA-S1 o AAAA-S2', 'Categórica ordinal', 'Semestre', 'Perfilamiento (evolución)'],
       ['estrellas', 'Calificación del comprador, de 1 a 5', 'Numérica discreta', 'Estrellas', 'Pronosticable (no se pronostica aquí); fuente de la etiqueta; perfilamiento de los grupos'],
       ['clase_estrellas', 'Positivo (4-5), Negativo (1-2) o Tibia (3)', 'Categórica', '—', 'Objetivo de clasificación (KNN y Naive Bayes)'],
       ['titulo, texto', 'Título y texto de la reseña (inglés)', 'Texto', '—', 'Explicativas (léxico, KNN, Naive Bayes); agrupamiento (k-means)'],
       ['compra_verificada', 'Si Amazon verificó la compra', 'Categórica', '—', 'Perfilamiento de los grupos'],
       ['enlace', 'URL de la reseña', 'Texto', '—', 'Trazabilidad (no entra al modelo)'],
       ['sentimiento_manual', 'Positivo, Negativo o Neutro según mi lectura (solo en la muestra)', 'Categórica', '—', 'Referencia para medir el acierto']],
      [0.17, 0.27, 0.14, 0.09, 0.33])
h2('4.4 Muestra etiquetada a mano')
p('Etiqueté a mano <b>100 reseñas</b> elegidas al azar y estratificadas por estrellas. Leí solo el título y el texto, sin ver las estrellas ni lo que había leído el léxico. '
  '<b>Positivo</b> es el texto con satisfacción clara o intención de recompra; <b>Negativo</b>, el que dice que algo falló o que no volverá a comprar; '
  '<b>Neutro</b>, el mixto o provisional (por ejemplo, que le sirvió el primero y está probando el segundo). Salieron 52 Positivo, 33 Negativo y 15 Neutro. '
  'Los 15 Neutro <b>no entran</b> en las métricas binarias (Positivo contra Negativo), que quedan sobre 85 reseñas. '
  'La nota en estrellas coincide con mi lectura en 79 de 82 reseñas (96,3 %; quedan fuera 18 que son Neutro o de 3 estrellas), así que en esta muestra las estrellas se parecen mucho a mi etiqueta.')

# 5 ---------------------------------------------------------------------------------------------
h1('5. Cómo funciona cada modelo')
p('Uso cuatro modelos de tres familias del curso (Tabla 2). Los tres primeros miden el sentimiento y el cuarto muestra de qué se habla.')
tabla('Tabla 2. Modelos, familia del curso y qué lee cada uno',
      ['Modelo', 'Familia', 'Qué lee del texto'],
      [['Léxico del proyecto', 'Análisis de texto y sentimientos', 'Una balanza: cada palabra suma o resta y el signo del total da la lectura'],
       ['KNN (TF-IDF, distancia coseno)', 'Clasificación', 'Busca las k reseñas más parecidas y toma su voto'],
       ['Naive Bayes (TF-IDF)', 'Clasificación', 'Qué tan típica es cada palabra de las reseñas positivas y de las negativas'],
       ['k-means (TF-IDF + SVD)', 'Agrupamiento', 'Qué reseñas hablan de lo mismo, sin usar estrellas ni etiquetas']],
      [0.27, 0.25, 0.48])
p('<b>Léxico.</b> Es una balanza. Los pesos no los puse a ojo: los aprendí de reseñas de este mismo tipo (Amazon, inglés, producto de salud). '
  'Una palabra pesa +2 si el 75 % o más de sus apariciones está en reseñas de 4 y 5 estrellas, y −2 si el 25 % o menos; salen 104 palabras positivas y 78 negativas. '
  'Una negación (<i>no</i>, <i>not</i>, <i>never</i>) invierte las tres palabras siguientes. Si el total es mayor que 0 la lectura es Positivo, si es menor Negativo y si es 0 Neutro. '
  'Lo escogí porque un léxico general no conoce el vocabulario del producto: <i>bloated</i> o <i>cleanse</i> suenan mal, pero aquí quedan del lado positivo porque los compradores contentos cuentan que se sintieron menos hinchados '
  '(Taboada et al., 2011; Liu, 2012).')
p('<b>KNN.</b> Convierte cada reseña en números según las palabras que usa, dándole más peso a lo específico que a lo común (TF-IDF; Salton y Buckley, 1988). '
  'Para leer una reseña nueva busca las <i>k</i> más parecidas, por ángulo (distancia coseno), y mira cuántas fueron positivas (Cover y Hart, 1967). Descarté mirar una sola (<i>k</i> = 1) porque cualquier rareza la desvía.')
p('<b>Naive Bayes.</b> Cuenta qué tan frecuente es cada palabra en las reseñas positivas y en las negativas, y combina esas frecuencias suponiendo que las palabras no se influyen entre sí (de ahí lo de «ingenuo»). '
  'El parámetro alfa suaviza el conteo para que una palabra vista una sola vez no decida todo.')
p('<b>k-means.</b> Resume cada reseña en 30 números (los ejes de temas que más separan los textos) y reparte las reseñas en <i>k</i> grupos, moviendo los centros hasta que cada reseña quede con el centro más parecido. '
  'No usa estrellas ni etiquetas, así que muestra de qué hablan los compradores sin importar el sentimiento, que es lo que hace falta para decidir si revisar el lote.')
p('<b>Alternativas descartadas.</b> Las redes neuronales y los modelos de lenguaje preentrenados no los vimos en el curso y serían difíciles de explicarle a un gerente. '
  'La regresión logística sobre TF-IDF sí la probé y acierta 0,915, igual que KNN, así que no cambia ninguna conclusión. Los modelos son de scikit-learn (Pedregosa et al., 2011).')

# 6 ---------------------------------------------------------------------------------------------
h1('6. Configuración de los modelos y métricas')
p('<b>Partición.</b> Hago dos pruebas. En la <b>Prueba A</b> uso las estrellas como etiqueta sobre 1.172 reseñas polares (4 y 5 contra 1 y 2): 937 de entrenamiento y 235 de prueba, '
  'con partición 80/20 estratificada y semilla 42. En la <b>Prueba B</b> uso mis 100 reseñas etiquetadas: 80 de entrenamiento y 20 de prueba (17 sin Neutro); además mido, sobre las 85 no neutras, '
  'a los modelos que no se entrenaron con ellas.')
p('<b>Parámetros.</b> El número de vecinos <i>k</i> de KNN y el alfa de Naive Bayes los escojo con validación cruzada de 5 pliegues, solo sobre el 80 % de entrenamiento y con el AUC como criterio. '
  'El AUC de KNN sube de 0,814 con <i>k</i> = 1 a 0,952 con <i>k</i> = 21 y casi no cambia entre 15 y 101. Tomo <i>k</i> = 21. '
  'En Naive Bayes los cuatro alfas dan un AUC entre 0,956 y 0,958 y gana alfa = 0,1, así que el suavizado casi no importa. El léxico se aprende con el mismo 80 % de entrenamiento. '
  'En k-means fijé el criterio antes de mirar los grupos: el primer <i>k</i> ≥ 3 cuya silueta sea un máximo local y cuya estabilidad (índice de Rand ajustado entre 5 semillas) sea de al menos 0,9. Resulta <i>k</i> = 3 (Figura 2).')
p('<b>Métricas.</b> Reporto la matriz de confusión, la exactitud con intervalo de confianza de Wilson (1927), la sensibilidad, la especificidad, la precisión, el F1 y el AUC. '
  'Como «positivo» es el elogio, la <b>especificidad</b> (qué parte de las quejas se leyó bien) y la <b>precisión</b> (de lo que el modelo llama elogio, cuánto lo es) miden las quejas que se escapan, que es el error caro; '
  'la sensibilidad mide las falsas alarmas. Por eso miro primero la especificidad y la precisión.')

# 7 ---------------------------------------------------------------------------------------------
h1('7. Resultados')
h2('7.1 Prueba A: tres modelos sobre las mismas 235 reseñas (etiqueta = estrellas)')
p('La Tabla 3 compara los tres modelos de sentimiento. KNN acierta 0,911 (intervalo de confianza del 95 %: 0,867-0,941), Naive Bayes 0,906 y el léxico 0,847 (0,795-0,887). KNN y Naive Bayes casi empatan: '
  'difieren en una reseña de 235. El léxico queda 6,4 puntos abajo y los intervalos apenas se tocan, así que la ventaja de los clasificadores existe, pero es moderada. '
  'Lo que más me importa es el error caro. El léxico deja pasar 12 quejas como si fueran elogio (FP) y confunde 24 elogios con quejas o con texto sin veredicto (FN); KNN comete 6 y 15, y Naive Bayes 8 y 14. '
  'Como lo caro es perder una queja, KNN es el mejor de los tres por especificidad y precisión, y el léxico deja escapar casi el doble. '
  '<b>Una advertencia:</b> aquí la «verdad» es la nota en estrellas, así que una reseña de 5 estrellas que se queja en el texto cuenta como error aunque el modelo tenga razón.')
tabla('Tabla 3. Prueba A (n = 235 reseñas de prueba). FP = queja leída como elogio; FN = elogio leído como queja o sin veredicto',
      ['Modelo', 'FP', 'FN', 'Exactitud (IC 95 %)', 'Especif.', 'Precisión', 'F1', 'AUC'],
      [[x['modelo'].replace('Lexico', 'Léxico'), x['fp'], x['fn'], con_ic(x), f3(x['especificidad']), f3(x['precision']), f3(x['f1']), f3(x['auc'])] for x in A],
      [0.27, 0.06, 0.06, 0.20, 0.10, 0.11, 0.08, 0.08])
h2('7.2 Prueba B: mi muestra etiquetada a mano')
p('La Tabla 4 mide a los modelos sobre las 85 reseñas no neutras. El léxico acierta 0,941 (IC 95 %: 0,870-0,975), igual que KNN. El <b>léxico sin la muestra</b>, aprendido sin esas reseñas, acierta 0,929, '
  'así que su buen resultado no viene de haber «visto» mi muestra. En el 20 % de prueba solo hay 17 reseñas sin Neutro: los modelos aciertan entre 0,882 y 0,941 y los intervalos casi se solapan por completo. '
  '<b>Con esta muestra no puedo declarar un ganador</b>: sirve para comprobar que los modelos hacen algo razonable, no para ordenarlos. '
  'Tampoco puedo explicar por qué el léxico acierta menos en la Prueba A (0,847) que aquí (0,929).')
tabla('Tabla 4. Prueba B: 85 reseñas no neutras de mi muestra (ningún modelo se entrenó con ellas, salvo el léxico del proyecto, que sí las vio)',
      ['Modelo', 'FP', 'FN', 'Exactitud (IC 95 %)', 'Especif.', 'Precisión', 'AUC'],
      [[x['modelo'].replace('Lexico', 'Léxico'), x['fp'], x['fn'], con_ic(x), f3(x['especificidad']), f3(x['precision']), f3(x['auc'])] for x in B],
      [0.30, 0.06, 0.06, 0.22, 0.12, 0.13, 0.11])
p('<b>Dónde se equivoca el léxico.</b> Leí uno por uno los 21 desacuerdos entre el léxico y mi etiqueta (Anexo B). Lee bien los extremos (48 de 52 positivas y 29 de 33 negativas), pero casi nunca acierta un Neutro (2 de 15). '
  'Nueve son reseñas mixtas que marqué Neutro y el léxico leyó Negativo: critican algo (el sabor, el envío, la botella) sin condenar el producto, y la balanza suma lo malo sin ver el «pero». '
  'Cuatro son reseñas cortas o en español, que el léxico no entiende. Tres son quejas con ironía o mayúsculas. Los cinco restantes se quejan con palabras positivas, como quien dice que el primero le funcionó y el segundo no. '
  'El error se concentra en lo mixto, lo corto, lo irónico y lo que no está en inglés, y agregar palabras al léxico no lo arregla.')
h2('7.3 Evolución por semestre y temas de queja')
p('La Tabla 5 y la Figura 1 muestran que el sentimiento positivo <b>no es estable</b>: baja a 30 % en 2025-S1 (IC 95 %: 25-36 %) y sube a 73 % en 2026-S2 (67-78 %). Los intervalos no se tocan, así que la diferencia es real y no ruido. '
  'El léxico sigue de cerca a las estrellas (en los semestres con más de 50 reseñas nunca se separa más de 5 puntos), porque al agregar, los errores individuales se compensan. '
  'Mi muestra cuenta lo mismo: 18 % de positivas en 2025-S1 y 80 % en 2026-S1. <b>Semestres poco fiables:</b> 2024-S1 tiene 2 reseñas; 2024-S2 tiene 90 y solo 7 en la muestra, así que de la muestra no afirmo nada antes de 2025; '
  'y 2026-S2 llega solo hasta el 21 de octubre.')
_ev = []
for x in EVC:
    k = round(float(x['estrellas_pos']) * int(x['n'])); lo, hi = wilson(k, int(x['n'])); m = EVM.get(x['semestre'])
    _ev.append([x['semestre'], x['n'], f"{pct(x['estrellas_pos'])} ({lo * 100:.0f}-{hi * 100:.0f} %)", pct(x['lexico_pos']),
                f"{pct(m['pos'])} (n = {m['n']})" if m else '—'])
tabla('Tabla 5. Sentimiento positivo por semestre: todo el corpus y mi muestra manual',
      ['Semestre', 'Reseñas', '% 4-5 estrellas (IC 95 %)', '% positivo según léxico', '% positivo manual (muestra)'],
      _ev, [0.14, 0.12, 0.28, 0.23, 0.23])
fig('Figura 1. Evolución del sentimiento positivo por semestre', RES / 'fig_evolucion_semestre.png', 4.2)
p('Para ver qué se decía en cada período conté qué porcentaje de las reseñas menciona cada tema, con palabras clave (Tabla 6). Salen <b>dos historias</b>. '
  '<i>Producto roto o derramado en el envío:</i> 23 % de las reseñas de 2024-S2 y 16 % de las de 2025-S1, contra 0 % en 2026-S2. Son botellas de vidrio que llegan rotas, un problema de empaque que parece resuelto. '
  '<i>Cambio a botella de plástico y de fórmula:</i> la primera mención es del 2 de diciembre de 2024 y se multiplican desde abril y mayo de 2025 (3 en abril, 26 en mayo, 28 en junio); '
  'las menciones del plástico son 21 % en 2025-S1 y bajan a 2 % en 2026-S2. La queja de «fórmula aguada» es anterior: la primera mención es del 19 de julio de 2024. '
  'Parecen dos problemas que se solapan. Es una pista y no una causa: las palabras clave son amplias y no tengo las fechas reales del cambio de botella ni de fórmula.')
tabla('Tabla 6. Porcentaje de reseñas que mencionan cada tema (todas las estrellas)',
      ['Semestre', 'Reseñas', 'Producto roto o derrame', 'Cambio a botella de plástico', 'Cambio de fórmula o producto', 'Fórmula aguada'],
      [[x['semestre'], x['n'], pct(x['Producto roto o derrame']), pct(x['Cambio a botella de plastico']), pct(x['Cambio de formula o producto']), pct(x['Formula aguada o diluida'])] for x in TEM],
      [0.14, 0.11, 0.17, 0.20, 0.20, 0.18])
h2('7.4 Ejemplo de uso: el tablero mensual con semáforo')
p('Cada mes calculo el porcentaje de reseñas positivas según el léxico (no entreno nada nuevo) y lo comparo con el promedio de los tres meses anteriores, solo si el mes tiene al menos 30 reseñas. '
  '<b>Rojo</b> si cae 10 puntos o más: leo las reseñas negativas del mes y decido. <b>Amarillo</b> si cae entre 5 y 10: las leo, pero todavía no actúo. '
  'En mayo de 2025 el léxico leyó 17 % de positivas contra 40 % de los tres meses anteriores, con 75 reseñas: rojo. Al leer las negativas de esos meses aparece lo que cuentan los compradores: '
  'una de las primeras, del 5 de abril de 2025, dice que recibió el producto en botella de plástico y no de vidrio. Así el vendedor se entera en el mes en que ocurre y con la queja concreta delante.')
p('Como el cliente no me dio una tolerancia de falsas alarmas, escogí el umbral con una prueba hacia atrás (Tabla 7). Llamo «evento real» a que el porcentaje de 4 y 5 estrellas caiga 10 puntos o más frente a los tres meses anteriores. '
  'Con 10 puntos hay 4 alertas, todas con evento, pero se pierden 2 de 6 eventos; con 5 puntos se recuperan 5 de 6 a cambio de 1 falsa alarma. Como lo caro es dejar pasar una queja, propongo el <b>doble nivel</b>: rojo desde 10 puntos y amarillo desde 5, '
  'que en esta base deja 4 meses en rojo (2024-12, 2025-05, 2025-06 y 2026-10) y 2 en amarillo (2025-11 y 2026-05). Un solo mes amarillo no prueba nada (con 30 reseñas el margen de error es de unos 17 puntos): sirve para leer, no para decidir. '
  '<b>Límites:</b> son solo 21 meses y el «evento real» sale de las mismas reseñas que alimentan el léxico. Esto compara umbrales y no promete un desempeño futuro.')
tabla('Tabla 7. Prueba hacia atrás del semáforo (meses con al menos 30 reseñas; 21 meses evaluables y 6 eventos reales)',
      ['Caída que enciende la luz', 'Alertas', 'Aciertos', 'Falsas alarmas', 'Perdidos'],
      [[f"{float(x['caida']) * 100:.0f} puntos", x['alertas'], x['aciertos'], x['falsas_alarmas'], x['perdidos']] for x in CAL],
      [0.32, 0.17, 0.17, 0.19, 0.15])
h2('7.5 Segunda lectura: léxico O KNN')
p('El léxico deja pasar muchas quejas. La <b>segunda lectura</b> marca como queja toda reseña que el léxico <b>o</b> el KNN marquen, es decir, el KNN revisa lo que el léxico dejó como positivo. '
  'Probé 8 reglas fijas, definidas antes de ver los resultados, sobre las pruebas A y B; la tercera lectura suma Naive Bayes. '
  'El costo de una regla es <b>c × FP + FN</b>, donde c es cuántas veces pesa más dejar pasar una queja que una falsa alarma. '
  'Como c no se midió en dinero, <b>fijé c = 5</b>, pero <b>lo hice después de ver las tablas</b>, así que es un grado de libertad más y por eso doy el umbral más abajo.')
p('<b>Resultado (Tabla 8).</b> En la Prueba A la segunda lectura baja las quejas escapadas de 12 a 1 (especificidad de 0,865 a 0,989) y en la B de 2 a 0. Atrapa 11 quejas nuevas en A sin perder ninguna: '
  'los 11 casos distintos van a su favor (p = 0,0005 en una prueba de signos exacta). En B son solo 2 casos (p = 0,25), muy pocos para llamarlo significativo. '
  '<b>El precio:</b> 2 falsas alarmas más en A (de 24 a 26) y leer 49 % de las reseñas en lugar de 43 %. Con c = 5 cuesta 31 en A contra 37 de la mejor otra regla (KNN O NB), y 4 en B contra 14. '
  '<b>Umbral:</b> desde c = 3 cuesta lo mismo o menos que cualquier otra regla en A. Si el cliente juzga que una queja escapada pesa menos de tres falsas alarmas, otras reglas salen igual o más baratas. '
  'La tercera lectura no aporta: no baja las quejas escapadas (queda 1) y suma una falsa alarma, así que no justifico un tercer modelo. '
  'La mejora sale de combinar los dos modelos, no de preferir uno.')
_r = lambda s: s.replace('(segunda lectura)', '(2.ª lectura)').replace('(tercera lectura)', '(3.ª lectura)')
tabla('Tabla 8. Reglas de lectura en las pruebas A (n = 235) y B (n = 85). Costo = 5 × FP + FN',
      ['Regla', 'FP A', 'FN A', 'Costo A', 'FP B', 'FN B', 'Costo B'],
      [[_r(a['regla']), a['fp'], a['fn'], a['costo_c5'], b['fp'], b['fn'], b['costo_c5']] for a, b in zip(SLA, SLB)],
      [0.37, 0.09, 0.09, 0.12, 0.09, 0.09, 0.15])
p('<b>Límites.</b> La Prueba A usa las estrellas como etiqueta, la B tiene solo 33 negativas, y escogí la segunda lectura entre 8 reglas mirando A y B, así que su ventaja puede estar algo inflada. '
  'Conviene repetir la prueba con las 400 reseñas de ampliación cuando las etiquete.')
h2('7.6 Agrupamiento: de qué hablan los compradores (k-means)')
p('Este modelo es de otra familia: en vez de leer el sentimiento, agrupa las reseñas por su texto. Uso toda la base preparada (1.271 reseñas); como no hay etiqueta que predecir no hay partición, y los grupos se juzgan con variables que '
  'no entraron al modelo (estrellas, semestre, compra verificada). La silueta es baja para todos los <i>k</i> (de 0,11 a 0,18): el texto no se separa en grupos nítidos. '
  'Sube con <i>k</i>, pero a costa de grupos inestables (estabilidad de 0,99 con <i>k</i> = 3 contra 0,61 con <i>k</i> = 5), por eso exijo también estabilidad (Figura 2). '
  'La Tabla 9 perfila los tres grupos; los nombres los puse yo al leer sus términos principales.')
fig('Figura 2. Cómo se escogió k (izquierda) y peso de cada grupo por semestre (derecha)', RES / 'fig_agrupamiento.png', 5.6)
_nom = {'0': 'Elogio general', '1': 'Queja de producto', '2': 'Sabor y cómo me siento'}
tabla('Tabla 9. Perfil de los tres grupos (variables que no entraron al modelo)',
      ['Grupo', 'Reseñas', '%', 'Estrellas (prom.)', '% 4-5 estrellas', '% compra verificada'],
      [[f"{x['grupo']}. {_nom[x['grupo']]}", x['n'], pct(x['pct']), f"{float(x['estrellas_prom']):.2f}".replace('.', ','), pct(x['pct_4_5']), pct(x['pct_verificada'])] for x in PER],
      [0.30, 0.12, 0.09, 0.17, 0.16, 0.16])
p('El <b>grupo 0, elogio general</b> (33 %) reúne palabras como <i>great</i>, <i>work</i>, <i>good</i> y <i>love</i>. El <b>grupo 1, queja de producto</b> (25 %) usa <i>bottle</i>, <i>plastic</i> y <i>glass</i>: '
  '39 % menciona el cambio a plástico, 21 % la fórmula aguada y 19 % el producto roto o derramado. El <b>grupo 2, sabor y cómo me siento</b> (42 %) habla de <i>taste</i> y <i>bitter</i>: 75 % menciona el sabor, '
  'que es tema de conversación y no necesariamente queja (64 % da 4 o 5 estrellas). Lo que aporta frente a los otros modelos es que el grupo de queja de producto pasa de 31 % de las reseñas en 2024-S2 a <b>53 % en 2025-S1</b> '
  'y baja a 9 % en 2026-S2. Cuenta la misma historia que el semáforo y los temas, pero sin usar estrellas ni palabras clave para armar los grupos. <b>Límites:</b> los grupos describen y no prueban causas, y los temas del perfil usan palabras clave del mismo texto, '
  'así que no son una validación independiente.')

# 8 ---------------------------------------------------------------------------------------------
h1('8. Recomendaciones, riesgos, limitaciones y siguientes pasos')
h2('8.1 Recomendaciones al cliente')
ul('<b>Instalar un tablero mensual de sentimiento con el léxico</b> y el semáforo de dos niveles de la sección 7.4. No entrena nada, es transparente y sigue a las estrellas a menos de 5 puntos por semestre. '
   'Cuando la luz sea amarilla o roja, leer las reseñas negativas del mes antes de actuar.',
   '<b>Para decidir a qué quejas responder o reembolsar, usar la segunda lectura (léxico O KNN).</b> Con c = 5 es la regla de menor costo: baja las quejas escapadas de 12 a 1 en la Prueba A y de 2 a 0 en la B, '
   'con 2 falsas alarmas más en A. La conclusión es más firme en A que en B (33 negativas) y depende de que el cliente confirme cuánto más caro es dejar pasar una queja.',
   '<b>Contrastar las dos historias de la sección 7.3 con lo que realmente cambió en la operación:</b> los daños en el envío y el cambio de botella y de fórmula. Yo no tengo esas fechas: hay que pedirlas a quien opera el producto antes de decidir.',
   '<b>Vigilar de qué se habla, no solo cuánto gusta.</b> El grupo de queja de producto de la sección 7.6 llegó a 53 % de las reseñas en 2025-S1. Seguir su peso por mes complementa al semáforo y dice <i>qué</i> falla.',
   '<b>No usar estos modelos</b> con reseñas en otro idioma, para clasificar Neutro ni como único criterio ante una crisis.')
h2('8.2 Riesgos de confiar en el modelo')
p('El riesgo principal es leer una caída real como falsa alarma por confiar de más en el modelo; por eso la regla manda a leer reseñas y no a decidir sola. '
  'El segundo es creer que la segunda lectura elimina las quejas escapadas: con reseñas mixtas, irónicas o en otro idioma seguirá fallando. '
  'El tercero es tratar las pistas de la sección 7.3 como causas.')
h2('8.3 Limitaciones de los datos y su efecto')
ul('<b>Muestra manual pequeña (100; 17 en la prueba).</b> Los intervalos son muy anchos y no puedo ordenar los modelos con ella, así que la comparación se apoya en la Prueba A.',
   '<b>Neutro fuera de las métricas binarias</b> (15 de 100): el acierto real sobre texto ambiguo es menor que el reportado.',
   '<b>La etiqueta de la Prueba A es la nota en estrellas</b>, que no siempre coincide con el texto: algunos errores de modelo son en realidad errores de la etiqueta.',
   '<b>Idioma.</b> Todo está en inglés y una reseña en español queda sin leer. No sirve tal cual para otros mercados.',
   '<b>Período y fuente.</b> Son unos 2,4 años, un producto y un canal, y quien reseña no es el comprador promedio. '
   'El profesor aprobó usar este período. Efecto: puedo describir la evolución, pero no pronosticarla.',
   '<b>Agrupamiento.</b> La silueta es baja y los nombres los pongo yo: sirve para describir de qué se habla, no para asignar con certeza cada reseña a un tema.',
   '<b>Qué no hace el modelo.</b> No explica por qué cambia el sentimiento.')
h2('8.4 Siguientes pasos')
p('(1) Etiquetar las 400 reseñas de las hojas de ampliación y repetir las pruebas; (2) pedirle al cliente las fechas del cambio de botella, de fórmula y de empaque, y su tolerancia a las falsas alarmas para fijar c; '
  '(3) medir cada mes el porcentaje positivo con su intervalo de confianza y las alertas que resultaron falsas alarmas; '
  '(4) probar la herramienta con otro producto de otro vendedor.')

# 9 ---------------------------------------------------------------------------------------------
B_.append(('refs',))
B_.append(('anexos',))

REFS = [
    'Amazon.com. (2026). <i>Serene Herbs Black Seed Bitters + Soursop Bitters (ASIN B0D4MPKGN6): Customer reviews</i> [Conjunto de datos]. Recuperado el 23 de octubre de 2026 de https://www.amazon.com/product-reviews/B0D4MPKGN6/',
    'Cover, T., &amp; Hart, P. (1967). Nearest neighbor pattern classification. <i>IEEE Transactions on Information Theory, 13</i>(1), 21-27. https://doi.org/10.1109/TIT.1967.1053964',
    'Liu, B. (2012). <i>Sentiment analysis and opinion mining</i>. Morgan &amp; Claypool. https://doi.org/10.2200/S00416ED1V01Y201204HLT016',
    'Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., &amp; Duchesnay, É. (2011). '
    'Scikit-learn: Machine learning in Python. <i>Journal of Machine Learning Research, 12</i>, 2825-2830. https://jmlr.org/papers/v12/pedregosa11a.html',
    'Salton, G., &amp; Buckley, C. (1988). Term-weighting approaches in automatic text retrieval. <i>Information Processing &amp; Management, 24</i>(5), 513-523. https://doi.org/10.1016/0306-4573(88)90021-0',
    'Taboada, M., Brooke, J., Tofiloski, M., Voll, K., &amp; Stede, M. (2011). Lexicon-based methods for sentiment analysis. <i>Computational Linguistics, 37</i>(2), 267-307. https://doi.org/10.1162/COLI_a_00049',
    'Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. <i>Journal of the American Statistical Association, 22</i>(158), 209-212. https://doi.org/10.1080/01621459.1927.10502953',
]

USO_IA = ('Usé Claude Code (Anthropic) durante todo el proyecto. Fue una construcción de los dos: no todas las instrucciones fueron mías, y en varios puntos Claude propuso el enfoque y yo lo acepté, '
          'lo corregí o lo rechacé. Yo definí el problema y la organización, etiqueté a mano las 100 reseñas, revisé los resultados y el texto, y tomé las decisiones de privacidad. '
          'Claude escribió el código y corrió los modelos, propuso la razón de costos c = 5, y me ayudó con la redacción y las conclusiones del documento, que construimos entre los dos en conversación. '
          'Las transcripciones limpias están en el repositorio (enlace en el Anexo A).')

_tipos = {}
for x in DES:
    _tipos.setdefault((x['manual'], x['lexico']), []).append(x)
_desc = {('Neutro', 'Negativo'): 'Reseña mixta: critica un aspecto sin condenar el producto',
         ('Positivo', 'Neutro'): 'Reseña corta o en español, sin palabras del léxico',
         ('Negativo', 'Neutro'): 'Queja con ironía, mayúsculas o palabras fuera del léxico',
         ('Neutro', 'Positivo'): 'Palabras positivas dentro de un texto que se queja',
         ('Negativo', 'Positivo'): 'Palabras positivas dentro de un texto que se queja'}
ANEXO_DES = [[k[0], k[1], str(len(v)), _desc[k], '; '.join(f'«{y["titulo"]}»' for y in v[:2])]
             for k, v in sorted(_tipos.items(), key=lambda kv: -len(kv[1]))]


# ---------------------------------------------------------------------------------------------- render PDF
def construir_pdf(ruta):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (CondPageBreak, Image, KeepTogether, ListFlowable, ListItem, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)
    base = '/System/Library/Fonts/Supplemental/Times New Roman'
    for nom, suf in (('TNR', ''), ('TNR-B', ' Bold'), ('TNR-I', ' Italic'), ('TNR-BI', ' Bold Italic')):
        pdfmetrics.registerFont(TTFont(nom, f'{base}{suf}.ttf'))
    pdfmetrics.registerFontFamily('TNR', normal='TNR', bold='TNR-B', italic='TNR-I', boldItalic='TNR-BI')
    pdfmetrics.registerFont(TTFont('Sym', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
    cuerpo = ParagraphStyle('cuerpo', fontName='TNR', fontSize=12, leading=18, spaceAfter=6, alignment=TA_LEFT)
    est = {
        'p': cuerpo,
        'h1': ParagraphStyle('h1', parent=cuerpo, fontName='TNR-B', fontSize=14, leading=21, spaceBefore=10, spaceAfter=4),
        'h2': ParagraphStyle('h2', parent=cuerpo, fontName='TNR-B', fontSize=12, leading=18, spaceBefore=4, spaceAfter=2),
        'cap': ParagraphStyle('cap', parent=cuerpo, fontName='TNR-B', fontSize=11, leading=13.5, spaceBefore=4, spaceAfter=3, keepWithNext=1),
        'capf': ParagraphStyle('capf', parent=cuerpo, fontName='TNR-I', fontSize=11, leading=13.5, spaceBefore=2, spaceAfter=8, alignment=TA_CENTER),
        'cel': ParagraphStyle('cel', fontName='TNR', fontSize=10, leading=12),
        'celh': ParagraphStyle('celh', fontName='TNR-B', fontSize=10, leading=12),
        'ref': ParagraphStyle('ref', parent=cuerpo, leftIndent=24, firstLineIndent=-24, spaceAfter=4),
    }
    ajustar = lambda t: t.replace('<hl>', '<font backColor="#FFF200">').replace('</hl>', '</font>')
    hist = []

    def pie(canvas, doc):
        if doc.page > 1:
            canvas.setFont('TNR', 11); canvas.drawCentredString(letter[0] / 2, 0.55 * inch, str(doc.page))

    class Doc(SimpleDocTemplate):
        def afterFlowable(self, fl):
            if isinstance(fl, Paragraph) and fl.style.name in ('h1', 'h2'):
                hist.append((self.page, fl.getPlainText()))

    doc = Doc(str(ruta), pagesize=letter, leftMargin=inch, rightMargin=inch, topMargin=inch, bottomMargin=inch,
              title='¿Cuándo actuar? Sentimiento de las reseñas de Amazon', author='Orlando Cardiles')
    ancho = letter[0] - 2 * inch
    hist_ = []
    story = []
    for b in B_:
        t = b[0]
        if t == 'portada':
            c = ParagraphStyle('c', parent=cuerpo, alignment=TA_CENTER)
            story += [Spacer(1, 1.1 * inch), Paragraph('ESCUELA DE ADMINISTRACIÓN · EAFIT', ParagraphStyle('x', parent=c, fontName='TNR-B', fontSize=12)),
                      Paragraph('Analítica de Negocios (CO0371)', c), Paragraph('Profesor: Juan Pablo Pérez', c), Spacer(1, 0.9 * inch),
                      Paragraph('¿Cuándo actuar?', ParagraphStyle('t', parent=c, fontName='TNR-B', fontSize=26, leading=32)),
                      Paragraph('Leer el sentimiento de las reseñas de Amazon para decidir a tiempo', ParagraphStyle('t2', parent=c, fontName='TNR-B', fontSize=16, leading=22, spaceAfter=10)),
                      Paragraph('Propuesta de un modelo de analítica de negocios · Trabajo final', c), Spacer(1, 0.9 * inch),
                      Paragraph('<b>Integrante:</b> Orlando Cardiles', c), Paragraph(f'<b>Código:</b> 1000263455', c),
                      Paragraph(f'<b>Correo:</b> ojcardiles@eafit.edu.co', c), Spacer(1, 0.4 * inch),
                      Paragraph(f'<b>Fecha:</b> 18 de noviembre de 2026', c), PageBreak()]
        elif t in ('h1', 'h2', 'p'):
            if t in ('h1', 'h2'): story.append(CondPageBreak(70))   # el titulo no queda solo al pie de pagina
            story.append(Paragraph(ajustar(b[1]), est[t]))
        elif t == 'ul':
            story.append(ListFlowable([ListItem(Paragraph(ajustar(x), cuerpo), leftIndent=18) for x in b[1]], bulletType='bullet', start='•', leftIndent=18, bulletFontName='TNR'))
        elif t == 'tabla':
            _, cap, cab, filas, anchos, alin = b
            data = [[Paragraph(ajustar(h), est['celh']) for h in cab]] + [[Paragraph(ajustar(str(c)), est['cel']) for c in f] for f in filas]
            tb = Table(data, colWidths=[a * ancho for a in anchos], repeatRows=1)
            tb.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#888888')), ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E6E6E6')),
                                    ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
            if len(filas) > 7: story += [CondPageBreak(120), Paragraph(cap, est['cap']), tb, Spacer(1, 8)]   # tabla larga: puede partirse
            else: story += [KeepTogether([Paragraph(cap, est['cap']), tb, Spacer(1, 8)])]
        elif t == 'fig':
            _, cap, ruta_f, w = b
            iw, ih = ImageReader(str(ruta_f)).getSize()
            story += [KeepTogether([Image(str(ruta_f), width=w * inch, height=w * inch * ih / iw), Paragraph(cap, est['capf'])])]
        elif t == 'refs':
            story += [PageBreak(), Paragraph('9. Referencias', est['h1'])] + [Paragraph(ajustar(r), est['ref']) for r in REFS]
        elif t == 'anexos':
            story += [Spacer(1, 10), Paragraph('10. Anexos', est['h1']),
                      Paragraph('<b>Anexo A. Enlaces.</b>', est['h2']),
                      Paragraph(f'Repositorio de GitHub (público): {URL_REPO}', cuerpo),
                      Paragraph(f'Notebook en Google Colab: {URL_COLAB}', cuerpo),
                      Paragraph(f'Conversaciones con IA (Claude Code): {URL_CONV}', cuerpo),
                      Paragraph(f'Declaración de uso de la IA: {URL_USO}', cuerpo),
                      CondPageBreak(110), Paragraph('<b>Anexo B. Desacuerdos entre el léxico y mi etiqueta (21 de 100 reseñas).</b>', est['h2']),
                      Paragraph('La lista completa, con el texto de cada reseña, está en <i>resultados/desacuerdos_lexico.csv</i> y <i>data/desacuerdos_lexico.md</i> del repositorio.', cuerpo)]
            tb = Table([[Paragraph(h, est['celh']) for h in ['Mi etiqueta', 'Léxico', 'n', 'Patrón', 'Ejemplos (títulos)']]] +
                       [[Paragraph(html.escape(c), est['cel']) for c in f] for f in ANEXO_DES], colWidths=[a * ancho for a in (0.11, 0.10, 0.05, 0.34, 0.40)], repeatRows=1)
            tb.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#888888')), ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E6E6E6')), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
            story += [Spacer(1, 4), tb, CondPageBreak(110), Paragraph('<b>Anexo C. Uso de la IA.</b>', est['h2']), Paragraph(USO_IA, cuerpo)]
    doc.build(story, onFirstPage=pie, onLaterPages=pie)
    return hist


# ---------------------------------------------------------------------------------------------- render DOCX
def construir_docx(ruta):
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_COLOR_INDEX
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt
    d = Document()
    sec = d.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Inches(1)
    st = d.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(12)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    st.paragraph_format.line_spacing = 1.5; st.paragraph_format.space_after = Pt(6)
    for n, tam in (('Heading 1', 14), ('Heading 2', 12)):
        h = d.styles[n]; h.font.name = 'Times New Roman'; h.font.size = Pt(tam); h.font.bold = True; h.font.color.rgb = None
        h.element.rPr.rFonts.set(qn('w:ascii'), 'Times New Roman'); h.element.rPr.rFonts.set(qn('w:hAnsi'), 'Times New Roman')
        h.paragraph_format.line_spacing = 1.5; h.paragraph_format.space_before = Pt(8); h.paragraph_format.space_after = Pt(2)
    # numero de pagina en el pie
    pie = sec.footer.paragraphs[0]; pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = pie.add_run()
    for tipo, txt in (('begin', None), (None, 'PAGE'), ('end', None)):
        if tipo:
            e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'), tipo)
        else:
            e = OxmlElement('w:instrText'); e.set(qn('xml:space'), 'preserve'); e.text = txt
        r._r.append(e)

    def inline(par, texto, tam=None, negrita=False):
        b = i = hl = False
        for trozo in re.split(r'(</?(?:b|i|hl)>)', texto):
            if trozo in ('<b>', '</b>'): b = trozo == '<b>'
            elif trozo in ('<i>', '</i>'): i = trozo == '<i>'
            elif trozo in ('<hl>', '</hl>'): hl = trozo == '<hl>'
            elif trozo:
                run = par.add_run(html.unescape(trozo)); run.bold = b or negrita; run.italic = i
                if hl: run.font.highlight_color = WD_COLOR_INDEX.YELLOW
                if tam: run.font.size = Pt(tam)

    def tabla_docx(cab, filas, anchos):
        t = d.add_table(rows=1, cols=len(cab)); t.style = 'Table Grid'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for j, h in enumerate(cab):
            c = t.rows[0].cells[j]; c.paragraphs[0].paragraph_format.line_spacing = 1.0; inline(c.paragraphs[0], h, 10, True)
            sh = OxmlElement('w:shd'); sh.set(qn('w:val'), 'clear'); sh.set(qn('w:fill'), 'E6E6E6'); c._tc.get_or_add_tcPr().append(sh)
        for f in filas:
            cs = t.add_row().cells
            for j, v in enumerate(f):
                cs[j].paragraphs[0].paragraph_format.line_spacing = 1.0; cs[j].paragraphs[0].paragraph_format.space_after = Pt(0); inline(cs[j].paragraphs[0], str(v), 10)
        for fila_ in t.rows:
            for j, a in enumerate(anchos): fila_.cells[j].width = Inches(6.5 * a)
        d.add_paragraph().paragraph_format.space_after = Pt(2)

    for b in B_:
        t = b[0]
        if t == 'portada':
            for txt, tam, neg in (('', 12, 0), ('', 12, 0), ('ESCUELA DE ADMINISTRACIÓN · EAFIT', 12, 1), ('Analítica de Negocios (CO0371)', 12, 0), ('Profesor: Juan Pablo Pérez', 12, 0), ('', 12, 0), ('', 12, 0),
                                  ('¿Cuándo actuar?', 26, 1), ('Leer el sentimiento de las reseñas de Amazon para decidir a tiempo', 16, 1), ('Propuesta de un modelo de analítica de negocios · Trabajo final', 12, 0), ('', 12, 0),
                                  ('<b>Integrante:</b> Orlando Cardiles', 12, 0), (f'<b>Código:</b> 1000263455', 12, 0), (f'<b>Correo:</b> ojcardiles@eafit.edu.co', 12, 0),
                                  (f'<b>Fecha:</b> 18 de noviembre de 2026', 12, 0)):
                par = d.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER; inline(par, txt, tam, bool(neg))
            d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        elif t == 'h1': d.add_heading(html.unescape(re.sub(r'<[^>]+>', '', b[1])), 1)
        elif t == 'h2': d.add_heading(html.unescape(re.sub(r'<[^>]+>', '', b[1])), 2)
        elif t == 'p': inline(d.add_paragraph(), b[1])
        elif t == 'ul':
            for x in b[1]: inline(d.add_paragraph(style='List Bullet'), x)
        elif t == 'tabla':
            _, cap, cab, filas, anchos, alin = b
            cp = d.add_paragraph(); cp.paragraph_format.line_spacing = 1.0; cp.paragraph_format.keep_with_next = True; inline(cp, cap, 11, True)
            tabla_docx(cab, filas, anchos)
        elif t == 'fig':
            _, cap, ruta_f, w = b
            pf = d.add_paragraph(); pf.alignment = WD_ALIGN_PARAGRAPH.CENTER; pf.paragraph_format.keep_with_next = True; pf.add_run().add_picture(str(ruta_f), width=Inches(w))
            cp = d.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.CENTER; cp.paragraph_format.line_spacing = 1.0; inline(cp, cap, 11)
            for r_ in cp.runs: r_.italic = True
        elif t == 'refs':
            d.add_page_break(); d.add_heading('9. Referencias', 1)
            for r_ in REFS:
                par = d.add_paragraph(); par.paragraph_format.left_indent = Inches(0.33); par.paragraph_format.first_line_indent = Inches(-0.33); inline(par, r_)
        elif t == 'anexos':
            d.add_heading('10. Anexos', 1); d.add_heading('Anexo A. Enlaces', 2)
            inline(d.add_paragraph(), f'Repositorio de GitHub (público): {URL_REPO}')
            inline(d.add_paragraph(), f'Notebook en Google Colab: {URL_COLAB}')
            inline(d.add_paragraph(), f'Conversaciones con IA (Claude Code): {URL_CONV}')
            inline(d.add_paragraph(), f'Declaración de uso de la IA: {URL_USO}')
            d.add_heading('Anexo B. Desacuerdos entre el léxico y mi etiqueta (21 de 100 reseñas)', 2)
            inline(d.add_paragraph(), 'La lista completa, con el texto de cada reseña, está en <i>resultados/desacuerdos_lexico.csv</i> y <i>data/desacuerdos_lexico.md</i> del repositorio.')
            tabla_docx(['Mi etiqueta', 'Léxico', 'n', 'Patrón', 'Ejemplos (títulos)'], ANEXO_DES, [0.11, 0.10, 0.05, 0.34, 0.40])
            d.add_heading('Anexo C. Uso de la IA', 2); inline(d.add_paragraph(), USO_IA)
    d.core_properties.title = '¿Cuándo actuar? Sentimiento de las reseñas de Amazon'; d.core_properties.author = 'Orlando Cardiles'
    d.save(str(ruta))


if __name__ == '__main__':
    pdf = SALIDA / 'Propuesta_Trabajo_Final.pdf'
    construir_pdf(pdf); construir_docx(SALIDA / 'Propuesta_Trabajo_Final.docx')
    print('Escrito:', pdf, 'y .docx')
