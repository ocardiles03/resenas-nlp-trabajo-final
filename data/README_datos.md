# README de datos — borrador de HECHOS (el texto final de la ficha lo escribe el equipo)

> Esta hoja reúne solo datos verificables del repositorio. Donde dice **[COMPLETA TÚ]** falta información que solo el equipo sabe.
> Ficha de procedencia obligatoria (enunciado): **nombre, enlace exacto, fecha de descarga, quién/cómo/cuándo recolectó**.

> **Datos personales:** los archivos originales (`data/crudo_chrome_apify/`, `data/bundle_xlsx_historico/` y similares) conservan el nombre público del comprador tal como lo muestra Amazon y, en la descarga de Apify, el enlace a su perfil. La base preparada (`base_preparada_resenas.csv`) no incluye el nombre del comprador.

## 1. Ficha de procedencia

| Campo de la ficha | Dato disponible en el repositorio | Falta |
|---|---|---|
| Nombre de la base | Reseñas de Amazon del producto Serene Herbs Black Seed Bitters + Soursop Bitters (bundle 32 oz, pack de 2), ASIN **B0D4MPKGN6** (base 1). Segunda base: producto ASIN **B0CYV4FCJS** (Soursop). | **[COMPLETA TÚ]** nombre con el que se citará en el PDF |
| Enlace exacto | Base 1: `https://www.amazon.com/product-reviews/B0D4MPKGN6/` · Base 2: `https://www.amazon.com/product-reviews/B0CYV4FCJS/` | **[COMPLETA TÚ]** confirmar que son los enlaces que se usarán en el documento |
| Fecha de descarga | Descarga con Apify: **2026-10-23** (nombre del archivo en `data/crudo_chrome_apify/`). Otros lotes: ver `data/bundle_xlsx_historico/` (v1-v3) y `data/crudo_chrome_apify/serene_chrome_reviews*.json`. | **[COMPLETA TÚ]** fechas exactas de cada lote |
| Quién recolectó | Los dueños/vendedores del producto (el brief de recolección dice: "soy el vendedor del producto"). | **[COMPLETA TÚ]** nombres de quienes recolectaron |
| Cómo recolectó | (a) Navegador Chrome con sesión de Amazon iniciada, botón "Mostrar 10 opiniones más", con pausas aleatorias de 4 a 9 s, por filtros de estrellas/orden/palabra clave (`recoleccion/brief_gemini.txt`). (b) Herramienta de terceros Apify "amazon-reviews-scraper-with-advanced-filters" (`data/crudo_chrome_apify/`, `recoleccion/apify_import/`). (c) Scripts y logs en `recoleccion/`. | **[COMPLETA TÚ]** descripción del proceso con tus palabras |
| Cuándo | Reseñas con fecha entre **jun-2024 y oct-2026** en la base 1 (1.271 reseñas con texto); recolección en octubre de 2026. | **[COMPLETA TÚ]** |
| Aprobación del periodo (≥ 4 años de seguimiento en ruta de corpus propio) | El equipo indicó que ya está comprobado. | **[COMPLETA TÚ]** guardar la evidencia (correo/mensaje del profesor) en `curso/` y citarla |

## 2. Qué es original y qué es preparado

| Tipo | Archivo | Contenido |
|---|---|---|
| Original (crudo) | `data/crudo_chrome_apify/*.json` | Descargas crudas del navegador y de Apify |
| Original (crudo) | `data/bundle_xlsx_historico/*.xlsx`, `data/serene_resenas_amazon*.json` | Lotes históricos de reseñas |
| Preparado | `data/reviews_bundle_soursop_bitters_v4.xlsx` | Base 1 unificada: id, estrellas, título, texto, fecha (1.271 reseñas con texto) |
| Preparado | `data/resenas_soursop_base_organizada.csv` | Base 2 organizada (2.519 reseñas con texto) |
| Etiquetas manuales | `data/etiquetado_manual_100.xlsx` | 100 reseñas etiquetadas a mano (columna `sentimiento_manual`) |
| Modelos / léxico | `data/lexico_cliente_v4.json`, `data/lemas_cliente_v4.json` | Léxico de sentimiento y lematización |
| Resultados | `data/acierto_sentimiento.md`, `data/desacuerdos_lexico.md` | Tablas de acierto y lista de desacuerdos léxico-manual |

## 3. Variables
`id` (id de la reseña en Amazon) · `estrellas` (1-5) · `titulo` · `texto` (inglés) · `fecha` (ISO) · `semestre` (derivada: AAAA-S1/S2) · `sentimiento_manual` (Positivo/Negativo/Neutro, solo en la muestra de 100).
Variable categórica objetivo: sentimiento (Positivo/Negativo). Variable numérica pronosticable: estrellas / % positivo por periodo. **[COMPLETA TÚ]** confirmar cuál presentas como objetivo.

## 4. Cómo reproducir
1. Abrir `Trabajo_Final_Resenas.ipynb` en Colab, pegar la URL del repositorio en `REPO_URL`.
2. Entorno de ejecución → Ejecutar todo.
