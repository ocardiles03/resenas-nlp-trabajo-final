# Diccionario del lenguaje del cliente (Bundle Black Seed + Soursop Bitters, B0D4MPKGN6)

Fuente: `03_Serene-Soursop/datos/reviews_bundle_soursop_bitters_v4.xlsx` · 1271 resenas con texto · estrellas {'1': 342, '2': 102, '3': 99, '4': 120, '5': 608} · genero estimado {'No claro': 513, 'Hombre': 292, 'Mujer': 466}.

Uso interno (investigacion del cliente). Las frases de salud NO se copian tal cual a anuncios (claims). Genero = estimado por nombre/texto, aproximado. Un grupo cuenta resenas distintas; las citas son literales en ingles con ID de resena. Las calificaciones de solo estrella (~4,000) no tienen texto y no entran aqui.
Regex por reglas: puede haber falsos positivos (p. ej. «bitter» en el nombre del producto, «gas» como palabra suelta). Las columnas E1-2/E3/E4-5 = estrellas; H/M/NC = Hombre/Mujer/No claro+unisex.

## Dolor / sintoma

| Grupo | Resenas | % | 1-2★ | 3★ | 4-5★ | H | M | NC | Palabras top |
|---|---|---|---|---|---|---|---|---|---|
| estrenimiento | 15 | 1% | 2 | 1 | 12 | 2 | 4 | 9 | constipation (12), constipated (3), can't go (1) |
| hinchazon_gases | 76 | 6% | 13 | 2 | 61 | 12 | 27 | 37 | bloating (51), bloated (22), gas (9), gassy (5), bloat (3) |
| digestion_estomago | 254 | 20% | 31 | 11 | 212 | 51 | 98 | 105 | gut (98), digestion (78), stomach (68), digestive (45), bowel (25), belly (11) |
| acidez_reflujo | 8 | 1% | 3 | 0 | 5 | 1 | 2 | 5 | acid (3), heartburn (3), acid reflux (2), gerd (1), reflux (1), acidic (1) |
| diarrea_nausea | 27 | 2% | 12 | 3 | 12 | 5 | 13 | 9 | diarrhea (9), cramping (8), cramps (5), nausea (4), threw up (3), vomit (3) |
| dolor_inflamacion | 37 | 3% | 8 | 2 | 27 | 6 | 14 | 17 | pain (23), joint (6), swelling (6), pains (5), inflammation (4), inflammatory (3) |
| azucar_presion | 10 | 1% | 4 | 1 | 5 | 5 | 1 | 4 | blood pressure (6), hypertension (2), blood sugar (2), diabetic (2), diabetes (1), glucose (1) |
| energia_fatiga | 113 | 9% | 6 | 3 | 104 | 25 | 48 | 40 | energy (105), energized (17), sluggish (3), tired (3), exhausted (2), lethargic (1) |
| sueno_estres | 28 | 2% | 1 | 1 | 26 | 6 | 12 | 10 | sleep (16), sleeping (4), calm (2), stress (2), relax (1), stressful (1) |
| peso_apetito | 60 | 5% | 6 | 3 | 51 | 17 | 17 | 26 | weight (30), appetite (18), cravings (12), belly fat (4), crave (3), slims (1) |
| parasitos_detox | 115 | 9% | 14 | 8 | 93 | 25 | 48 | 42 | detox (53), cleansing (23), cleanse (19), cleans (12), flush (6), detoxing (5) |
| inmunidad | 49 | 4% | 9 | 2 | 38 | 8 | 18 | 23 | immune (37), sick (18), immunity (4), cold (4), flu (1) |
| piel_cabello | 14 | 1% | 2 | 2 | 10 | 0 | 8 | 6 | skin (12), hair (2), nails (1), rashes (1), rash (1) |
| higado_rinon_tiroides | 10 | 1% | 2 | 0 | 8 | 2 | 4 | 4 | liver (7), kidneys (2), thyroid (1), menopause (1) |
| cancer_enfermedad_grave | 3 | 0% | 1 | 0 | 2 | 0 | 2 | 1 | chemotherapy (1), chemo (1), cancer (1) |

**estrenimiento** — citas:
- (4★, No claro, `R16BKTHKJ1GJJT`) «I’m usually very constipated.»
- (5★, Mujer, `R1E6EG1EMZZ0AV`) «I’m no longer constipated or bloated, and I’ve lost my vacation weight—and then some!»
- (4★, No claro, `R1M98LAQBWSUTN`) «Stool was mostly hard like I was constipated.»
- (1★, No claro, `R281R6UMCRTQBL`) «Taste like crud and dosent do anything except cause constipation!»
- (3★, Mujer, `R30FT2G66YNYO9`) «Even though it has helped with slow digestion and constipation I would not recommend because of flavor.»
- (5★, Mujer, `R3966A87X3UZ2L`) «So taking them both together for my gut and constipation.»

**hinchazon_gases** — citas:
- (5★, Mujer, `R3M9VO38ZSQGUY`) «I’m feeling less bloated and gassy, which was my main concern when I started.»
- (5★, Mujer, `R11KA1IDHV2IJI`) «Bloat is gone but do your research first!.»
- (2★, Hombre, `R18ZK2QBSD2EI5`) «The first two bottles I had were great , I did not need to be by the bathroom but my bloating and water retention diminished and over quality felt great!»
- (4★, No claro, `R1M98LAQBWSUTN`) «When I changed and started taking it after the last meal of day, it helped some but did have gassy stomach pain by morning.»
- (4★, Mujer, `R1Q167AL1S2ZX9`) «Feeling less bloated andnow complete bowel movements.The taste is not as bad as I had been told.»
- (1★, Hombre, `R1T4G0ZC8AUTUY`) «3rd it was really efficient for gas.»

**digestion_estomago** — citas:
- (5★, No claro, `RFGQ72DNBH34O`) «I brought this for helping with my gut health and to shrink this tummy… I have been feeling like my tummy has gone down but haven’t really weighed in to see.»
- (5★, Mujer, `R1KDTTC9ZC3PL1`) «Each 16oz bottle is packed with potent, natural ingredients — no fillers or artificial junk — just pure, concentrated herbal goodness.I’ve noticed a real improvement in my digestion and overall gut comfort since I started using it daily.»
- (3★, No claro, `R21DOCMN94OUQ4`) «Effectively at cleansing the intestine just like Halleys colon tea.Its definitely overpriced.»
- (4★, No claro, `R2M5FJCDFL7FZN`) «Title: Great results for digestion, but the taste is challengingI’ve been taking this daily and have definitely noticed a real improvement in my digestion, specifically with decreased bloating and constipation.»
- (1★, No claro, `R107MGRADSCJG6`) «I remember the first 2 times I purchased, I felt amazing and had healthy and absolutely amazing bowel movements, blood pressure had dropped immensely.»
- (1★, Mujer, `R11L3MM91YO7WG`) «The true product has a strong effect on the stomach and I react to it easily.»

