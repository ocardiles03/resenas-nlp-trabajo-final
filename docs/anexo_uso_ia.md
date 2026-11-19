# Declaración de uso de la IA

**Herramienta:** Claude Code (Anthropic), usado por Orlando Cardiles del 12 al 19 de noviembre de 2026. Todo el proyecto (código, notebook, análisis y documento) se hizo en esa herramienta.

**Cómo se trabajó.** Fue una construcción conjunta entre Orlando y Claude. No todas las instrucciones vinieron de Orlando: en varios puntos Claude propuso el enfoque y Orlando lo aceptó, lo corrigió o lo rechazó.

**Qué hizo Orlando**
- Definió la organización, el problema y la decisión, y dijo qué entregables hacían falta.
- Etiquetó a mano las 100 reseñas de la muestra (la herramienta solo guarda lo que él elige; no etiqueta nada por su cuenta).
- Revisó resultados y texto, corrigió el rumbo (por ejemplo, el orden del documento y el tono de la redacción) y decidió publicar el repositorio con los datos tal como se descargaron.

**Qué hizo Claude**
- Escribió el código: preparación de la base, léxico, KNN, Naive Bayes, k-means, pruebas y el generador del notebook.
- Ejecutó las pruebas y los modelos y exportó las tablas y figuras.
- Propuso la razón de costos c = 5 para la segunda lectura, que Orlando aceptó.

**Redacción y conclusiones.** Claude ayudó con la redacción del documento y con las conclusiones; ambas fueron una construcción de los dos en conversación, no algo escrito solo por uno de los dos.

**Qué se puede verificar.** Las cifras del documento salen de `resultados/*.csv`, que exporta el notebook, y el generador del documento las contrasta con esos archivos antes de escribir el PDF.

**Transcripciones.** Están en [`conversaciones_ia/`](conversaciones_ia/): texto limpio de las conversaciones, sin salidas de herramientas, con el correo personal y los nombres de compradores redactados.
