#!/usr/bin/env python3
"""Arma oficinas.json + tokens.json (reparto equilibrado). Sin MLV, sin links ML, sin direcciones."""
import csv,json,os,secrets,re
B=os.path.dirname(os.path.abspath(__file__)); R='/workspace/forrent/reports/'
ASES=[tuple(x) for x in json.load(open(os.path.join(B,'asesoras_config.json')))]  # [nombre, correo]; fuera de git
EXCL=re.compile(r'h[aá]bitat|casanova|peraig',re.I)
EXCL_CORREOS=set(json.load(open(os.path.join(B,'excluir_correos.json'))))  # fuera de git
def oid(c): return re.sub(r'[^a-z0-9]+','-',c.lower()).strip('-')[:60]
of=[];seen=set()
for r in csv.DictReader(open(R+'alianza_sin_respuesta_telefonos_20261028.csv')):
    if EXCL.search(r['oficina']) or r['correo_destino'] in EXCL_CORREOS: continue
    of.append({'id':oid(r['correo_destino']),'oficina':r['oficina'],'correo':r['correo_destino'],'fecha':f"{r['fecha_envio']} {r['hora_envio']}".strip(),
      'telefono':r['telefono_oficina'],'captadores':r['captadores_y_telefonos'],'verificar':r['nota_verificar'],'respondio':False,'estado_correo':'No respondió'}); seen.add(r['correo_destino'])
for r in csv.DictReader(open(R+'control_alianza.csv')):
    if r['estado']=='positiva' and r['correo'] not in seen and not EXCL.search(r['oficina']):
        m=re.search(r'tel\.?\s*([+\d][\d\s-]{8,})',r['resumen']); 
        of.append({'id':oid(r['correo']),'oficina':r['oficina'],'correo':r['correo'],'fecha':r['fecha_envio'],'telefono':m.group(1).strip() if m else '',
          'captadores':'','verificar':'','respondio':True,'estado_correo':f"Respondió ({r['fecha_respuesta']}): interesada"})
tp=os.path.join(B,'tokens.json'); t=json.load(open(tp)) if os.path.exists(tp) else {'admin':secrets.token_urlsafe(18),'asesores':{}}
for a,_ in ASES: t['asesores'].setdefault(a,secrets.token_urlsafe(12))
asig={a:[] for a,_ in ASES}
pend=[o for o in of if not o['respondio']]; resp=[o for o in of if o['respondio']]
for i,o in enumerate(pend+resp): asig[ASES[i%len(ASES)][0]].append(o['id'])
# respeta asignación previa si ya existe (no reparte de nuevo)
ap=os.path.join(B,'asignacion.json')
if os.path.exists(ap): asig=json.load(open(ap))
json.dump(of,open(os.path.join(B,'oficinas.json'),'w'),ensure_ascii=False,indent=1)
json.dump(t,open(tp,'w'),ensure_ascii=False,indent=1); json.dump(asig,open(ap,'w'),ensure_ascii=False,indent=1)
json.dump(dict(ASES),open(os.path.join(B,'asesoras.json'),'w'),ensure_ascii=False,indent=1)
print(len(of),'oficinas;',{a:len(v) for a,v in asig.items()})