**acidez_reflujo** — citas:
- (4★, No claro, `R16BKTHKJ1GJJT`) «Taste is horrific and it gives me heartburn.»
- (5★, Mujer, `R17NFM226S599E`) «I had problems with ingesting, I go to bed with sour stomach n heartburn.»
- (5★, Hombre, `R18O0291GZP56B`) «I used to force down water mixed with baking soda in order to help my acid reflux, now THAT tastes bad.»
- (4★, Mujer, `R1RUIQM5ZSPS8C`) «Good if you don’t have acid issues.»
- (1★, No claro, `R2J2OKOV8JWEI5`) «It taste like stomach acid.»
- (2★, No claro, `R2MNF36YP0I1N0`) «This order of soursop bitters was packaged different and taste very acidic and spicey.»

**diarrea_nausea** — citas:
- (3★, No claro, `R2OFS0DRYR4BER`) «About 5 hours later I had excruciating cramping, nausea and headache/dizziness, I felt  unwell.»
- (3★, Mujer, `RCM405SM54N99`) «Diarrhea severe cramping.»
- (2★, Mujer, `RWQG1IPRWJRA1`) «It may cause nausea and diarrhea.»
- (5★, Mujer, `R11KA1IDHV2IJI`) «It was concerning for me because I started to get lightheaded and nauseous by the end of the week.»
- (5★, Mujer, `R1AX453MQQ1DIS`) «This product will clean you out, no your stomach willNot cramp.»
- (1★, Hombre, `R20ZPHQVV7TA4X`) «I took one spoonful of it and threw up.»

**dolor_inflamacion** — citas:
- (5★, Hombre, `R17BJYV1ED485J`) «But let me tell you i started it Thursday night and now its Tuesday the inflammation in my body has left, muscle pains decreased dramatically, more energy, less cravings for sweets, sleeping better, digestive issues left and just overall feel way better!»
- (4★, No claro, `R1M98LAQBWSUTN`) «Joint and back pains are little to none and I’ve lost 4 lbs.»
- (5★, No claro, `R2698EP6XASSYP`) «They say it's bitter but I cant say it is, the taste you will acquire over time but trust me this is a very good supplement if you are like me who have joint pains some times or feel low energy....»
- (1★, Mujer, `R7NIF7TXOMLC8`) «I had a slight allergic reaction with some abdominal pain and throat swelling the first day.»
- (4★, Mujer, `R1RUIQM5ZSPS8C`) «If you have any sort of acid issues gastritis or anything just beware that it will put you in a lot of pain.»
- (1★, No claro, `R26HK7YKAL6XHP`) «NOT WORTH THE MONEY, I GAVE IT 3 WEEKS AND I ENDED UP AT MY DRS WITH THE WORST STOMACH PAIN EVER!TRUST ME!»

**azucar_presion** — citas:
- (5★, Hombre, `R34YNOFO7ZO8D6`) «I am diabetic and have high blood pressure for now about 3 to 4 years.»
- (5★, No claro, `RWG9228WR4BHK`) «Great product.Especially for persons with diabetes and high blood pressure.I would definitely recommend.»
- (1★, No claro, `R107MGRADSCJG6`) «I remember the first 2 times I purchased, I felt amazing and had healthy and absolutely amazing bowel movements, blood pressure had dropped immensely.»
- (1★, No claro, `R1JP1JPT0EZ4UA`) «Put me into what doctor’s call hypertensive crisis.»
- (2★, Hombre, `R2PQRXIPDZ360J`) «Tastes terrible and raised my glucose level»
- (3★, Mujer, `R2U5MLHAA5DESC`) «Not Hypertension friendly!!!»

**energia_fatiga** — citas:
- (5★, Mujer, `R1RCQU21QA83NY`) «I also feel more energized throughout the day — not a jittery kind of energy, but steady and clear.Another plus is the clean ingredient list.»
- (5★, No claro, `R24WLFT3HVSO65`) «Also My energy levels elevated, i no longer feel exhausted after sleep.»
- (3★, No claro, `R13WHEOQDZOTJ2`) «As for the product itself it’s been two weeks, haven’t really noticed energy yet..»
- (2★, Hombre, `R1AR7JJ8K1V5HJ`) «It only been 4 days and I feel and see no difference as of 9/18/2025, also no energy level or effectiveness.»
- (4★, Mujer, `R1IREEPS06D9XZ`) «Not only it has help me with shedding pounds, my inmune system is stronger, i sleep better and have more energy.»
- (4★, No claro, `R1VA0NXE58W9GK`) «This product gives me energy i can't speak for any one else but im satisfied with the product and will order more when i run out»

**sueno_estres** — citas:
- (5★, Mujer, `RCSQCUX1QARJF`) «It did relax me and I went right to sleep.»
- (5★, Hombre, `R17BJYV1ED485J`) «But let me tell you i started it Thursday night and now its Tuesday the inflammation in my body has left, muscle pains decreased dramatically, more energy, less cravings for sweets, sleeping better, digestive issues left and just overall feel way better!»
- (4★, Hombre, `R1G6CVESYKE71Y`) «I like  it sleep  better  at night»
- (4★, Mujer, `R1IREEPS06D9XZ`) «Not only it has help me with shedding pounds, my inmune system is stronger, i sleep better and have more energy.»
- (2★, No claro, `R1L5NF6U9I39NY`) «This plastic bottle was very nasty glass bottle has a more calmer taste won’t purchase this again.»
- (3★, No claro, `R2OFS0DRYR4BER`) «I didn’t get any sleep that night.»

**peso_apetito** — citas:
- (5★, No claro, `RXB5PWS66H71Z`) «I lost 6 lbs so far in the two weeks I’ve taken it, and my appetite has decreased.»
- (5★, Mujer, `R11KA1IDHV2IJI`) «I noticed a change in my eating habits and cravings.»
- (1★, No claro, `R16JMVVIHC5W4N`) «For the taste alone these are costly but if they remove brain fog, I lose some weight ( belly) fat and can feel significantly better it might be worth the cost.»
- (4★, No claro, `R1M98LAQBWSUTN`) «It did suppress my appetite and when I ate, you immediately have to go to the bathroom.»
- (4★, Hombre, `R23M40IVPTFAY9`) «I mix these with the v8 beet and Ginger..I noticed i use the toilet more and losing some weight»
- (3★, No claro, `R2M49ZS6ON23N4`) «I am dropping weight so much, and our daughter looks this up.»

