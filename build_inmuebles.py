#!/usr/bin/env python3
"""inmuebles.json: oficina(id) -> inmuebles que nos interesan (sin MLV, sin links ML, sin dirección).
MLV por correo: control_alianza.csv. MLV->Wasi: scripts/mlv_wasi_map.py; MLV->Rex: ml_alianza_rex_list.json;
respaldo: cobertura_alianza_ml_624_20261027.csv. Excluye pausadas (ml_pausadas_panel_20261028.txt).
Links: solo los que ya existen en archivos de /workspace/forrent (no se construyen)."""
import csv,json,re,sys,os,glob,subprocess
F='/workspace/forrent/'; R=F+'reports/'; sys.path.insert(0,F+'scripts'); import mlv_wasi_map as M
B=os.path.dirname(os.path.abspath(__file__))
paus={'MLV-'+x for x in open(R+'ml_pausadas_panel_20261028.txt').read().split()}
wmap=M.load_mlv_to_wasi(); rex=json.load(open(R+'ml_alianza_rex_list.json'))['published']
cob={r['mlv']:r for r in csv.DictReader(open(R+'cobertura_alianza_ml_624_20261027.csv'))}
wdet={}
for f in [F+'wasi_aliados_90dias_20261026.csv',F+'wasi_aliados_activos_180dias_20261026.csv']:
    for r in csv.DictReader(open(f)): wdet[r['codigo']]=r
# links existentes
L=subprocess.run("grep -rhoE 'https?://(www\\.)?(info\\.wasi\\.co|rexup\\.net)/[^ \"'\"'\"',)<>\\\\]*' --include=*.csv --include=*.md --include=*.json --include=*.txt /workspace/forrent",shell=True,capture_output=True,text=True).stdout.split()
wl,rl={},{}
for u in set(L):
    m=re.search(r'info\.wasi\.co/.*?/(\d{6,})$',u) or re.search(r'info\.wasi\.co/(\d{6,})$',u)
    if m: wl.setdefault(m.group(1),[]).append(u)
    m=re.search(r'cod_inmueble=(\d+)$',u)
    if m: rl.setdefault(m.group(1),[]).append(u)
def pick_w(c):
    us=wl.get(c,[]); return (sorted([u for u in us if '/x/' not in u]) or sorted(us) or [''])[0]
def pick_r(c):
    us=rl.get(c,[]); return (sorted([u for u in us if 'ver_inmueble.php' in u]) or sorted(us) or [''])[0]
def oid(c): return re.sub(r'[^a-z0-9]+','-',c.lower()).strip('-')[:60]
def money(p):
    try: return f"US$ {float(p):,.0f}".replace(',','.')
    except Exception: return ''
NOADDR=re.compile(r'\b(calle|av\.?|avenida|edif(icio)?|torre|piso|apto\.?\s*\d|casa\s*n|qta|quinta|res(idencias)?\.?\s+[A-Z])',re.I)
out={};sinlink=[]
for r in csv.DictReader(open(R+'control_alianza.csv')):
    lst=[]
    for mlv in r['mlvs'].split():
        if mlv in paus: continue
        c=cob.get(mlv,{}); it={}
        if mlv in rex or c.get('fuente')=='Rex':
            x=rex.get(mlv,{}); cod=x.get('codigo_rex') or c.get('codigo','')
            it={'fuente':'Rex','codigo':cod,'titulo':c.get('titulo') or x.get('label',''),'precio':money(x.get('precio_usd')),'zona':'',
                'link':x.get('link_rex') if x.get('link_rex') and 'mercadolibre' not in x['link_rex'] else pick_r(cod)}
        else:
            w=wmap.get(mlv,{}); cod=w.get('wasi_id') or (c.get('codigo') if c.get('fuente')=='Wasi' else '')
            if not cod: it={'fuente':'','codigo':'','titulo':c.get('titulo',''),'precio':'','zona':'','link':''}
            else:
                d=wdet.get(cod,{}); it={'fuente':'Wasi','codigo':cod,'titulo':c.get('titulo') or d.get('titulo') or w.get('wasi_title',''),
                   'zona':', '.join(x for x in (d.get('zona'),d.get('municipio')) if x),'precio':money(d.get('precio')),'link':pick_w(cod)}
        if not it['zona']:
            m=re.search(r'\b[Ee]n ([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ. ]+?)(?:\s+\d|,|$)',it['titulo'])
            if m: it['zona']=m.group(1).strip()
        if NOADDR.search(it['titulo']): it['titulo']=re.split(NOADDR,it['titulo'])[0].strip(' ,-') or 'Inmueble'
        if not it['link']: sinlink.append((r['oficina'],it['fuente'],it['codigo'],mlv))
        lst.append(it)
    if lst: out[oid(r['correo'])]=lst
json.dump(out,open(os.path.join(B,'inmuebles.json'),'w'),ensure_ascii=False,indent=1)
with open(R+'alianzas_inmuebles_sin_link_20261028.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['oficina','fuente','codigo','mlv_interno']); w.writerows(sinlink)
print('oficinas con inmuebles:',len(out),'inmuebles:',sum(map(len,out.values())),'sin link:',len(sinlink))
