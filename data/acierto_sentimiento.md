# Acierto del sentimiento frente a etiquetas manuales

Hoja(s): etiquetado_manual_100.xlsx. Etiquetadas: 100 (Negativo 33, Neutro 15, Positivo 52).
Particion 80/20 estratificada, semilla 42: entrenamiento 80, prueba 20 (17 sin Neutro).
Binario = Positivo (clase 1) vs Negativo; las Neutro manuales no entran en las metricas binarias. VN/FP/FN/VP = matriz de confusion.

## 1. Conjunto de prueba (20 %): todos los modelos con las mismas resenas

| Modelo | n | VN | FP | FN | VP | Exactitud (IC 95 %) | Sensibilidad | Especificidad | Precision | F1 | AUC |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Lexico del proyecto | 17 | 7 | 0 | 1 | 9 | 0.941 (0.730-0.990) | 0.900 | 1.000 | 1.000 | 0.947 | 1.000 |
| Lexico sin la muestra | 17 | 7 | 0 | 1 | 9 | 0.941 (0.730-0.990) | 0.900 | 1.000 | 1.000 | 0.947 | 0.986 |
| KNN con estrellas | 17 | 5 | 2 | 0 | 10 | 0.882 (0.657-0.967) | 1.000 | 0.714 | 0.833 | 0.909 | 0.993 |
| Naive Bayes con estrellas | 17 | 5 | 2 | 0 | 10 | 0.882 (0.657-0.967) | 1.000 | 0.714 | 0.833 | 0.909 | 1.000 |
| KNN con etiquetas manuales | 17 | 7 | 0 | 2 | 8 | 0.882 (0.657-0.967) | 0.800 | 1.000 | 1.000 | 0.889 | 0.986 |

KNN con etiquetas manuales: k = 11 (CV de hasta 5 pliegues sobre el entrenamiento), corte = 0.618. KNN con estrellas: k = 25, entrenado con 1080 resenas del Excel v4 (sin las etiquetadas). Naive Bayes con estrellas: alfa = 0.3 (CV de 5 pliegues, misma base de entrenamiento).

| k | 1 | 3 | 5 | 7 | 9 | 11 | 15 | 21 | 25 | 31 | 41 | 51 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AUC (CV), KNN manual | 0.814 | 0.911 | 0.942 | 0.953 | 0.951 | 0.973 | 0.944 | 0.908 | 0.916 | 0.889 | 0.789 | 0.641 |

## 2. Toda la muestra etiquetada (modelos que no se entrenan con ella)

| Modelo | n | VN | FP | FN | VP | Exactitud (IC 95 %) | Sensibilidad | Especificidad | Precision | F1 | AUC |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Lexico del proyecto | 85 | 32 | 1 | 4 | 48 | 0.941 (0.870-0.975) | 0.923 | 0.970 | 0.980 | 0.950 | 0.987 |
| Lexico sin la muestra | 85 | 31 | 2 | 4 | 48 | 0.929 (0.854-0.967) | 0.923 | 0.939 | 0.960 | 0.941 | 0.976 |
| KNN con estrellas | 85 | 29 | 4 | 1 | 51 | 0.941 (0.870-0.975) | 0.981 | 0.879 | 0.927 | 0.953 | 0.991 |
| Naive Bayes con estrellas | 85 | 28 | 5 | 1 | 51 | 0.929 (0.854-0.967) | 0.981 | 0.848 | 0.911 | 0.944 | 0.994 |

## 3. Matriz de confusion de 3 clases: lexico del proyecto (filas = manual, columnas = lexico)

| manual \ lexico | Negativo | Neutro | Positivo |
|---|---|---|---|
| Negativo | 29 | 3 | 1 |
| Neutro | 9 | 2 | 4 |
| Positivo | 0 | 4 | 48 |

## 4. Evolucion por semestre (muestra etiquetada)

| Semestre | n | % Positivo manual | % Neutro manual | % Negativo manual | % positivo segun lexico |
|---|---|---|---|---|---|
| 2024-S1 | 1 | 0 % | 0 % | 100 % | 0 % |
| 2024-S2 | 7 | 14 % | 14 % | 71 % | 14 % |
| 2025-S1 | 22 | 18 % | 18 % | 64 % | 27 % |
| 2025-S2 | 16 | 44 % | 25 % | 31 % | 44 % |
| 2026-S1 | 30 | 80 % | 10 % | 10 % | 73 % |
| 2026-S2 | 24 | 67 % | 12 % | 21 % | 71 % |

## 5. Evolucion por semestre (todo el Excel v4, sin etiquetas manuales)

| Semestre | n | % 4-5 estrellas | % positivo segun lexico |
|---|---|---|---|
| 2024-S1 | 2 | 50 % | 50 % |
| 2024-S2 | 90 | 40 % | 39 % |
| 2025-S1 | 268 | 30 % | 25 % |
| 2025-S2 | 324 | 59 % | 55 % |
| 2026-S1 | 313 | 71 % | 66 % |
| 2026-S2 | 274 | 73 % | 68 % |