**parasitos_detox** — citas:
- (5★, No claro, `R2005LX42SUCB9`) «I noticed a big improvement in digestion and overall mood.No side effects so far, which is a plus for me.Perfect for anyone starting a cleanse or detox journey.»
- (5★, Mujer, `R2HRMDMF6W42HQ`) «BUT the benefit of gut health and release of mucus, toxins, parasites are AMAZING and necessary!»
- (2★, No claro, `RBWP067Y4YEGI`) «Did some research and this product can cause hives, due to the cleansing detox nature.»
- (3★, No claro, `R13WHEOQDZOTJ2`) «but it is detoxing mildly, and I feel a little better with movement and going up/down the stairs.»
- (2★, No claro, `R1C05DW1VXUC4E`) «And ofcourse it didn’t detox my body like before at all.»
- (4★, Mujer, `R1UPQ2T6Q2FKRJ`) «Would not waste my money on the detox or the black seed bitters.»

**inmunidad** — citas:
- (5★, Mujer, `R381HK7HUT70YF`) «It’s also been a fantastic boost for my immune system, especially during cold and flu season.What I love most is the clean energy and clarity I feel throughout the day.»
- (1★, No claro, `RFNJF93B192X5`) «On day two of consuming I was terribly sick and since ceasing to use have not been sick.»
- (5★, Hombre, `R12BLPFYQ0HE0`) «I mainly bought this for the premium black seed oil because there has been a buzz about how good and effective it is for not just the immune system but for many vital organs.»
- (1★, Mujer, `R14FI616KDCUV0`) «I got deathly sick on the 1st tsp 🤢🤮 I didn't even want to give it 1 star but the app made me»
- (4★, No claro, `R16BKTHKJ1GJJT`) «Been taking this on and off because I have been sick and was on several medications and for women during there menstruation have to be off (makes your flow heavy).»
- (4★, No claro, `R1HE9PRZNSOJD3`) «This bundle has been great for digestion and even helped curb my cold symptoms.»

**piel_cabello** — citas:
- (5★, Mujer, `R1SSCQ8YLJ9V4S`) «Also it's caused my skin to clear up and my skin is glowing.»
- (5★, Mujer, `RGBZ5HFXGQ53L`) «It has cleared my skin and made my nails stronger.»
- (3★, No claro, `R368RSOAH6O3KK`) «It has no effect on my skin whatsoever.»
- (2★, No claro, `RBWP067Y4YEGI`) «After taking this, I'm getting rashes and hives.»
- (1★, No claro, `RGW5BAGTK84V8`) «Additionally, consider applying coconut oil to your skin after showering.»
- (4★, No claro, `RMO02A4BEGF19`) «I’m 12lbs down and my skin cleared up.»

**higado_rinon_tiroides** — citas:
- (5★, Mujer, `RMMKM7FZVFKTM`) «Helps my Liver and Kidneys.»
- (1★, No claro, `R106BXGAPOGDPN`) «After taking it my liver is messed up.»
- (5★, Hombre, `R25NOZCZIKVGQK`) «That awful taste is what jumpstarts the bile production in your liver and gets your gut juices flowing.»
- (2★, No claro, `R3DZPLATF855OE`) «Read ingredients if you have thyroid issues.»

**cancer_enfermedad_grave** — citas:
- (1★, No claro, `R1FCE5E2ZQGVP7`) «I canceled my order Please don’t send this product to me, My Doctor said this stuff will interfere with my with my chemotherapy treatment, Don’t send please.»
- (5★, Mujer, `R1JL2USPZ6YBLR`) «Still waiting to see if it affected my cancer positively»
- (4★, Mujer, `R24UH1NZ6V62B8`) «I am hoping it will help with chemo side effects (stomach issues).»

## Resultado

| Grupo | Resenas | % | 1-2★ | 3★ | 4-5★ | H | M | NC | Palabras top |
|---|---|---|---|---|---|---|---|---|---|
| funciona_mejora | 489 | 38% | 90 | 37 | 362 | 99 | 182 | 208 | works (107), work (105), results (102), it works (90), help (48), effective (47) |
| sin_efecto | 60 | 5% | 38 | 10 | 12 | 11 | 19 | 30 | waste of money (8), no change (7), no side effects (6), did not work (6), no results (5), no difference (4) |
| efecto_adverso | 42 | 3% | 24 | 2 | 16 | 8 | 20 | 14 | side effects (17), reaction (11), diarrhea (9), allergic (7), hives (4), made me sick (3) |
| efecto_rapido_fuerte | 159 | 13% | 50 | 11 | 98 | 24 | 65 | 70 | strong (61), first time (32), bathroom (32), powerful (24), bowel movements (10), poop (8) |
| recompra_recomienda | 157 | 12% | 46 | 8 | 103 | 31 | 69 | 57 | recommend (79), recommended (23), my second (16), buying again (6), buy again (6), staple (6) |

**funciona_mejora** — citas:
- (3★, Mujer, `R11VG69B2F9A81`) «It only works if you do the recommended dosage, this has not once sent me to the restroom, but I do believe it does work on your gut I have seen results there, but for that I think I'll switch over to the pill form, the taste is not worth it!!!»
- (5★, Hombre, `R306FQAHTROTUA`) «I’d keep taking it I feel like I need to take a shot glass sometime it works but kind of doesn’t work all the way and makes me feel sick and I will do some enemas to help - but I like the product wish it was more in amount .»
- (4★, Mujer, `RJWZAAP65JL2J`) «product so far has help improve my gut health and, sleep help.»
- (1★, Mujer, `R12S1EKP9GYRSR`) «is horrible it doesn’t work at all, it tastes horrible, i wasted my money on something that doesn’t work»
- (5★, Mujer, `R17NFM226S599E`) «It’s work so I ordered some more , because it works for me I gave my sister some.»
- (4★, Mujer, `R1Q167AL1S2ZX9`) «It works and it helps with my gut issues.»

**sin_efecto** — citas:
- (1★, Mujer, `RKYAC0Q5Z6T3O`) «no change in bowel movements, no weight loss, no change in energy.»
- (3★, Mujer, `R13RGRTTUA97X3`) «I just bought it again and it seems about half the strength for more money and not as effective as before.»
- (2★, Hombre, `R1AR7JJ8K1V5HJ`) «It only been 4 days and I feel and see no difference as of 9/18/2025, also no energy level or effectiveness.»
- (1★, No claro, `R1M1AWQL64YMJZ`) «Forfeiting $50 for a product that does not provide results is bad for business.»
- (2★, No claro, `R1NO5ZEEKQ24ON`) «did not work as expected.»
- (5★, Mujer, `R1SSCQ8YLJ9V4S`) «All the ingredients are natural and I've felt no side effects the past few days.»

