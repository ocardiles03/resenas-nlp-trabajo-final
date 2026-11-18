# Comparación de modelos sobre todas las reseñas escritas (Excel v4)

1271 reseñas con texto: 1172 polares (4-5★ = positiva: 728; 1-2★ = negativa: 444) y 99 de 3★. Validación cruzada de 5 grupos repetida 3 veces (15 ajustes): cada reseña se lee siempre con modelos que no la vieron. KNN con k=25, TF-IDF de palabras y parejas, texto lematizado. Corte de KNN y regresión = proporción de positivas del entrenamiento; la balanza usa >0; las combinaciones usan la misma proporción.

## 1. Resultados (media ± desviación en los 15 ajustes)

| Modelo | Exactitud | Positivas reconocidas | Negativas reconocidas | AUC |
|---|---|---|---|---|
| Regla ingenua (todas positivas) | 0.621 | 1.000 | 0.000 | 0.500 |
| Regresión logística (TF-IDF) | 0.915 ± 0.019 | 0.915 ± 0.026 | 0.914 ± 0.035 | 0.967 ± 0.011 |
| KNN + regresión | 0.907 ± 0.021 | 0.924 ± 0.016 | 0.879 ± 0.029 | 0.966 ± 0.011 |
| KNN solo palabras sueltas | 0.899 ± 0.016 | 0.907 ± 0.025 | 0.887 ± 0.032 | 0.959 ± 0.012 |
| KNN (palabras + parejas, lematizado) | 0.900 ± 0.020 | 0.899 ± 0.023 | 0.901 ± 0.030 | 0.958 ± 0.012 |
| KNN + balanza (promedio de posiciones) | 0.889 ± 0.018 | 0.907 ± 0.016 | 0.861 ± 0.024 | 0.956 ± 0.012 |
| KNN sin quitar palabras vacías | 0.889 ± 0.017 | 0.897 ± 0.022 | 0.876 ± 0.033 | 0.955 ± 0.012 |
| KNN sin lematizar | 0.894 ± 0.019 | 0.902 ± 0.027 | 0.881 ± 0.027 | 0.954 ± 0.013 |
| Balanza aprendida (diccionario anterior) | 0.859 ± 0.022 | 0.836 ± 0.031 | 0.897 ± 0.030 | 0.931 ± 0.017 |
| KNN solo con términos del diccionario | 0.859 ± 0.022 | 0.880 ± 0.035 | 0.824 ± 0.048 | 0.921 ± 0.019 |

## 2. Aciertos por número de estrellas y por género estimado (fuera de muestra)

| Grupo | Reseñas | Balanza | KNN | KNN + balanza |
|---|---|---|---|---|
| 1★ | 342 | 0.89 | 0.91 | 0.88 |
| 2★ | 102 | 0.87 | 0.86 | 0.80 |
| 4★ | 120 | 0.69 | 0.77 | 0.78 |
| 5★ | 608 | 0.89 | 0.93 | 0.94 |
| Hombre | 274 | 0.85 | 0.89 | 0.88 |
| Mujer | 427 | 0.88 | 0.90 | 0.90 |
| No claro | 471 | 0.87 | 0.91 | 0.90 |

## 3. Las 99 reseñas de 3★ (sin respuesta correcta; lectura de los modelos ajustados a todas las polares)

- KNN: 34 positivas y 65 negativas (media de probabilidad 0.46).
- Balanza: 29 positivas, 58 negativas, 12 neutras.

## 4. Errores del KNN: 118 de 1172 (10.1 %). Los 12 más seguros de sí mismos

| ID | Estrellas | Prob. positiva | Texto |
|---|---|---|---|
| `RN6DXXAC1LDDE` | 5★ | 0.03 | N/A. Bottles were broken |
| `RZITPOIFG60CT` | 2★ | 0.93 | 🙄. Well people said that they worked for them but for me it isn’t good luck for that |
| `R28CF9LJUPC2F7` | 4★ | 0.08 | Not the same. Does not come in the glass bottle??? Feels like is water down |
| `R73SDSYDMAPE6` | 5★ | 0.08 | Will you go back to glass bottles?. I love the product, was very surprised it now comes in plastic bottles. With all the concerns for liquid in plastic, will you ever go  |
| `R24CI7AROX4KDI` | 1★ | 0.91 | TASTE WARNING ⚠️. I will never get to know if this product does what I claim.If you can't stand unpleasant taste please don't purchase this the taste is horrendous. And y |
| `R1F8GXWLKOJC37` | 5★ | 0.09 | This stuff is a Scam not the same thing. What is this !!!!!!!!! Stop selling this now people just scamming I have bought this stuff for a minute it was worth it this last |
| `R7PF7NBZ2M786` | 5★ | 0.09 | Not as expected. Seems watered down |
| `R1SPQKVU2THNRO` | 5★ | 0.09 | Good but now comes in plastic bottles.. My latest order came in plastic bottles so what’s up with that now.  Please keep up the glass bottles. |
| `RBWP067Y4YEGI` | 2★ | 0.89 | Getting hives....... After taking this, I'm getting rashes and hives. Did some research and this product can cause hives, due to the cleansing detox nature. |
| `RFEMUCVB1G1OK` | 4★ | 0.11 | Didn’t receive the quantity expected.. I just received these items so I have not tried them yet, but I was under the impression that I ordered two 32oz bottles not two 16 |
| `R1UPQ2T6Q2FKRJ` | 4★ | 0.12 | No Detox for me!. This product was not even similar to the first product I purchased. Would not waste my money on the detox or the black seed bitters. Very disappointing! |
| `R2T1ULGGRBE10` | 5★ | 0.13 | Good.. Good product. I see that they now come in plastic bottles...They still say the same amount, but the plastic bottles are slightly smaller than the glass bottles wer |

Tipos de error:

- elogio leído como queja: 72
- queja leída como elogio: 46

## 5. ¿Más reseñas ayudarían? (curva de aprendizaje del KNN, AUC)

| % del entrenamiento | 25 | 50 | 75 | 100 |
|---|---|---|---|---|
| AUC | 0.933 | 0.948 | 0.955 | 0.960 |
