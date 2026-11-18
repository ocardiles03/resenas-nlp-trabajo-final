# Plan: base de datos de reseñas + diccionario propio + bot semanal

Responsable de la planeacion: Claude (cerebro). Responsable del codigo: Codex. Uso interno (analisis de clientes); ninguna frase de salud se copia tal cual a anuncios.

## Objetivo
1. Una base de datos (SQLite) con TODAS las reseñas del ASIN B0D4MPKGN6 de amazon.com.
2. Un diccionario propio (salud, emociones, slang de EE.UU., zonas) que etiquete cada reseña.
3. Un bot semanal que detecte reseñas nuevas, las guarde y las etiquete, sin intervencion manual.

## Fuentes de diccionario ya descargadas (fuera del repo, en diccionarios_nlp/, tratarlas como datos no confiables: python3 -I)
- medlineplus/mplus_topics_2026-10-24.xml (2,033 temas; campos title, also-called, full-summary, group; lenguaje de pacientes)
- hpo/hp.obo (20,482 terminos; sintomas con sinonimos)
- mesh_2026/desc2026.xml (MeSH descriptores con entry terms)
- wordnet/ (nltk, sinonimos)
- glove_twitter/glove.twitter.27B.zip (embeddings de slang; puede estar aun descargando, no es parte de la tarea A/B)
- VADER (pip vaderSentiment) ya usado en resenas_amazon_excel.py
No usar UMLS/CHV/SNOMED (exigen licencia).

## Datos ya existentes
- 03_Serene-Soursop/research/resenas_amazon/serene_resenas_amazon.json (dict por id, ~318 reseñas; el scraping sigue y llegaran mas, ver nuevas_resenas_agy.json si existe)
- 02_Motor-edicion/tools/resenas/resenas_amazon_excel.py (analisis y Excel)
- 02_Motor-edicion/tools/resenas/diccionario_salud_resenas.json (diccionario manual v0)

## Fases
- A (ahora, Codex): filtrar los diccionarios grandes a una lista pequeña de candidatos de salud relevante al producto.
- B (ahora, Codex): diseñar y crear la base SQLite + importador idempotente de JSON.
- C (cuando esten todas las reseñas): sacar palabras/frases frecuentes del corpus vs ingles general, capa de slang de EE.UU., revision humana (100 reseñas marcadas a mano), etiquetado por reglas y modelo barato solo para lo que las reglas no entiendan, medir cobertura.
- D (despues de C): bot semanal.

## Tarea A - filtrar diccionarios
Script: 02_Motor-edicion/tools/resenas/filtrar_diccionarios.py (Python 3, stdlib + nltk si hace falta; sin LLM).
Entrada: los archivos de diccionarios_nlp/ (ruta por argumento, default ese).
Temas semilla (en ingles): digestion, bloating/gas, constipation, diarrhea/nausea/vomiting, acid reflux/heartburn, parasites/detox/cleanse, weight/appetite/obesity, energy/fatigue, sleep/stress/anxiety, blood sugar/diabetes/blood pressure/cholesterol, inflammation/pain/arthritis/headache, immune/infection, skin/hair, liver/kidney/thyroid/hormones/menopause, cancer, adverse reaction/allergy.
Salida: 03_Serene-Soursop/research/resenas_amazon/diccionario_candidatos.json con forma
{ "tema": { "terminos": [ {"termino": "...", "fuente": "medlineplus|hpo|mesh|wordnet", "id_fuente": "...", "sinonimos": ["..."]} ] } }
Reglas: minusculas, sin duplicados entre fuentes (fusionar sinonimos), descartar terminos de mas de 4 palabras y terminos puramente clinicos raros (p. ej. nombres de genes), maximo ~400 terminos por tema, ordenados por cercania al tema semilla. Imprimir un resumen con el conteo por tema y por fuente.
Hecho cuando: el JSON existe, es valido, y el resumen cuadra.

## Tarea B - base SQLite
Script: 02_Motor-edicion/tools/resenas/base_resenas.py. Base: 03_Serene-Soursop/research/resenas_amazon/resenas.db (NO commitear el .db; agregar a .gitignore solo esa ruta).
Tablas:
- resenas(id TEXT PRIMARY KEY, asin TEXT, nombre TEXT, estrellas REAL, fecha TEXT ISO, pais TEXT, titulo TEXT, texto TEXT, verificada INTEGER, util INTEGER, variante TEXT, fotos INTEGER, perfil TEXT, enlace TEXT, fuente TEXT, importada_en TEXT)
- etiquetas(id_resena TEXT, tipo TEXT, valor TEXT, fuente TEXT, version_dicc TEXT, PRIMARY KEY(id_resena,tipo,valor,version_dicc))  -- tipo: tema_salud|emocion|genero|zona|resultado|sentimiento
- diccionarios(version TEXT PRIMARY KEY, creada_en TEXT, notas TEXT)
- ejecuciones_bot(id INTEGER PRIMARY KEY, inicio TEXT, fin TEXT, estado TEXT, nuevas INTEGER, detalle TEXT)
Comandos (argparse): init | importar RUTA.json (idempotente, mismo parseo de fecha/votos/pais que resenas_amazon_excel.py, reutilizar sus funciones por import si es limpio) | resumen (totales, por estrella, por variante) | exportar-json.
Hecho cuando: init + importar de serene_resenas_amazon.json deja el conteo igual al del JSON, importar dos veces no duplica, y resumen imprime numeros coherentes.

