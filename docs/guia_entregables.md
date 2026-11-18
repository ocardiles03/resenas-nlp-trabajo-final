# Guía exacta para el documento PDF, las diapositivas y el pitch

Es una **guía** (qué lleva cada parte, de dónde sacar los números, qué preguntas responder). Fuente: `curso/00_trabajo_final/Trabajo_Final_editable.docx`.
Rúbrica del portafolio: Problema 15 % · Datos 15 % · Modelos 20 % · Resultados 25 % · Recomendaciones 10 % · Notebook 10 % · Forma/APA 5 %.

## Formato del PDF (del enunciado)
Máx. **12 páginas** sin portada/referencias/anexos · fuente 12 · interlineado 1,5 · **≥ 5 referencias APA 7** · Colab ejecutado de principio a fin con datos desde el repo · README con ficha de procedencia.

## Estructura del PDF (orden fijado por el enunciado, 4.1) y presupuesto de páginas
Portada, referencias y anexos no cuentan para las 12 páginas.

| # | Sección (orden del enunciado) | Págs. aprox. | Rúbrica | Qué debe contener | De dónde salen los datos |
|---|---|---|---|---|---|
| 0 | Portada | aparte | Forma | Curso, profesor, integrantes (nombres, códigos, correos), título, fecha | — |
| 1 | Resumen ejecutivo | 0,5 | Problema | ≤ 250 palabras: problema, solución, resultado principal, recomendación | Al final, con los resultados |
| 2 | Problema de negocio | 1 | Problema 15 % | Qué organización, qué decisión, cómo la toma hoy, cuánto cuesta equivocarse | `contexto_marca/` |
| 3 | Propuesta de valor | 0,5 | Problema | Qué cambia, quién usa el modelo, en qué momento de la decisión, beneficio esperado | Tus conclusiones |
| 4 | Datos | 2 | Datos 15 % | Ficha de procedencia, n.º de registros, período, qué es un registro, preparación, descriptivo breve, **diccionario de variables** (nombre, descripción, tipo, unidad, rol); muestra etiquetada a mano | `data/README_datos.md`; notebook §2 (celda de preparación) |
| 5 | Cómo funciona cada modelo | 1,5 | Modelos 20 % | Explicación intuitiva sin fórmulas, por qué se ajusta, alternativas descartadas | Notebook §3 (léxico, KNN, Naive Bayes y k-means: tres familias) |
| 6 | Configuración y métricas | 1 | Modelos | Partición 80/20 (semilla 42, estratificada), parámetros y cómo se escogieron, por qué esas métricas (qué error sale más caro) | Notebook §3; `src/acierto_sentimiento.py` |
| 7 | Resultados | 3 | Resultados 25 % | Tablas y figuras, comparación de modelos, lectura en lenguaje de negocio, **un ejemplo concreto de uso**, evolución por semestre, errores | Notebook §4 y `resultados/` |
| 8 | Recomendaciones, riesgos, limitaciones y próximos pasos | 1,5 | Recomend. 10 % | Coherentes con los resultados y realistas; riesgos de confiar en el modelo; limitaciones de los datos | Tablas con *n* por semestre |
| 9 | Referencias | aparte | Forma 5 % | ≥ 5 reales en APA 7, incluida la fuente de los datos | — |
| 10 | Anexos | aparte | Notebook | Enlaces al repositorio/Colab y a las conversaciones con IA; lista de desacuerdos; ficha de datos | `resultados/desacuerdos_lexico.csv` |

Reglas de forma: fuente 12, interlineado 1,5, páginas numeradas, tablas y figuras con número y leyenda y citadas en el texto antes de aparecer.

## Lo que cada sección tiene que dejar claro (checklist)
- [ ] Hilo **problema → datos → modelo → decisión** (la nota pesa sobre todo en la coherencia).
- [ ] Cada número del texto aparece en una tabla del notebook y viceversa.
- [ ] Todo lo que afirmes sobre una causa (p. ej. por qué el léxico se equivoca) se apoya en casos que leíste, no en suposiciones.
- [ ] Cada limitación va acompañada de su efecto sobre lo que puedes concluir.
- [ ] Las métricas binarias excluyen los Neutro: dilo y di cuántos son.
- [ ] Todos los integrantes pueden explicar el código (todos deben conocer todo).

## Preguntas guía por sección (para tus propias palabras)
- **Problema:** ¿quién decide?, ¿qué decide?, ¿qué cambia si el sentimiento sube o baja?
- **Datos:** ¿por qué estas reseñas?, ¿qué sesgos tienen?, ¿qué no sabes de ellas?
- **Modelos:** ¿por qué léxico + KNN + k-means (sentimientos, clasificación y agrupamiento)?, ¿qué ve cada uno en el texto?, ¿qué es k y cómo se eligió?
- **Resultados:** ¿qué modelo acierta más y con qué margen?, ¿cuánto de esa diferencia es ruido por el tamaño de la muestra?, ¿qué errores comete cada uno?, ¿qué patrón ves en los desacuerdos?, ¿cómo evoluciona el sentimiento y qué semestres son poco fiables?
- **Recomendaciones:** ¿qué harías mañana distinto?, ¿qué medirías después?

## Diapositivas (pitch 15 min + 5 de preguntas)
Reparto sugerido por el enunciado: 3 min organización, decisión y costo de equivocarse · 3 min datos y origen · 4 min modelo sin tecnicismos y configuración · 4 min resultados y significado · 1 min recomendación. Todos exponen.

| Bloque | Diapositivas posibles | Tiempo |
|---|---|---|
| Organización, decisión y costo de equivocarse | Portada + problema | 3 min |
| Datos y su origen | Fuente, período, tamaño, ficha; muestra manual y criterio | 3 min |
| Modelo sin tecnicismos y configuración | Esquema de los modelos; partición y k | 4 min |
| Resultados y qué significan | Tabla de métricas + matriz; errores con ejemplos; evolución por semestre | 4 min |
| Recomendación final | Decisión y próximos pasos | 1 min |

Reglas: una idea por diapositiva, números grandes, pocas palabras; el 40 % de la nota es la evaluación de pares, así que ensayen quién explica qué.

## Preguntas que pueden hacerte en los 5 min (ensáyenlas con tus palabras)
1. ¿Por qué 100 reseñas son suficientes? ¿Qué intervalo de confianza tienen tus resultados?
2. ¿Por qué se excluyen los Neutro de las métricas?
3. ¿Qué es k y por qué elegiste ese valor?
4. ¿El léxico "vio" la muestra? (ver "Léxico sin la muestra")
5. ¿Qué significa un AUC de ese valor?
6. ¿Qué pasaría con reseñas en otro idioma o con ironía?
7. ¿Qué decisión concreta tomaría la organización con esto?
8. ¿Cómo sabes que el periodo cubierto es suficiente? (ten a mano la aprobación del profesor)

## Pendientes antes de entregar
- [ ] Pegar `REPO_URL` en el notebook, subir el repo y ejecutar en Colab de principio a fin.
- [ ] Completar la ficha de procedencia (`data/README_datos.md`).
- [ ] Guardar en `curso/` la evidencia de aprobación del periodo de datos.
- [ ] Anexos del PDF: enlace al repositorio/Colab y a las conversaciones con IA (lo pide el enunciado, 4.1 punto 11).
- [ ] Escribir todas las celdas ✍️ del notebook, el PDF y las diapositivas.
