# KNN sobre las reseñas de Amazon (método de la Clase 12, EAFIT)

Fuente: Excel v4, 1271 reseñas con texto; 4-5★ = positiva, 1-2★ = negativa, 3★ = tibia (fuera de entrenamiento). Entrenamiento 937 · prueba 235 · positivas en entrenamiento 62.1 % (= punto de corte). Texto lematizado (spaCy en_core_web_sm) y sin palabras vacías, conservando no/not/never.

## 1. ¿Cuántos vecinos?

| k | 1 | 5 | 15 | 25 | 51 | 101 | 201 | 401 |
|---|---|---|---|---|---|---|---|---|
| AUC (CV 5) | 0.814 | 0.931 | 0.951 | 0.951 | 0.949 | 0.949 | 0.946 | 0.925 |

Mejor k = **25**.

## 2. ¿Qué tan bien lee? (reseñas de prueba con la nota tapada)

| Modelo | Exactitud | Positivas reconocidas | Negativas reconocidas | AUC | Errores |
|---|---|---|---|---|---|
| Regla ingenua (todas positivas) | 0.621 | 146/146 (1.00) | 0/89 (0.00) | 0.500 | 89 |
| KNN, corte 0.5 | 0.911 | 140/146 (0.96) | 74/89 (0.83) | 0.968 | 21 |
| KNN, corte 0.621 | 0.915 | 132/146 (0.90) | 83/89 (0.93) | 0.968 | 20 |
| Balanza aprendida (lexico_cliente.py) | 0.847 | 122/146 (0.84) | 77/89 (0.87) | 0.939 | 36 |

## 3. ¿Cuáles son quejas? (leer primero las de arriba)

Al azar, 37.9 % de las reseñas de prueba es queja.

| Decil | Reseñas | Quejas | % queja | Elevación | % de todas las quejas (acum.) |
|---|---|---|---|---|---|
| 1 | 24 | 23 | 96 % | 2.53 | 26 % |
| 2 | 23 | 23 | 100 % | 2.64 | 52 % |
| 3 | 24 | 22 | 92 % | 2.42 | 76 % |
| 4 | 23 | 12 | 52 % | 1.38 | 90 % |
| 5 | 24 | 5 | 21 % | 0.55 | 96 % |
| 6 | 23 | 3 | 13 % | 0.34 | 99 % |
| 7 | 24 | 1 | 4 % | 0.11 | 100 % |
| 8 | 23 | 0 | 0 % | 0.00 | 100 % |
| 9 | 24 | 0 | 0 % | 0.00 | 100 % |
| 10 | 23 | 0 | 0 % | 0.00 | 100 % |

## 4. Las reseñas de 3 estrellas (tibias), leídas por KNN

De 99 reseñas de 3★: 29 se leen positivas y 70 negativas.

## 5. Dime con quién andas (ejemplos con vecinos)

**Queja bien leída** · `R22RSUDWYU9466` · 1★ · prob. positiva 0.36 (corte 0.62) — «No increase in movement, but decrease. taste is not as expected. I do not recommend this to anyone.. I purchased this for the first time, It was nothing like what I what was advertised. It was not hard to smell nor all that bad with taste.. My son and I took it for about a week and there was no incr»

- parecido 0.25 · 5★ · `RQ3NUH9WQJ9S2` — «Don't go anywhere on your first time taking it. Ot do have a bad taste to it but it works»
- parecido 0.24 · 1★ · `R2RCXJKLP3COOL` — «Arrived broken with no returns. I received the bottle completely shattered, with the box soaked in the product. Would not recommend if there is no way to get re»
- parecido 0.24 · 1★ · `R1AFYBM6XFD3C0` — «Not For Me. I’ve taken a generic soursop bitters from Amazon that gave me far better results than this brand. I really wanted to be impressed with this but I’m »

**Queja bien leída** · `R1VNSKG813FXPT` · 1★ · prob. positiva 0.12 (corte 0.62) — «Disappointed. This was weak. The bitters weren’t “BITTERING”. I couldn’t taste anything. It was as if it was watered down. My husband is Caribbean and said, “WHAT IS DIS”. Meaning, it has no taste. I’m extremely disappointed.»

- parecido 0.31 · 2★ · `R1ATCOLIX423R4` — «Watered down not the original formula. I’ve ordered this product before on TikTok shop and once on Amazon and never had a problem but with this batch right here»
- parecido 0.29 · 1★ · `RXNXUL8EKNSD8` — «Made me vomit.. I never had anything that tasted that badly. Instant vomit. Couldn't get a refund»
- parecido 0.27 · 1★ · `R25H1WJONXNH93` — «New formula is no longer bitter. So disappointed. They’ve changed the formula and it’s so watered down that it’s no longer bitter. Also disappointed that they s»

**Queja que KNN leyó como positiva (error)** · `R2ICCOI1H8S7M0` · 1★ · prob. positiva 0.72 (corte 0.62) — «Serene Herbs is a rip off.. This product worked great! Unfortunately my attempt to buy more from their website ended with my losing $125.99 on a 6 bottle deal that never arrived. Every attempt to track the order has lead to a screen that says “waiting for details”. Every attempt to contact Serene He»

- parecido 0.52 · 5★ · `R3OPH211OR61DN` — «Serene Herbs. We love them!»
- parecido 0.50 · 5★ · `R2MPX06C4C173U` — «Serene herb. Great product»
- parecido 0.46 · 5★ · `RC5P2WAE1YMQA` — «Serene herbs. Good product»

**Queja que KNN leyó como positiva (error)** · `R3LO8O13LTSVPK` · 1★ · prob. positiva 0.64 (corte 0.62) — «Smashed to bits in the shipping box due to sloppy inadequate packing.. Great product but terrible customer service.  Arrived shattered.  No live person to speak with.»

- parecido 0.36 · 1★ · `R1TX6IDZ9GBA0Y` — «Taste and customer service. Customer service is terrible placed and order over a month ago and still haven't received it. Taste is bitter but not the worst thin»
- parecido 0.33 · 1★ · `R105SDHGTS6G3I` — «Worst Company Ever. Love this product but their customer service is the worst.  Takes over a week to get it packed to ship.  It’s been well over 2 weeks now the»
- parecido 0.32 · 5★ · `R31FBA93VV4J5T` — «Great product. Arrived  on time»

**Queja que KNN leyó como positiva (error)** · `RBWP067Y4YEGI` · 2★ · prob. positiva 0.88 (corte 0.62) — «Getting hives....... After taking this, I'm getting rashes and hives. Did some research and this product can cause hives, due to the cleansing detox nature.»

- parecido 0.24 · 4★ · `R1R67T5LU0S32W` — «Be at home after taking!. The taste was horrible! But it did clear me out! It's only getting a four because of the taste. It's the worstest thing I've ever tast»
- parecido 0.24 · 5★ · `R1PRKFDBIF8O51` — «Energy booster. I regained my energy after taking a dose. Thank you!»
- parecido 0.23 · 5★ · `R2PVLV1FE3N6XT` — «Detox. it works»

## Cómo usarlo

- `knn_resenas_v4.csv` ordena las 1,271 reseñas de más negativa a más positiva (probabilidad fuera de muestra; las de entrenamiento se leen por validación cruzada, sin ver su propia nota). Sirve para leer primero las quejas.
- Probabilidad de positiva = parte de los k vecinos que es 4-5★. El corte es la proporción de positivas del entrenamiento, no 0.5.
- Cuidado: hay una sola marca/producto, así que KNN puede reconocer el tema (plástico, sello, sabor) y no solo la opinión; no hay prueba por producto como en la Clase 12.