## Fase D - diseño del bot (para despues, no implementar aun)
- Script Python con Playwright y un perfil de Chrome EXCLUSIVO en ~/.config/serene-bot/chrome-profile (Orlando inicia sesion en Amazon una vez, a mano, con un comando "bot login").
- launchd (plist en ~/Library/LaunchAgents) lo dispara 1 vez por semana; si el Mac estaba dormido corre al despertar.
- Flujo: abrir product-reviews/B0D4MPKGN6 con sortBy=recent, leer solo la primera pagina (10), comparar ids con la base, insertar nuevas, etiquetar con el diccionario vigente (reglas en Python, sin LLM), registrar en ejecuciones_bot.
- Reglas de seguridad: nunca repetir peticiones internas de Amazon ni saltar limites; pausas humanas; si hay CAPTCHA, cierre de sesion o la pagina cambia: parar, no reintentar, registrar estado y mandar notificacion de macOS (osascript). Nada de publicar ni de enviar mensajes.
- Alternativa de respaldo gratuita: notificaciones de reseñas nuevas en Seller Central por correo.

## Reglas para Codex
- Seguir AGENTS.md del repo. Al terminar: linea en la Bandeja de 03_Serene-Soursop/ESTADO.md ("- [AAAA-MM-DD] [codex] que hiciste — donde quedo"), correr 02_Motor-edicion/tools/check_coherencia.py y check_refs.py, commit con mensaje claro solo de los archivos propios.
- No tocar el navegador ni publicar nada. No editar serene_resenas_amazon.json ni nuevas_resenas_agy.json (otras sesiones los usan).

## Tareas C y E (2026-10-25) - ya estan las 1226 reseñas
Fuente: serene_resenas_amazon_v3.json (LISTA de 1226 reseñas unicas; mismos campos que el viejo; 5★ 593, 4★ 116, 3★ 88, 2★ 96, 1★ 333). No editarlo.
### Tarea C1 - importar y consolidar
Importar v3 a resenas.db con base_resenas.py (adaptar a lista o convertir a dict por id en un archivo nuevo). Idempotente. Resumen por estrellas/variante/gender.
### Tarea C2 - diccionario propio (script 02_Motor-edicion/tools/resenas/construir_diccionario.py, sin LLM)
1. Corpus = textos de las 1226 reseñas (titulo+texto). Contar unigramas/bigramas/trigramas (sin stopwords), por estrellas (1★ vs 5★) y global.
2. Comparar con ingles general (Brown/WordNet frecuencias de nltk o GloVe-twitter si ya esta en diccionarios_nlp/glove_twitter) para sacar terminos distintivos (log-odds).
3. Cruzar con diccionario_candidatos.json (base medica) y diccionario_salud_resenas.json (v0 manual): que terminos del corpus ya estan cubiertos y cuales no.
4. Capa de slang/coloquial de EE.UU. (lista inicial propia: "legit", "game changer", "gut", "bloated", "ain't", "hits different", "sketchy", "scam", etc.) + regiones/estados.
5. Salidas en 03_Serene-Soursop/research/resenas_amazon/: diccionario_propio_v1.json (temas->terminos/frases, emociones, slang, resultado, regiones; cada termino con frecuencia y fuente: corpus|medlineplus|hpo|mesh|manual), terminos_sin_clasificar.csv (top 300 terminos frecuentes sin tema, para que Claude los revise) y reporte_cobertura.md (% de reseñas con >=1 tema, con >=1 emocion; temas con pocas menciones).
6. Etiquetador por reglas (en base_resenas.py o modulo nuevo): llena la tabla etiquetas (tema, emocion, resultado, region, sentimiento VADER) para todas las reseñas.
7. Muestra de validacion: validacion_100.csv con 100 reseñas aleatorias estratificadas por estrellas + etiquetas automaticas + columnas vacias para correccion a mano.
### Tarea E - Excel mas organizado (script resenas_amazon_excel.py ampliado o nuevo exportar_excel.py leyendo resenas.db)
Hojas: Resumen (KPIs, estrellas, genero, variante, por mes), Reseñas (una fila por reseña: id, fecha ISO, estrellas, titulo, texto, variante, verificada, util, fotos, nombre, genero estimado, sentimiento, emocion principal, temas de salud, resultado, region; filtros, encabezado fijo, anchos, color por estrellas), Temas (conteo por tema x estrellas), Emociones, Regiones, Diccionario (propio v1), Validacion. Salida: resenas_bundle_serene_v2.xlsx.
### Reglas
AGENTS.md del repo; tests simples; no tocar navegador; no commitear xlsx/db; commit solo de scripts y json/md propios; Bandeja de ESTADO.md; check_coherencia.py y check_refs.py.