**efecto_adverso** — citas:
- (5★, No claro, `R1Q69PFSCTNUOL`) «I scaled back but I still had the allergic reaction.»
- (1★, No claro, `R22RNT81W62DA5`) «It’s taste awful, and I’m experiencing an allergic reaction.»
- (1★, Mujer, `R7NIF7TXOMLC8`) «Allergic Reaction intolerable taste won’t allow return.»
- (2★, No claro, `RBWP067Y4YEGI`) «After taking this, I'm getting rashes and hives.»
- (4★, No claro, `R1J2KX72T8E97W`) «Product has side effects.»
- (4★, No claro, `R1M98LAQBWSUTN`) «It’s not something I want to continue to take over a long period of time due to the side effects.»

**efecto_rapido_fuerte** — citas:
- (3★, Mujer, `R13RGRTTUA97X3`) «The first time I bought this product it was really good and worked immediately.»
- (4★, No claro, `R1M98LAQBWSUTN`) «It did suppress my appetite and when I ate, you immediately have to go to the bathroom.»
- (2★, No claro, `R1WW8YO7YBI6UC`) «I started taking right away, nothing happened not even sending me to the bathroom.»
- (5★, Mujer, `R318OWFLH0XN5A`) «all I can say about this product is OMG  it works wonders I feel super light after the first time in the bathroom and lighter each and every time after that thank you TK for your vision I'm on my second set I wouldn't ran out of this product»
- (3★, No claro, `R35E271HWUUKH9`) «After the first day, my digestion improved, I was going to the bathroom regularly, and I felt noticeably less bloated.»
- (1★, Hombre, `R370YHWYV6J2ET`) «First time I noted the strong herbal taste to it.»

**recompra_recomienda** — citas:
- (5★, Mujer, `R21GDNL863NTTP`) «Whether I’m winding down in the evening or just taking a moment for myself, it’s become a go-to.Overall, I would definitely recommend SourSop Serene Herbs to anyone looking for a natural way to support their wellness.»
- (3★, Mujer, `R11VG69B2F9A81`) «It only works if you do the recommended dosage, this has not once sent me to the restroom, but I do believe it does work on your gut I have seen results there, but for that I think I'll switch over to the pill form, the taste is not worth it!!!»
- (5★, Mujer, `R137C06DH0MKVX`) «I would recommend it to anyone looking»
- (3★, Mujer, `R13RGRTTUA97X3`) «I would totally recommend it if they went back to the original recipe and strength.»
- (2★, Mujer, `R1GT94XBFZ8NMH`) «This is my second time purchasing this brand of soursop bitters.»
- (4★, No claro, `R1HE9PRZNSOJD3`) «However, the taste is pretty unpleasant, so I’d recommend having something to chew on or a hard candy ready afterward.»

## Objecion: sabor

| Grupo | Resenas | % | 1-2★ | 3★ | 4-5★ | H | M | NC | Palabras top |
|---|---|---|---|---|---|---|---|---|---|
| amargo | 230 | 18% | 82 | 17 | 131 | 43 | 88 | 99 | bitter (225), sour (51), bitterness (21), harsh (7), bite (4), bittersthe (1) |
| sabor_malo_asco | 173 | 14% | 83 | 19 | 71 | 22 | 74 | 77 | horrible (68), nasty (46), awful (36), terrible (26), disgusting (21), gag (8) |
| sabor_aceptable | 111 | 9% | 16 | 4 | 91 | 24 | 39 | 48 | mix it with (18), taste good (16), get used to (13), tolerable (13), pleasant (9), mixed with (9) |
| sabor_general | 499 | 39% | 198 | 50 | 251 | 93 | 188 | 218 | taste (642), tastes (87), tasted (40), flavor (34), tasting (26), smell (15) |
| natural_de_hierbas | 181 | 14% | 44 | 9 | 128 | 37 | 69 | 75 | herbs (103), natural (82), ingredients (60), herbal (57), organic (31), herb (10) |

**amargo** — citas:
- (5★, Hombre, `RPG83LQBVSUBJ`) «The Sour Sap Bitter is bitter but good for your gut health while the Black Seed Bitters provides a boost of antioxidants and anti-inflammatory properties.»
- (1★, Hombre, `R12M4BGNFCXT6P`) «Received my Sour Sop Bitters & Black Seed Oil and the sour sop bottle had leaked everywhere inside the package….low 1/4 of my bottle and these aren’t cheap….buyer beware»
- (2★, Hombre, `R24WRWHGBFQTAF`) «The product is supposed to be bitter—this batch isn’t bitter at all, and the soursop version is much thicker than before.»
- (4★, No claro, `R2A29K9A9C3UN2`) «I like sour and bitter taste so this may be most people’s complaint or adjustment.»
- (3★, No claro, `R2EJ7RG17S1S5M`) «It's not sour as advertised - just a very harsh chemical taste.»
- (2★, Mujer, `R2LCQLQFCAQWIJ`) «The soursop bitter supposed to be bitter..»

**sabor_malo_asco** — citas:
- (1★, Mujer, `R12S1EKP9GYRSR`) «is horrible it doesn’t work at all, it tastes horrible, i wasted my money on something that doesn’t work»
- (1★, Hombre, `R1L4XFJ7JCHTI3`) «I gulped it down and prepared for the gag from the awful, thick, bitter taste.»
- (5★, Mujer, `RP23ZXGG3333Q`) «The taste is Horrible, I mean just Horrible, but I’m still taking it every day.»
- (4★, No claro, `R10MOY6JWPCZ2N`) «Works wonderfully, but tastes awful.»
- (4★, Mujer, `R12AW1BHMN2R0N`) «The taste is very horrible I haven't felt any changes but I have noticed I've been going to the bathroom a lot.»
- (3★, No claro, `R13SKFPQ098TPA`) «I'm going to give it 3 stars for now because I haven't had it/used to long enough to notice results but THIS STUFF TASTES DISGUSTING!!!!!!!»

