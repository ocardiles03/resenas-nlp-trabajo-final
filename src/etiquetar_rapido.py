#!/usr/bin/env python3
"""Etiquetado rapido de sentimiento a teclado: una pagina local que muestra una resena a la vez.

Uso (desde la raiz del proyecto, con Excel CERRADO):
  .venv/bin/python -I src/etiquetar_rapido.py                                   # hoja de las 100
  .venv/bin/python -I src/etiquetar_rapido.py --hoja data/etiquetado_manual_ampliacion_200.xlsx
Abre http://127.0.0.1:8765 en el navegador. Teclas: 1 = Positivo, 2 = Negativo, 3 = Neutro, flecha izquierda = volver.
La herramienta NO etiqueta nada por su cuenta: solo guarda lo que tu eliges. Cada clic se guarda en un archivo
.json junto a la hoja (puedes cerrar y seguir luego); el boton "Guardar en Excel" escribe sentimiento_manual en el .xlsx.
Solo escribe la columna sentimiento_manual; no toca las demas columnas ni las listas desplegables.
"""
import argparse, importlib.util, json, sys, threading, warnings, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from openpyxl import load_workbook

DATA = Path(__file__).resolve().parent.parent / 'data'
VALIDOS = ('Positivo', 'Negativo', 'Neutro')
COL = 'sentimiento_manual'

