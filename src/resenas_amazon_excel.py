#!/usr/bin/env python3
"""Convierte las resenas de Amazon (JSON descargado del navegador) en un Excel
con una fila por resena: estrellas, fecha, genero estimado, emocion, temas de
salud y zona de EE.UU. mencionada en el texto.

Uso:
  python3 resenas_amazon_excel.py resenas.json salida.xlsx
Requiere: pip install openpyxl gender-guesser vaderSentiment
Uso interno (analisis de clientes); no copiar frases de salud a anuncios.
"""
import json
import re
import sys
from pathlib import Path

import gender_guesser.detector as gender
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

DICC = json.loads((Path(__file__).parent / "diccionario_salud_resenas.json").read_text())

MESES = {m: i + 1 for i, m in enumerate(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
     "septiembre", "octubre", "noviembre", "diciembre"])}
MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"])}

# Census Bureau: estado -> (region, division)
ESTADOS = {
    "Connecticut": ("Noreste", "Nueva Inglaterra"), "Maine": ("Noreste", "Nueva Inglaterra"),
    "Massachusetts": ("Noreste", "Nueva Inglaterra"), "New Hampshire": ("Noreste", "Nueva Inglaterra"),
    "Rhode Island": ("Noreste", "Nueva Inglaterra"), "Vermont": ("Noreste", "Nueva Inglaterra"),
    "New Jersey": ("Noreste", "Atlantico Medio"), "New York": ("Noreste", "Atlantico Medio"),
    "Pennsylvania": ("Noreste", "Atlantico Medio"),
    "Illinois": ("Medio Oeste", "Este Norte Central"), "Indiana": ("Medio Oeste", "Este Norte Central"),
    "Michigan": ("Medio Oeste", "Este Norte Central"), "Ohio": ("Medio Oeste", "Este Norte Central"),
    "Wisconsin": ("Medio Oeste", "Este Norte Central"),
    "Iowa": ("Medio Oeste", "Oeste Norte Central"), "Kansas": ("Medio Oeste", "Oeste Norte Central"),
    "Minnesota": ("Medio Oeste", "Oeste Norte Central"), "Missouri": ("Medio Oeste", "Oeste Norte Central"),
    "Nebraska": ("Medio Oeste", "Oeste Norte Central"), "North Dakota": ("Medio Oeste", "Oeste Norte Central"),
    "South Dakota": ("Medio Oeste", "Oeste Norte Central"),
    "Delaware": ("Sur", "Atlantico Sur"), "Florida": ("Sur", "Atlantico Sur"), "Georgia": ("Sur", "Atlantico Sur"),
    "Maryland": ("Sur", "Atlantico Sur"), "North Carolina": ("Sur", "Atlantico Sur"),
    "South Carolina": ("Sur", "Atlantico Sur"), "Virginia": ("Sur", "Atlantico Sur"),
    "West Virginia": ("Sur", "Atlantico Sur"), "Washington DC": ("Sur", "Atlantico Sur"),
    "Alabama": ("Sur", "Este Sur Central"), "Kentucky": ("Sur", "Este Sur Central"),
    "Mississippi": ("Sur", "Este Sur Central"), "Tennessee": ("Sur", "Este Sur Central"),
    "Arkansas": ("Sur", "Oeste Sur Central"), "Louisiana": ("Sur", "Oeste Sur Central"),
    "Oklahoma": ("Sur", "Oeste Sur Central"), "Texas": ("Sur", "Oeste Sur Central"),
    "Arizona": ("Oeste", "Montana"), "Colorado": ("Oeste", "Montana"), "Idaho": ("Oeste", "Montana"),
    "Montana": ("Oeste", "Montana"), "Nevada": ("Oeste", "Montana"), "New Mexico": ("Oeste", "Montana"),
    "Utah": ("Oeste", "Montana"), "Wyoming": ("Oeste", "Montana"),
    "Alaska": ("Oeste", "Pacifico"), "California": ("Oeste", "Pacifico"), "Hawaii": ("Oeste", "Pacifico"),
    "Oregon": ("Oeste", "Pacifico"), "Washington State": ("Oeste", "Pacifico"),
}
ABREV = {
    "CT": "Connecticut", "ME": "Maine", "MA": "Massachusetts", "NH": "New Hampshire", "RI": "Rhode Island",
    "VT": "Vermont", "NJ": "New Jersey", "NY": "New York", "PA": "Pennsylvania", "IL": "Illinois",
    "IN": "Indiana", "MI": "Michigan", "OH": "Ohio", "WI": "Wisconsin", "IA": "Iowa", "KS": "Kansas",
    "MN": "Minnesota", "MO": "Missouri", "NE": "Nebraska", "ND": "North Dakota", "SD": "South Dakota",
    "DE": "Delaware", "FL": "Florida", "GA": "Georgia", "MD": "Maryland", "NC": "North Carolina",
    "SC": "South Carolina", "VA": "Virginia", "WV": "West Virginia", "AL": "Alabama", "KY": "Kentucky",
    "MS": "Mississippi", "TN": "Tennessee", "AR": "Arkansas", "LA": "Louisiana", "OK": "Oklahoma",
    "TX": "Texas", "AZ": "Arizona", "CO": "Colorado", "ID": "Idaho", "MT": "Montana", "NV": "Nevada",
    "NM": "New Mexico", "UT": "Utah", "WY": "Wyoming", "AK": "Alaska", "CA": "California", "HI": "Hawaii",
    "OR": "Oregon", "WA": "Washington State",
}
CIUDADES = {
    "new york city": "New York", "nyc": "New York", "brooklyn": "New York", "bronx": "New York",
    "harlem": "New York", "long island": "New York", "buffalo": "New York", "los angeles": "California",
    "san francisco": "California", "bay area": "California", "san diego": "California",
    "sacramento": "California", "houston": "Texas", "dallas": "Texas", "austin": "Texas",
    "san antonio": "Texas", "miami": "Florida", "orlando": "Florida", "tampa": "Florida",
    "jacksonville": "Florida", "atlanta": "Georgia", "chicago": "Illinois", "detroit": "Michigan",
    "philadelphia": "Pennsylvania", "philly": "Pennsylvania", "pittsburgh": "Pennsylvania",
    "boston": "Massachusetts", "baltimore": "Maryland", "charlotte": "North Carolina",
    "raleigh": "North Carolina", "nashville": "Tennessee", "memphis": "Tennessee",
    "new orleans": "Louisiana", "las vegas": "Nevada", "phoenix": "Arizona", "seattle": "Washington State",
    "portland": "Oregon", "denver": "Colorado", "minneapolis": "Minnesota", "st. louis": "Missouri",
    "kansas city": "Missouri", "cleveland": "Ohio", "columbus": "Ohio", "cincinnati": "Ohio",
    "milwaukee": "Wisconsin", "indianapolis": "Indiana", "louisville": "Kentucky",
    "birmingham": "Alabama", "washington dc": "Washington DC", "d.c.": "Washington DC",
    "new jersey": "New Jersey",
}
REGIONES_VAGAS = {"the south": "Sur", "down south": "Sur", "the midwest": "Medio Oeste",
                  "the east coast": "Noreste", "east coast": "Noreste", "west coast": "Oeste",
                  "the northeast": "Noreste", "new england": "Noreste", "the west": "Oeste"}