**sabor_aceptable** — citas:
- (5★, Hombre, `R25NOZCZIKVGQK`) «I either mix it into a powder greens to slam in the morning or mix it with honey and lemon with hot water in the evening.»
- (4★, No claro, `R2B3RM1UXAMMY`) «The taste is not pleasant, you definitely should mix it with some type of juice»
- (1★, Mujer, `R3T0CUP5XWUB3K`) «I did have to mix it with some juice but omg it’s still nasty barely was able to drink it after mixing it with the juice.»
- (5★, Mujer, `R72V97UHEHL0K`) «Doesn't taste good but you get used to it.»
- (3★, Hombre, `R1BB4OHU7TN1CD`) «It says to mix it with something like juice ….»
- (1★, No claro, `R1C2JKTHB3SEWR`) «I tried mixing it in strong beverages to mask the taste…nothing worked!»

**sabor_general** — citas:
- (5★, Mujer, `R20L6WTNY3AJEG`) «The taste is not gonna be sweet it’s bitters it’s supposed to have a bitter taste.You will get used to the taste its worth the purchase.»
- (1★, Mujer, `R10CQ3Q3XWQYRY`) «It tastes like water because I ordered it before knowing what it was supposed to taste like.»
- (3★, No claro, `R13WHEOQDZOTJ2`) «The taste is less then desirable but I follow up with a lime to get the taste off my tongue.»
- (5★, Hombre, `R17DGZCRB2XRM9`) «The taste is fruity and taste good!»
- (1★, No claro, `R18D1QV80RZ9H0`) «Smells like cinnamon and that’s not what the bitters are suppose to smell like more  earthy if that make sense»
- (2★, No claro, `R1HTKT3OPCUR3R`) «It’s time I stop telling people to buy this product because a few things have changed about it.- Now comes in plastic bottles.- The soursop bitters had a peppery taste and I couldn’t smell soursop at all.»

**natural_de_hierbas** — citas:
- (5★, No claro, `R34JMZNBUT4VMJ`) «The ingredients are organic and natural, which gives me peace of mind, and the blend tastes exactly like a real herbal tonic should — earthy and powerful.»
- (5★, Mujer, `R1557WTKQTKENN`) «I also like that it’s made from all-natural herbs—ones I can read and understand.If you’re looking for a gentle, natural detox or just want to support your digestion, I’d definitely recommend giving it a try.»
- (3★, No claro, `R35E271HWUUKH9`) «I purchased the Serene Herbs Soursop Bitters Liquid & Black Seed Bundle (Organic Herbal Guanabana for Digestive Support & Immune Health, 16 oz each).I’ll be honest—the taste is awful.»
- (1★, No claro, `R1M1AWQL64YMJZ`) «The formula/ingredient list has changed per Serene Herbs Customer Service.»
- (1★, No claro, `R1VQ7Q786IQFG2`) «Also i dont remember but either soursop or blackseeds bitters, one of the ingredients was “camphor” which doesn’t make sense as it’s a toxic substance.Make sure you understand all the ingredients listed on the label before drinking this.»
- (4★, No claro, `R2M5FJCDFL7FZN`) «It works well and I appreciate the organic ingredients.»

## Objecion: precio

| Grupo | Resenas | % | 1-2★ | 3★ | 4-5★ | H | M | NC | Palabras top |
|---|---|---|---|---|---|---|---|---|---|
| caro | 29 | 2% | 13 | 6 | 10 | 8 | 8 | 13 | expensive (14), too much (8), cost (7), overpriced (6), pricey (1), costly (1) |
| buen_valor | 88 | 7% | 19 | 4 | 65 | 23 | 27 | 38 | worth it (29), worth the (24), cheaper (8), cheap (8), value (7), great value (7) |
| precio_general | 116 | 9% | 65 | 9 | 42 | 34 | 35 | 47 | money (75), price (35), deal (9), paid (8), $50 (5), pay (3) |

**caro** — citas:
- (1★, No claro, `R16JMVVIHC5W4N`) «For the taste alone these are costly but if they remove brain fog, I lose some weight ( belly) fat and can feel significantly better it might be worth the cost.»
- (3★, Hombre, `R2Y5460KXWXR4Y`) «We've had no problems from this bundle except for the one we just received and they cost too much for me not to get what I paid for.»
- (1★, Mujer, `RFX8J6NKNQJZ5`) «This stuff cost too much for them to not be transparent.»
- (5★, Hombre, `R13SHJEHBB07PB`) «One of the best fines I’ve found us for very overpriced.»
- (3★, No claro, `R1E5VM2JREPP7A`) «It’s too expensive when you can get it cheaper elsewhere $44 for two bottles»
- (2★, Mujer, `R1GT94XBFZ8NMH`) «As for the black seed bitters this was my first time trying it so I can't say too much about it other than it looks watered down also.»

**buen_valor** — citas:
- (1★, No claro, `R107MGRADSCJG6`) «Finding the quality of a lot of products has dropped a great deal.»
- (3★, Mujer, `R11VG69B2F9A81`) «It only works if you do the recommended dosage, this has not once sent me to the restroom, but I do believe it does work on your gut I have seen results there, but for that I think I'll switch over to the pill form, the taste is not worth it!!!»
- (1★, Hombre, `R12M4BGNFCXT6P`) «Received my Sour Sop Bitters & Black Seed Oil and the sour sop bottle had leaked everywhere inside the package….low 1/4 of my bottle and these aren’t cheap….buyer beware»
- (3★, Mujer, `R13RGRTTUA97X3`) «Not worth the price anymore.»
- (5★, No claro, `R14MVRJRGL3VCC`) «This is a great health good value for you money ease to take»
- (5★, Mujer, `R1557WTKQTKENN`) «The taste is definitely bitter (no surprise there), but the results make it worth it.Within a few days, I felt lighter, less bloated, and had more energy later in the day.»

**precio_general** — citas:
- (1★, No claro, `R16JMVVIHC5W4N`) «The price should be $25 each in my opinion between $40-50 so this better work,»
- (5★, Mujer, `R1E6EG1EMZZ0AV`) «That’s an excellent price compared to buying directly from the vendor’s website, where the combo is $69.99 plus tax and shipping (around $72 total).»
- (5★, Mujer, `R17NFM226S599E`) «A friend told me about Soursop I brought the tea good.Then I brought 2 n1 deal Soursop bitter, $64.19 good buy.»
- (1★, Hombre, `R2ICCOI1H8S7M0`) «Unfortunately my attempt to buy more from their website ended with my losing $125.99 on a 6 bottle deal that never arrived.»
- (3★, No claro, `R2PVKI3FKO0QTK`) «I paid Almost $50 for something that I do not even know if they’re the same ingredients.»
- (3★, Mujer, `R13RGRTTUA97X3`) «Not worth the price anymore.»

## Objecion: envio / envase / autenticidad

