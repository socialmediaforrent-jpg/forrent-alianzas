#!/usr/bin/env python3
"""Caja <-> Render (alianzas). GET /sync/respuestas -> une; POST /sync/data; luego exporta alianzas_confirmadas.csv.
Env: /workspace/forrent/secrets/render_alianzas.env (RENDER_URL, SYNC_KEY)."""
import json,os,sys,urllib.request,subprocess
B=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,B); os.environ.pop('DATA_DIR',None); import app
e=dict(l.strip().split('=',1) for l in open('/workspace/forrent/secrets/render_alianzas.env') if '=' in l and not l.startswith('#'))
u=e['RENDER_URL'].rstrip('/'); k=e['SYNC_KEY']
def req(p,d=None):
    r=urllib.request.Request(u+p,data=None if d is None else json.dumps(d,ensure_ascii=False).encode(),headers={'X-Sync-Key':k,'Content-Type':'application/json','User-Agent':'forrent-sync'},method='GET' if d is None else 'POST')
    with urllib.request.urlopen(r,timeout=120) as f: return json.loads(f.read() or b'{}')
loc=app.load('respuestas',{})
if '--push-only' not in sys.argv: loc=app.merge(loc,req('/sync/respuestas')); app.wj('respuestas',loc)
req('/sync/data',{'oficinas':app.load('oficinas',[]),'tokens':app.load('tokens',{}),'asignacion':app.load('asignacion',{}),'inmuebles':app.load('inmuebles',{}),'respuestas':loc})
subprocess.run([sys.executable,os.path.join(B,'export_confirmadas.py')])