vader = SentimentIntensityAnalyzer()
gd = gender.Detector(case_sensitive=False)


def buscar(frases, texto):
    return [f for f in frases if re.search(r"(?<![a-z])" + re.escape(f) + r"(?![a-z])", texto)]


def parsear_fecha(s):
    """'Calificado en Estados Unidos el 21 de octubre de 2026' -> (2026-10-21, 'Estados Unidos')."""
    m = re.search(r"en (.+?) el (\d{1,2}) de (\w+) de (\d{4})", s)
    if m and m.group(3).lower() in MESES:
        return f"{m.group(4)}-{MESES[m.group(3).lower()]:02d}-{int(m.group(2)):02d}", m.group(1)
    m = re.search(r"in (?:the )?(.+?) on (\w+) (\d{1,2}), (\d{4})", s)
    if m and m.group(2).lower() in MONTHS:
        return f"{m.group(4)}-{MONTHS[m.group(2).lower()]:02d}-{int(m.group(3)):02d}", m.group(1)
    return "", ""


def votos(s):
    m = re.search(r"(\d[\d,]*)", s)
    if m:
        return int(m.group(1).replace(",", ""))
    return 1 if re.search(r"\b(una|one) (persona|person)", s, re.I) else 0


def genero(nombre, texto):
    t = texto.lower()
    if buscar(DICC["genero_pistas"]["mujer"], t):
        return "Mujer", "texto"
    if buscar(DICC["genero_pistas"]["hombre"], t):
        return "Hombre", "texto"
    primero = re.sub(r"[^A-Za-z]", " ", nombre).split()
    if not primero:
        return "No claro", ""
    r = gd.get_gender(primero[0].capitalize())
    if r in ("male", "mostly_male"):
        return "Hombre", "nombre"
    if r in ("female", "mostly_female"):
        return "Mujer", "nombre"
    return "No claro", ""


def zona(texto):
    t = texto.lower()
    estados = []
    for est in ESTADOS:
        if re.search(r"(?<![a-z])" + est.lower() + r"(?![a-z])", t) and est not in ("Washington State",):
            estados.append(est)
    for ab, est in ABREV.items():
        if re.search(r",\s*" + ab + r"\b", texto):
            estados.append(est)
    for c, est in CIUDADES.items():
        if re.search(r"(?<![a-z])" + re.escape(c) + r"(?![a-z])", t):
            estados.append(est)
    for v, reg in REGIONES_VAGAS.items():
        if v in t:
            return "", reg, "", v
    estados = list(dict.fromkeys(estados))
    if estados:
        est = estados[0]
        reg, div = ESTADOS[est]
        return est, reg, div, "texto"
    return "", "", "", ""