| Grupo | Resenas | % | 1-2★ | 3★ | 4-5★ | H | M | NC | Palabras top |
|---|---|---|---|---|---|---|---|---|---|
| envio_tardio | 136 | 11% | 71 | 15 | 50 | 32 | 48 | 56 | package (48), packaging (32), arrived (26), delivery (21), shipping (20), delivered (17) |
| danado_derrame | 75 | 6% | 58 | 6 | 11 | 11 | 25 | 39 | broken (51), damaged (22), leaking (17), damage (7), broke (6), leaked (6) |
| sello_envase | 324 | 25% | 217 | 36 | 71 | 61 | 116 | 147 | bottles (295), plastic (249), bottle (227), sealed (16), seal (10), lid (5) |
| autenticidad_diluido | 177 | 14% | 127 | 18 | 32 | 39 | 56 | 82 | watered (85), not the same (60), formula (36), real (25), scam (19), diluted (13) |

**envio_tardio** — citas:
- (5★, No claro, `R10FEXAE4OSKDS`) «Other than a delay in arrival delivered asd described.»
- (3★, No claro, `R11H0IY4BHM1CS`) «I love these bitters but they are often delayed weeks even months when shipping so be aware!»
- (5★, Mujer, `R137C06DH0MKVX`) «It arrived well packaged and is easy to add to my daily routine.»
- (1★, Mujer, `R18YI0BS4MMUVJ`) «I ordered from the official website, and the product arrived in glass bottles with professional packaging.»
- (4★, Mujer, `R1A5THOZMLISVF`) «Companies need to be aware that glass packaging is a healthier packaging.»
- (3★, Mujer, `R1AQBMDOBS7Y8A`) «I just got my 3rd bottle today after 2 shipping delays, took me almost a month to get them.»

**danado_derrame** — citas:
- (1★, Mujer, `R2N8P9N1HP4MT1`) «Product was damaged beyond use both bottles were crushed so it showed up as a box of crushed glass»
- (1★, Hombre, `R17OPHC2L4TZXW`) «Damaged package- broken glass bottle.»
- (4★, Mujer, `R5AZ4K956PDDF`) «Product came leaking with damaged cork.»
- (5★, No claro, `RDF347N87S7NG`) «The package arrived on time and was well-sealed, with no leaks or damage to the bottles.The instructions on the label were easy to follow.»
- (3★, No claro, `R13WHEOQDZOTJ2`) «I didn’t see any evidence of leakage in the box so I’m assuming it was sent to the warehouse this way.»
- (5★, Mujer, `R13WHFCA5AGK29`) «If you don't have a doppler, I suggest you get one because it will spill out trying to put it in a tablespoon.I would also say, just take it immediately.»

**sello_envase** — citas:
- (5★, Mujer, `RCSQCUX1QARJF`) «The plastic sealed bottles came in a plastic sealed wrap , which I think is great, to avoid possible breakage due to mishandling and noticeable tampering.»
- (1★, No claro, `R1V49TOU9X1QHB`) «My first order was in glass bottles and had a seal around the top and when you opened  The plastic seal there was another seal that you had to remove.»
- (5★, No claro, `R2T1ULGGRBE10`) «I see that they now come in plastic bottles...They still say the same amount, but the plastic bottles are slightly smaller than the glass bottles were.»
- (1★, No claro, `RYGQO31V7PW0M`) «I received my most recent order of the soursop and black seed bitters 2 bottle bundle set and was very disappointed that they have change the glass bottles to plastic bottles which is not good for anyones health a glass bottle is best.»
- (3★, No claro, `R11AUZZIH3E45F`) «Sadly, I’ll have to try out different companies that use glass bottles and not the toxic plastic bottles.»
- (3★, No claro, `R13WHEOQDZOTJ2`) «My order arrived and my soursop bottle had a plastic safety seal and my black seed botttle did not.»

**autenticidad_diluido** — citas:
- (1★, No claro, `R2XGD19ZKN40BT`) «This is not the same product that if been getting,it came in plastic instead of glass and was not the same formula I’ve been using.»
- (1★, No claro, `R18D1QV80RZ9H0`) «I bought this once and it came in a glass bottle and now it came in a plastic bottle and it’s not the real bitters Fake !!!!!»
- (2★, Hombre, `R18ZK2QBSD2EI5`) «The second bottle I used the product seemed to be quite a bit watered down and diluted.»
- (3★, Mujer, `R1AQBMDOBS7Y8A`) «It taste like watered down coffee, I’m feeling like this batch is not the same quality as the other two.»
- (2★, No claro, `R1ATCOLIX423R4`) «Watered down not the original formula.»
- (5★, Mujer, `R1F8GXWLKOJC37`) «This stuff is a Scam not the same thing.»

## Objecion: reembolso y servicio

| Grupo | Resenas | % | 1-2★ | 3★ | 4-5★ | H | M | NC | Palabras top |
|---|---|---|---|---|---|---|---|---|---|
| reembolso_devolucion | 83 | 7% | 74 | 7 | 2 | 14 | 27 | 42 | refund (36), return (35), replacement (9), returned (8), canceled (7), money back (3) |
| servicio_cliente | 53 | 4% | 8 | 4 | 41 | 8 | 21 | 24 | support (45), customer service (11), complaints (6), complaint (1), complaining (1), complain (1) |