PAGINA = r"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Etiquetado rapido</title>
<style>
 body{font-family:system-ui,sans-serif;max-width:860px;margin:24px auto;padding:0 16px;color:#222}
 #barra{height:8px;background:#ddd;border-radius:4px;overflow:hidden}#prog{height:100%;background:#305496;width:0}
 #info{margin:8px 0;color:#555;font-size:14px}
 h2{margin:16px 0 8px}#texto{white-space:pre-wrap;font-size:19px;line-height:1.5;background:#f7f7f7;padding:16px;border-radius:8px}
 .btns{display:flex;gap:12px;margin:20px 0}
 button{font-size:18px;padding:14px 20px;border:0;border-radius:8px;cursor:pointer;flex:1;color:#fff}
 #b1{background:#2e7d32}#b2{background:#c62828}#b3{background:#757575}
 .aux{flex:0 0 auto;background:#e0e0e0;color:#222;font-size:15px;padding:10px 14px}
 #msg{margin-top:12px;font-size:14px;color:#2e7d32} .actual{outline:4px solid #305496}
</style></head><body>
<div id="barra"><div id="prog"></div></div><div id="info"></div>
<h2 id="titulo"></h2><div id="texto"></div>
<div class="btns"><button id="b1">1 &middot; Positivo</button><button id="b2">2 &middot; Negativo</button><button id="b3">3 &middot; Neutro</button></div>
<div class="btns"><button class="aux" id="atras">&larr; Volver</button><button class="aux" id="sig">Saltar &rarr;</button>
<button class="aux" id="guardar">Guardar en Excel</button></div><div id="msg"></div>
<script>
let items=[],i=0;
const $=id=>document.getElementById(id);
async function cargar(){items=await (await fetch('/api/items')).json();i=Math.max(0,items.findIndex(x=>!x.label));if(items.every(x=>x.label))i=0;pintar();}
function pintar(){
 const hechas=items.filter(x=>x.label).length,it=items[i];
 $('prog').style.width=(100*hechas/items.length)+'%';
 $('info').textContent=`Resena ${i+1} de ${items.length}  |  etiquetadas: ${hechas}`+(it.label?`  |  tu etiqueta: ${it.label}`:'');
 $('titulo').textContent=it.titulo||'(sin titulo)';$('texto').textContent=it.texto;
 ['Positivo','Negativo','Neutro'].forEach((v,k)=>$('b'+(k+1)).classList.toggle('actual',it.label===v));
}
async function poner(v){
 const it=items[i];it.label=v;
 await fetch('/api/label',{method:'POST',body:JSON.stringify({id:it.id,label:v})});
 if(i<items.length-1)i++;else $('msg').textContent='Llegaste a la ultima. Revisa con "Volver" o pulsa "Guardar en Excel".';
 pintar();
}
function mover(d){i=Math.min(items.length-1,Math.max(0,i+d));pintar();}
$('b1').onclick=()=>poner('Positivo');$('b2').onclick=()=>poner('Negativo');$('b3').onclick=()=>poner('Neutro');
$('atras').onclick=()=>mover(-1);$('sig').onclick=()=>mover(1);
$('guardar').onclick=async()=>{const r=await (await fetch('/api/guardar',{method:'POST'})).json();$('msg').textContent=r.mensaje;};
document.addEventListener('keydown',e=>{
 if(e.key==='1')poner('Positivo');else if(e.key==='2')poner('Negativo');else if(e.key==='3')poner('Neutro');
 else if(e.key==='ArrowLeft')mover(-1);else if(e.key==='ArrowRight')mover(1);});
cargar();
</script></body></html>"""


def leer_filas(hoja):
    """[(id, titulo, texto, etiqueta_actual)] de la hoja 'Etiquetado'."""
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')   # aviso inofensivo de openpyxl sobre los desplegables de Excel (aqui solo se lee)
        ws = load_workbook(hoja, read_only=True)['Etiquetado']
    filas = list(ws.iter_rows(values_only=True))
    ix = {n: k for k, n in enumerate(filas[0])}
    return [(f[ix['id']], f[ix['titulo']] or '', f[ix['texto']] or '', f[ix[COL]] if f[ix[COL]] in VALIDOS else None)
            for f in filas[1:] if f[ix['id']]]


def guardar_en_excel(hoja, etiquetas):
    """Escribe sentimiento_manual en el .xlsx (solo esa columna). Rechaza guardar si Excel tiene el archivo abierto."""
    if (hoja.parent / ('~$' + hoja.name)).exists():
        return 'No guarde: Excel tiene el archivo abierto. Cierralo (sin guardar) y vuelve a pulsar el boton; tus clics estan a salvo.'
    spec = importlib.util.spec_from_file_location('hoja_etiquetado', Path(__file__).resolve().parent / 'hoja_etiquetado.py')
    he = importlib.util.module_from_spec(spec); sys.modules['hoja_etiquetado'] = he; spec.loader.exec_module(he)
    wb = load_workbook(hoja)
    he.restaurar_validaciones(wb)   # Excel guarda los desplegables en un formato que openpyxl descarta: se recrean
    ws = wb['Etiquetado']
    cab = [c.value for c in ws[1]]
    col_id, col_s = cab.index('id') + 1, cab.index(COL) + 1
    n = 0
    for r in range(2, ws.max_row + 1):
        v = etiquetas.get(ws.cell(r, col_id).value)
        if v in VALIDOS:
            ws.cell(r, col_s).value = v; n += 1
    wb.save(hoja)
    return f'Guardado: {n} sentimientos escritos en {hoja.name}.'


def main():
    ap = argparse.ArgumentParser(description='Etiquetado rapido de sentimiento a teclado')
    ap.add_argument('--hoja', default=str(DATA / 'etiquetado_manual_100.xlsx'))
    ap.add_argument('--puerto', type=int, default=8765)
    ap.add_argument('--no-abrir', action='store_true', help='no abre el navegador solo')
    a = ap.parse_args()
    hoja = Path(a.hoja).resolve()
    estado = hoja.with_name('.etiquetas_rapidas_' + hoja.stem + '.json')
    filas = leer_filas(hoja)
    etiquetas = {r[0]: r[3] for r in filas if r[3]}
    if estado.exists():
        etiquetas.update({k: v for k, v in json.loads(estado.read_text(encoding='utf-8')).items() if v in VALIDOS})
    lock = threading.Lock()

    class H(BaseHTTPRequestHandler):
        def _json(self, obj):
            b = json.dumps(obj).encode('utf-8')
            self.send_response(200); self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)

        def do_GET(self):
            if self.path == '/api/items':
                self._json([{'id': i, 'titulo': t, 'texto': x, 'label': etiquetas.get(i)} for i, t, x, _ in filas])
            else:
                b = PAGINA.encode('utf-8')
                self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)

        def do_POST(self):
            n = int(self.headers.get('Content-Length') or 0)
            cuerpo = json.loads(self.rfile.read(n) or b'{}')
            with lock:
                if self.path == '/api/label' and cuerpo.get('label') in VALIDOS and cuerpo.get('id') in {f[0] for f in filas}:
                    etiquetas[cuerpo['id']] = cuerpo['label']
                    estado.write_text(json.dumps(etiquetas, ensure_ascii=False), encoding='utf-8')
                    return self._json({'ok': True})
                if self.path == '/api/guardar':
                    return self._json({'mensaje': guardar_en_excel(hoja, etiquetas)})
            self._json({'ok': False})

        def log_message(self, *args):
            pass

    srv = ThreadingHTTPServer(('127.0.0.1', a.puerto), H)
    url = f'http://127.0.0.1:{a.puerto}'
    print(f'{len(filas)} resenas, {len(etiquetas)} ya etiquetadas. Abre {url}  (Ctrl+C para salir; tu progreso queda guardado)')
    if not a.no_abrir:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\nCerrado. Si no pulsaste "Guardar en Excel", tus clics siguen en', estado.name)


if __name__ == '__main__':
    main()