def analizar(r):
    texto = f"{r.get('titulo','')}. {r.get('texto','')}"
    t = texto.lower()
    fecha, pais = parsear_fecha(r.get("fecha", ""))
    gen, gen_fuente = genero(r.get("nombre", ""), texto)
    comp = vader.polarity_scores(texto)["compound"]
    sent = "Positivo" if comp >= 0.35 else "Negativo" if comp <= -0.2 else "Neutral/mixto"
    emo = {k: len(buscar(v, t)) for k, v in DICC["emociones"].items()}
    emo = [k for k, v in sorted(emo.items(), key=lambda x: -x[1]) if v > 0][:2]
    temas = [k for k, v in DICC["temas"].items() if buscar(v, t)]
    claves = sorted({w for v in DICC["temas"].values() for w in buscar(v, t)})
    res = "sin_efecto" if buscar(DICC["resultado"]["sin_efecto"], t) else \
        "efecto_adverso" if buscar(DICC["resultado"]["efecto_adverso"], t) else \
        "mejora" if buscar(DICC["resultado"]["mejora"], t) else ""
    est, reg, div, fuente_z = zona(texto)
    est_num = float(re.match(r"[\d.]+", r.get("estrellas", "0")).group(0)) if re.match(r"[\d.]+", r.get("estrellas", "")) else None
    return {
        "ID": r["id"], "Nombre": r.get("nombre", ""), "Estrellas": est_num, "Fecha": fecha, "Pais": pais,
        "Titulo": r.get("titulo", ""), "Texto": r.get("texto", ""),
        "Compra verificada": "Si" if r.get("verificada") else "No", "Votos utiles": votos(r.get("util", "")),
        "Variante": r.get("variante", ""), "Fotos": r.get("fotos", 0),
        "Genero (estimado)": gen, "Genero fuente": gen_fuente,
        "Sentimiento": sent, "Sentimiento (VADER)": round(comp, 2), "Emocion (diccionario)": ", ".join(emo),
        "Temas de salud": ", ".join(temas), "Palabras de salud": ", ".join(claves),
        "Resultado reportado": res,
        "Estado mencionado": est, "Region": reg, "Division": div, "Zona fuente": fuente_z,
        "Perfil": r.get("perfil", ""), "Enlace": f"https://www.amazon.com/gp/customer-reviews/{r['id']}",
    }


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    datos = json.loads(Path(sys.argv[1]).read_text())
    revs = list(datos.values()) if isinstance(datos, dict) else datos
    filas = [analizar(r) for r in revs]
    filas.sort(key=lambda f: f["Fecha"], reverse=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "Resenas"
    cols = list(filas[0].keys())
    ws.append(cols)
    for f in filas:
        ws.append([f[c] for c in cols])
    head = PatternFill("solid", fgColor="1F4E78")
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = head
        c.alignment = Alignment(vertical="center", wrap_text=True)
    anchos = {"Texto": 80, "Titulo": 30, "Nombre": 22, "Temas de salud": 28, "Palabras de salud": 28,
              "Enlace": 28, "Variante": 26, "Emocion (diccionario)": 24}
    for i, c in enumerate(cols, 1):
        ws.column_dimensions[get_column_letter(i)].width = anchos.get(c, 14)
    ti = cols.index("Texto") + 1
    for row in ws.iter_rows(min_row=2):
        row[ti - 1].alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions

    res = wb.create_sheet("Resumen")
    def conteo(titulo, clave, split=False):
        res.append([titulo])
        res.cell(res.max_row, 1).font = Font(bold=True)
        cnt = {}
        for f in filas:
            vals = [v.strip() for v in str(f[clave]).split(",")] if split else [f[clave]]
            for v in vals:
                if v not in ("", None):
                    cnt[v] = cnt.get(v, 0) + 1
        for k, v in sorted(cnt.items(), key=lambda x: -x[1]):
            res.append([k, v, round(100 * v / len(filas), 1)])
        res.append([])
    res.append(["Total de resenas", len(filas)])
    res.append([])
    conteo("Estrellas", "Estrellas")
    conteo("Genero estimado", "Genero (estimado)")
    conteo("Sentimiento", "Sentimiento")
    conteo("Emociones", "Emocion (diccionario)", True)
    conteo("Temas de salud", "Temas de salud", True)
    conteo("Resultado reportado", "Resultado reportado")
    conteo("Region mencionada", "Region")
    conteo("Variante", "Variante")
    res.column_dimensions["A"].width = 42

    d = wb.create_sheet("Diccionario salud")
    d.append(["Tema", "Palabras"])
    for k, v in DICC["temas"].items():
        d.append([k, ", ".join(v)])
    d.column_dimensions["A"].width = 26
    d.column_dimensions["B"].width = 120

    wb.save(sys.argv[2])
    print(f"{len(filas)} resenas -> {sys.argv[2]}")


if __name__ == "__main__":
    main()