**reembolso_devolucion** — citas:
- (3★, No claro, `R13WHEOQDZOTJ2`) «I was gonna return the blackseed until I found out this item cannot be returned because it’s considered a perishable.»
- (2★, No claro, `R2IXH22O9HKIZN`) «I use the product daily however I’m returning my product and canceling my subscription and tryin other brands based on their ingredient list and source of the product.»
- (1★, No claro, `R2VBJ9KOBBMW62`) «And this product is not eligible for return/refund, fifty bucks wasted VERY Disappointed :(.»
- (3★, No claro, `R3PKXYRSSVWTMW`) «I already open it but truly wish I didn't so I could have return for a full refund.»
- (1★, No claro, `R3V3N2TTAJET0X`) «This is not the bitters it's the worst  thing I have ever taste no bitters at all in this thing I will return and want my money back this is junk  who made this thing  this does not taste like the last purchase»
- (2★, No claro, `R577F8DFO4ICK`) «I am not happy about it as you can not return them or get a refund.»

**servicio_cliente** — citas:
- (3★, No claro, `RBMCCBK6FMT92`) «Changing to 3 stars because of their customer service support.This product is in plastic bottles.»
- (1★, Mujer, `R105SDHGTS6G3I`) «Love this product but their customer service is the worst.»
- (5★, Hombre, `R12BLPFYQ0HE0`) «Both support immune health and function plus digestive health as well as many other benefits.»
- (5★, Mujer, `R1557WTKQTKENN`) «I also like that it’s made from all-natural herbs—ones I can read and understand.If you’re looking for a gentle, natural detox or just want to support your digestion, I’d definitely recommend giving it a try.»
- (2★, No claro, `R1AM5WTXRITYEO`) «Customer service satisfaction has to be #1 if you want to keep up and I was almost going to be a subscription service customer.»
- (1★, No claro, `R1M1AWQL64YMJZ`) «The formula/ingredient list has changed per Serene Herbs Customer Service.»

## Lenguaje emocional

| Grupo | Resenas | % | 1-2★ | 3★ | 4-5★ | H | M | NC | Palabras top |
|---|---|---|---|---|---|---|---|---|---|
| gratitud_amor | 398 | 31% | 46 | 14 | 338 | 91 | 153 | 154 | great (240), love (114), amazing (49), happy (35), excellent (30), thank (26) |
| sorpresa_asombro | 41 | 3% | 7 | 2 | 32 | 5 | 19 | 17 | impressed (10), wow (7), surprise (6), surprised (6), magic (5), surprisingly (4) |
| alivio | 69 | 5% | 7 | 5 | 57 | 13 | 29 | 27 | lighter (17), feel light (13), no more (10), relief (8), finally (6), so much better (6) |
| enojo_decepcion | 228 | 18% | 149 | 24 | 55 | 36 | 86 | 106 | horrible (68), disappointed (62), waste (36), awful (36), worst (31), terrible (26) |
| miedo_duda_escepticismo | 110 | 9% | 48 | 16 | 46 | 26 | 36 | 48 | expected (38), not sure (19), hope (13), hopefully (8), doubt (6), expecting (6) |
| confianza_fe | 50 | 4% | 22 | 6 | 22 | 8 | 18 | 24 | believe (18), honestly (15), trust (12), honest (7), legit (2), testimonials (1) |
| cambio_vida | 14 | 1% | 2 | 1 | 11 | 2 | 5 | 7 | my health (6), life changing (3), saved my (2), game changer (2), changed my life (1), gamechanger (1) |

**gratitud_amor** — citas:
- (5★, Mujer, `R2IWCE8P8BSUN4`) «Love and love and love love love»
- (5★, No claro, `RYLMDK80DMMIW`) «love love love this brand of sour all bitters it is amazing .I use it everyday.»
- (1★, No claro, `R107MGRADSCJG6`) «I remember the first 2 times I purchased, I felt amazing and had healthy and absolutely amazing bowel movements, blood pressure had dropped immensely.»
- (2★, Hombre, `R18ZK2QBSD2EI5`) «The first two bottles I had were great , I did not need to be by the bathroom but my bloating and water retention diminished and over quality felt great!»
- (3★, Mujer, `R1XGKAKMXV3MSR`) «I love this product but I don’t like the new plastic bottles they come in, I loved the glass bottles because it’s better for the quality of the product.»
- (2★, No claro, `R21ZEK1A8A1AQE`) «I wanted to love this bundle because the ingredients and potential health benefits sound great, but this review is based strictly on taste—not effectiveness.»

**sorpresa_asombro** — citas:
- (4★, No claro, `R7HSF5T8V88XW`) «Nothing.....nothing changes the taste in my mouth as i sip everything around me  wow......wow......wow.....»
- (5★, No claro, `R3TROSRL1XQ38H`) «It might just surprise you the way it surprised me.»
- (5★, Mujer, `R11KA1IDHV2IJI`) «My husband ordered this for me and wow did it take all the bloating away.»
- (1★, No claro, `R11WJ4BX5WIO2Q`) «Wow I know the cost of things changes but plastic bottles are not a good idea.»
- (1★, No claro, `R1AFYBM6XFD3C0`) «I really wanted to be impressed with this but I’m not.»
- (2★, No claro, `R1WPOSLUBPZNAH`) «Wow the Taste of the Soursop!!»

**alivio** — citas:
- (5★, Mujer, `R3R3D19II32B5T`) «No more bloating and my digestion is finally back on track.»
- (5★, Mujer, `R11KA1IDHV2IJI`) «I will still use this product as it is effective and made me feel a lot lighter and more energy.»
- (2★, Mujer, `R1GT94XBFZ8NMH`) «Immediately I noticed that it is lighter in color.»
- (1★, No claro, `R1U41PS55Z74AV`) «If you need some relief just do what I did, buy some prune juice, it cheaper.»
- (3★, No claro, `R21DOCMN94OUQ4`) «Its a colon cleaner but very overpriced.»
- (1★, Mujer, `R22RSUDWYU9466`) «We actually went from going daily or every other day to once no more than 2x's in that week and a half.»

**enojo_decepcion** — citas:
- (1★, Mujer, `R12S1EKP9GYRSR`) «is horrible it doesn’t work at all, it tastes horrible, i wasted my money on something that doesn’t work»
- (1★, Mujer, `R1V8S4F21FDYJI`) «Subject: Serious Concern About Product Quality and ConsistencyI am extremely disappointed and frustrated with a recent purchase.»
- (2★, Mujer, `R3H7MIEQ6SX4HG`) «Subject: Serious Concern About Product Quality and ConsistencyI am extremely disappointed and frustrated with a recent purchase.»
- (3★, No claro, `RBMCCBK6FMT92`) «Disappointing, it wouldn’t be as disappointing if they would of given me a refund.»
- (5★, Mujer, `RP23ZXGG3333Q`) «The taste is Horrible, I mean just Horrible, but I’m still taking it every day.»
- (4★, No claro, `R10MOY6JWPCZ2N`) «Works wonderfully, but tastes awful.»

**miedo_duda_escepticismo** — citas:
- (5★, Hombre, `R34YNOFO7ZO8D6`) «I am also perimenopausal.I really had hopes that this product would help me with belly fat.When I got the product and started drinking it, I was expecting to taste to be a lot worse than what it was based on the descriptions from people it was not undrinkable.»
- (2★, Hombre, `R18ZK2QBSD2EI5`) «I hope this specific company is able to reel back in and fulfill to the highest quality .»
- (3★, Mujer, `R1AQBMDOBS7Y8A`) «I’m worried now though that the quality has gone down since they have become so popular.»
- (5★, Mujer, `R1EMQZ5510AW2R`) «Hopefully it slims her down a little»
- (4★, Mujer, `R1FIU9YIIZ8CMK`) «Not sure why they gave me plastic when it's supposed to be a healthy product company.»
- (1★, Mujer, `R1G4QGJOSXCI5P`) «Hopefully the next one tastes better.»

**confianza_fe** — citas:
- (5★, No claro, `R32NV2I90UB9TT`) «I’m going to be completely honest it tastes bitter but I believe it’s working.»
- (3★, No claro, `RPBACQ7JLGAX5`) «I honestly can't believe how people can drink this.»
- (3★, Mujer, `R11VG69B2F9A81`) «It only works if you do the recommended dosage, this has not once sent me to the restroom, but I do believe it does work on your gut I have seen results there, but for that I think I'll switch over to the pill form, the taste is not worth it!!!»
- (5★, Mujer, `R1557WTKQTKENN`) «Serene Herbal Bitters – My Honest Thoughts.»
- (1★, Mujer, `R1PEIUO3NAKCER`) «I’m not getting the same results and I believe this seller is watering down the original product.»
- (2★, Mujer, `R1U4SI9PLED3UV`) «I tried mixing it in different juices and drinks to make it work, and it just wont relent.I don’t know if I believe any of these people that have been taking it for so long.»

**cambio_vida** — citas:
- (5★, No claro, `R19R3Y5MDZWO1H`) «Help manage my health, specially my weight...very comfortable with the results 🙏»
- (1★, No claro, `R1FCE5E2ZQGVP7`) «Product not benefiting to my health, To many ingredients, where is sour sop and Black seed.»
- (4★, Mujer, `R1FIU9YIIZ8CMK`) «I saved my glass bottles and poured the ones in plastic in the glass.»
- (5★, No claro, `R1QACRRBBLFGJY`) «This is by far the best thing I have done for my self and my health!»
- (1★, No claro, `R228CSHC73IM0O`) «Due to the fact that I'm talking this product to improve my health,the plastic bottles is a complete disaster for me .»
- (3★, No claro, `R2P9UGCP68H35H`) «The first one changed my life and health is doing better  I was a Anemia all my life but now it’s gone.»

## Frases frecuentes (2-3 palabras) por banda de estrellas

_Resenas distintas que contienen la frase (minimo 3)._

**1-2 estrellas:** plastic bottles (59); watered down (54); glass bottles (45); plastic bottle (41); don t (32); black seed (31); glass bottle (30); taste like (24); didn t (24); soursop bitters (23); came in plastic (22); doesn t (19); black seed bitters (17); seed bitters (17); same product (16); first time (16); ordered this product (14); t work (13); tastes like (13); sour sop (13); won t (12); came in glass (12); first order (12); serene herbs (11); do not buy (11); bitter taste (11); taste the same (10); couldn t (9); t taste (9); both bottles (9)

**3 estrellas:** glass bottles (12); don t (11); plastic bottles (11); watered down (9); black seed (9); soursop bitters (8); didn t (6); glass bottle (5); serene herbs (4); taste the same (4); first time (4); know how (4); product works (4); horrible taste (4); see any (4); love this product (4); black seed bitters (4); seed bitters (4); sour sap (3); do believe (3); tik tok (3); try it again (3); doesn t (3); tastes like (3); all over (3); plastic bottle (3); another review (3); see results (3); after days (3); past the taste (3)

**4-5 estrellas:** black seed (78); soursop bitters (60); great product (53); serene herbs (51); gut health (36); good product (35); black seed bitters (35); seed bitters (35); herbs soursop (29); more energy (27); serene herbs soursop (27); highly recommend (26); works great (23); herbs soursop bitters (22); don t (22); really works (21); bitter taste (20); these products (17); few days (17); soursop and black (16); works well (15); doesn t (15); digestive system (15); seed bundle (15); black seed bundle (15); non gmo (15); immune system (15); product works (14); taste good (14); ve been using (14)

## Palabras que separan elogio de queja (adaptado de la Clase 11, EAFIT)

% de la palabra/pareja en resenas 4-5★ frente a 1-2★, normalizado por 10,000 palabras de cada grupo (50 % = no separa). Minimo 15 apariciones en 10 resenas. Sin lematizar. 3★ excluidas.

**Hacia la queja (1-2★):** return (0%, 0+/32-); disappointed (1%, 1+/52-); plastic bottle (2%, 1+/46-); refund (2%, 1+/30-); company (2%, 1+/27-); original (3%, 1+/25-); broken (3%, 2+/48-); same product (4%, 1+/17-); disappointing (4%, 1+/16-); top (4%, 1+/15-); not buy (4%, 1+/15-); batch (4%, 1+/15-); scam (5%, 1+/14-); watered (5%, 5+/67-); watered down (5%, 5+/64-); plastic (5%, 16+/196-); plastic bottles (6%, 7+/78-); taste like (7%, 3+/29-); box (7%, 2+/19-); damaged (7%, 2+/18-); glass bottle (7%, 4+/35-); worst (7%, 3+/26-); leaking (8%, 2+/15-); color (10%, 2+/13-); seller (10%, 2+/13-); waste (10%, 4+/26-); purchased (10%, 6+/36-); different (10%, 14+/82-); totally (11%, 3+/17-); instead (11%, 3+/17-); same (11%, 19+/106-); formula (11%, 5+/27-); website (11%, 3+/16-); amazon (12%, 8+/42-); items (12%, 4+/21-); off (12%, 7+/36-); glass (12%, 28+/142-); disgusting (12%, 3+/15-); changed (12%, 8+/39-); tasted (12%, 6+/29-)

**Hacia el elogio (4-5★):** really works (100%, 22+/0-); sleep (100%, 15+/0-); wellness (100%, 33+/0-); energized (100%, 17+/0-); immune system (100%, 16+/0-); cleanse (100%, 17+/0-); seed bundle (100%, 15+/0-); gmo (100%, 15+/0-); throughout (100%, 15+/0-); powerful (100%, 24+/0-); works great (100%, 25+/0-); taste good (100%, 15+/0-); more energy (100%, 28+/0-); non gmo (100%, 15+/0-); works well (100%, 16+/0-); easy (100%, 27+/0-); immune (96%, 34+/1-); excellent (95%, 29+/1-); clean (95%, 29+/1-); great product (95%, 58+/2-); overall (95%, 56+/2-); routine (95%, 27+/1-); eat (95%, 27+/1-); highly recommend (95%, 26+/1-); works (95%, 211+/8-); boost (94%, 25+/1-); yes (94%, 25+/1-); digestion (94%, 73+/3-); gut health (94%, 46+/2-); awesome (94%, 22+/1-); digestive (93%, 41+/2-); few days (92%, 18+/1-); natural (92%, 68+/4-); support (92%, 33+/2-); energy (92%, 96+/6-); best (92%, 47+/3-); detox (92%, 47+/3-); issues (91%, 30+/2-); job (91%, 15+/1-); product works (91%, 15+/1-)
