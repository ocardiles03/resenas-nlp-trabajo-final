# Cobertura del diccionario propio v1

Corpus: 1226 reseñas v3; base consolidada: 2741. Fuente SHA256: c8ee3cb861d56e7e7001ab0fbaf34d2d5a7e230ea7bfd8e94510c385bb72b203.

Referencia: WordNet: conteos de uso de lemas (proxy; no corpus general balanceado). Log-odds con suavizado 0,5, por ocurrencias; vocabulario conjunto. N-gramas contiguos sin stopwords; referencia de frases escasa: interpretar su ranking con cautela.

- tema_salud: 457/1226 (37.28 %).
- tema_producto: 910/1226 (74.23 %).
- emocion: 719/1226 (58.65 %).
- temas_totales: 1044/1226 (85.15 %).

## Temas (menciones, no resultados comprobados)

- acidez_reflujo: 7 — pocas menciones (<10)
- azucar_presion: 17
- cancer_enfermedad_grave: 3 — pocas menciones (<10)
- diarrea_nausea: 16
- digestion: 237
- efecto_adverso: 60
- energia_fatiga: 111
- estrenimiento: 95
- higado_rinon_tiroides: 13
- hinchazon_gases: 75
- inflamacion_dolor: 32
- inmunidad: 37
- parasitos_limpieza: 86
- peso_apetito: 63
- piel_cabello: 14
- sueno_estres: 30

## Operacion/Producto (menciones por tema)

- dudas_autenticidad: 183
- entrega_pedido: 337
- envase_plastico_vidrio: 354
- precio_valor: 195
- sabor: 636

## Cobertura de resenas de 1 estrella

- Con al menos un tema de salud o producto: 320/333 (96.10 %).
- Explicadas por una senal de queja concreta o resultado sin_efecto/efecto_adverso: 255/333 (76.58 %).
- Sin explicacion automatica concreta: 78/333.
- Explicadas es una aproximacion por reglas, no precision validada. Una simple mencion de bottle, taste o pedido no basta para explicar una estrella; se exige senal de queja del tema o resultado negativo. Las quejas pueden ser negadas o referidas a terceros y necesitan revision humana.

## Taxonomia y seleccion de terminos

- 16 temas de salud canonicos sin tildes y 5 de producto; las etiquetas activas se regeneran sin alias ingleses. Se conserva el mapa de alias en _meta.taxonomia.
- bloating_gas pasa a hinchazon_gases; sus disparadores de hinchazon/gas se retiran de digestion. La union de reseñas con salud se conserva.
- terminos_producto_top150.csv documenta los 150 terminos distintos presentes, sus frecuencias y asignacion. Seleccion entre candidatos utiles revisados del CSV de no clasificados y de las frecuencias completas; desempate alfabetico. Se suman las semillas pedidas aunque no entren en los 150. Procedencia corpus + revision manual.
- Ejemplos propuestos: plastic bottles, seal, leaking, customer service, replacement, watered down, formula, aftertaste, flavor, worth it. No se clasifican como producto palabras genericas como good, product o artefactos «se pudo cargar el archivo multimedia».
- Palabras ambiguas (came/different/real/quality/strong/open/etc.) requieren contexto local segun taxonomia_resenas.py. Las frecuencias del diccionario son literales; las etiquetas aplican ese filtro contextual.
- terminos_sin_clasificar.csv significa ahora sin tema de salud NI Operacion/Producto. Puede contener palabras ya cubiertas por emocion/resultado.
- Region: BAJA COBERTURA, 2/1226; se mantiene como mencion, sin inferir residencia.

## Validacion pendiente

Muestra estratificada reproducible (semilla 20261025): {1: 27, 2: 8, 3: 7, 4: 10, 5: 48}. 100 filas; columnas manuales preservadas por ID. La cobertura no mide precision ni recall; falta revision humana.

Se normalizan apostrofos y se usan limites de palabra. Negacion local solo para emociones y resultados; temas son menciones incluso negadas. Resultado puede ser multiple. Genero es estimado; region es mencion textual, nunca residencia. Riesgos: polisemia (regular, cold, gas), sarcasmo, negaciones lejanas y alusiones a terceros. No se infieren zonas por slang. Sentimiento VADER: ±0,05; emocion principal = mas expresiones distintas, desempate alfabetico.

## C1: resumen consolidado

- estrellas: {3.0: 302, 1.0: 508, 5.0: 1393, 2.0: 283, 4.0: 255}
- variante: {'Flavor Name: SoursopSize: 16 Fl Oz (Pack of 1)': 1313, 'Tamaño: 16 Fl Oz (Pack of 2)': 1077, 'Tamaño: 16 Fl Oz (Pack of 3)': 149, '': 194, 'Nombre del sabor: GuanábanaTamaño: 16 Fl Oz (paquete de 1)': 8}
- genero estimado: {'No claro': 1079, 'Mujer': 1043, 'Hombre': 537, 'unisex': 82}

## Genero y zona reforzados (v2)

- Genero estimado Hombre/Mujer: 722/1226 (58.89 %); unisex: 30; No claro: 474.
- Confianza (todas las resenas): {'media': 711, 'baja': 508, 'alta': 7}.
- Genero por confianza: {('Mujer', 'media'): 436, ('No claro', 'baja'): 474, ('Hombre', 'media'): 275, ('unisex', 'baja'): 30, ('Mujer', 'alta'): 6, ('Mujer', 'baja'): 4, ('Hombre', 'alta'): 1}.
- Region de EEUU mapeada: 2/1226 (0.16 %); menciones geograficas incluyendo ambiguas: 2.
- Origen cultural autorreferido: 1; menciones culturales sin autorreferencia no se infieren como origen.
- Nombres: manual US + gender-guesser; nltk names/SSA no disponibles. Apodos manuales; inicial aislada no utiliza el apellido. Unisex se mantiene como categoria, sin forzar genero.
- Texto explicito gana al nombre (alta). Pista indirecta como my husband/my wife gana al nombre, pero solo es alta si coinciden; de otro modo baja. Ladies/sir son audiencia y no asignan genero. Dos pistas explicitas incompatibles dejan No claro. Las inferencias de pareja son heuristicas y requieren revision.
- Estado/region/division/evidencia se conservan por mencion en zona_detalle. Una resena puede mencionar varias ubicaciones. IN/OR/ME/OK/HI y otras siglas solo mayusculas con contexto locativo o postal. Tri-state, East Coast y Southwest quedan ambiguas sin asignacion censal unica. Gulf Coast: Sur, division indeterminada; no se inventa estado ni division.
- Washington State se distingue de DC; Portland sin estado no se asigna. Caribbean/Jamaica se conservan aparte de EEUU. No se deduce residencia por el nombre ni por el estilo de escritura.

## Hasta 30 frases geograficas halladas para revision

1. R11L3MM91YO7WG — Hawaii / Oeste / Pacífico:  is the serene herbs website doesn’t ship to Hawaii anymore. Do not buy this product from Amazon!!!!
2. R25NEW14NEHUTO — Virginia / Sur / Atlántico Sur: TED THIS PRODUCT IS MADE/BOTTLED IN THE US. (VIRGINIA) THE 1ST ORIGINAL I PURCHASED WAS MADE AND BOTTLED IN GHANA. SO 

Solo se hallaron 2 menciones geograficas en el corpus; se listan todas, sin completar con frases inventadas.

## Ejecucion

Usar venv con openpyxl, nltk, vaderSentiment y gender-guesser; WordNet local en diccionarios_nlp/wordnet. Ejecutar con -I: construir_diccionario.py y exportar_excel.py. Pruebas: python -I -m unittest discover -s 02_Motor-edicion/tools/resenas/tests -p "test_*resenas.py". La validacion_100 conserva correcciones manuales por ID al regenerar.
