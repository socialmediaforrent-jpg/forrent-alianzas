#!/usr/bin/env python3
"""For Rent · Sistema de Alianzas para Punta de Cierre. Un link por asesora; cada oficina es una tarjeta.
Local: datos en esta carpeta. Render: DATA_DIR + /sync/data y /sync/respuestas (igual que estatus_web)."""
import json,os,re,hmac,html,threading,datetime,urllib.parse
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
BASE=os.path.dirname(os.path.abspath(__file__)); DATA_DIR=os.environ.get('DATA_DIR'); REMOTE=bool(DATA_DIR)
SYNC_KEY=os.environ.get('SYNC_KEY',''); PORT=int(os.environ.get('PORT',18797)); LOCK=threading.Lock()
D=DATA_DIR or BASE
if REMOTE: os.makedirs(D,exist_ok=True)
F={k:os.path.join(D,k+'.json') for k in ('oficinas','tokens','asignacion','respuestas','inmuebles')}
CCS=datetime.timezone(datetime.timedelta(hours=-4))  # Caracas
def load(k,d):
    try: return json.load(open(F[k]))
    except Exception: return d
def wj(k,o):
    tmp=F[k]+'.tmp'; json.dump(o,open(tmp,'w'),ensure_ascii=False,indent=1); os.replace(tmp,F[k])
def merge(a,b):
    o=dict(a)
    for k,v in b.items():
        if k not in o or (v.get('at') or '')>(o[k].get('at') or ''): o[k]=v
    return o
e=html.escape
def tel(s): return re.sub(r'[^\d+]','',s or '')
def card(o,r,tok):
    r=r or {}; ok=' ok' if r.get('contactado') else ''
    ph=f"<a class=btn href='tel:{tel(o['telefono'])}'>📞 Llamar {e(o['telefono'])}</a>" if o.get('telefono') else "<span class=sin>Sin teléfono de oficina</span>"
    cap=''.join(f"<div class=cap>👤 {e(n.split(':')[0])} <a href='tel:{tel(n.split(':',1)[1])}'>{e(n.split(':',1)[1].strip())}</a></div>" for n in (o.get('captadores') or '').split(' | ') if ':' in n)
    ver=f"<div class=ver>⚠ Verificar número: {e(o['verificar'])}</div>" if o.get('verificar') else ''
    def rad(n,v): return ''.join(f"<label><input type=radio name={n} value={x} {'checked' if r.get(n)==x else ''}> {x.capitalize()}</label>" for x in ('si','no')).replace('Si','Sí')
    inm=load('inmuebles',{}).get(o['id'],[])
    def li(x):
        lk=f" · <a href='{e(x['link'])}' target=_blank rel=noopener>Ver ficha</a>" if x.get('link') else " · <i>(sin link)</i>"
        cod=f"{x['fuente']} {e(x['codigo'])}" if x.get('codigo') else 'sin código'
        meta=' · '.join(v for v in (e(x.get('zona','')),e(x.get('precio',''))) if v)
        return f"<li>{e(x['titulo'] or 'Inmueble')}{(' — '+meta) if meta else ''}<br><small>{cod}{lk}</small></li>"
    inms=f"<details class=inm><summary>🏠 Inmuebles que nos interesan ({len(inm)})</summary><ul>{''.join(map(li,inm))}</ul></details>" if inm else ''
    cls='resp' if o['respondio'] else 'noresp'
    return f"""<div class='card{ok}'><div class=n>{e(o['oficina'])}</div>
<div class=meta>✉ {e(o['correo'])} · Enviado: {e(o['fecha'])} (hora Caracas)</div><div class='est {cls}'>{e(o['estado_correo'])}</div>
<div>{ph}</div>{cap}{ver}{inms}
<form onsubmit="return g(this,'{o['id']}')"><div class=row><b>¿Contactado?</b> {rad('contactado','')}</div>
<div class=row><b>¿Aceptó la alianza?</b> {rad('acepto','')}</div>
<input name=persona placeholder='Nombre de la persona con la que habló' value="{e(r.get('persona',''))}">
<textarea name=nota placeholder='Nota'>{e(r.get('nota',''))}</textarea><button>Guardar</button> <span class=msg>{('Último guardado: '+e(r['at'][:16].replace('T',' '))) if r.get('at') else ''}</span></form></div>"""
CSS="""body{font-family:system-ui,sans-serif;background:#f4f4f4;margin:0}header{background:#fff;padding:12px 16px;border-bottom:3px solid #E76108;display:flex;gap:12px;align-items:center}
header img{height:48px}h1{font-size:18px;margin:0}main{max-width:760px;margin:auto;padding:12px}.card{background:#fff;border-radius:10px;padding:14px;margin:12px 0;border-left:6px solid #ccc}
.card.ok{border-left-color:#16a34a}.n{font-weight:700;font-size:17px}.meta{color:#555;font-size:13px;margin:4px 0}.est{display:inline-block;font-size:12px;padding:2px 8px;border-radius:10px;margin:4px 0}
.resp{background:#dcfce7;color:#166534}.noresp{background:#fee2e2;color:#991b1b}.btn{display:inline-block;background:#E76108;color:#fff;padding:9px 14px;border-radius:8px;text-decoration:none;margin:6px 0;font-weight:600}
.cap{font-size:14px;margin:2px 0}.ver{color:#b45309;font-size:13px}.sin{color:#888;font-size:13px}.inm{margin:8px 0;font-size:14px}.inm li{margin:4px 0}.inm summary{cursor:pointer;font-weight:600}.row{margin:8px 0}.row label{margin-left:12px}
input[name=persona],textarea{width:100%;box-sizing:border-box;padding:8px;margin:4px 0;border:1px solid #ccc;border-radius:6px}button{background:#111;color:#fff;border:0;padding:8px 16px;border-radius:6px}"""
JS="""async function g(f,id){const d=new FormData(f);const b={id:id,contactado:d.get('contactado')||'',acepto:d.get('acepto')||'',persona:d.get('persona')||'',nota:d.get('nota')||''};const m=f.querySelector('.msg');m.style.color='';
if(b.acepto=='si'&&!b.persona.trim()){m.style.color='#c00';m.textContent='Escribe el nombre de la persona que aceptó';return false}
m.textContent='Guardando…';const r=await fetch(location.pathname+'/guardar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});const j=await r.json().catch(()=>({}));
if(r.ok){m.textContent='✔ Guardado';if(b.contactado=='si')f.closest('.card').classList.add('ok')}else{m.style.color='#c00';m.textContent=j.error||'Error al guardar'}return false}"""
def page(t,sub,body): return f"<!doctype html><html lang=es><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><meta name=robots content=noindex><title>{e(t)}</title><style>{CSS}</style></head><body><header><img src=/logo.jpg><div><h1>Sistema de Alianzas para Punta de Cierre</h1><div>{sub}</div></div></header><main>{body}</main><script>{JS}</script></body></html>"
class H(BaseHTTPRequestHandler):
    def send(self,c,b,ct='text/html; charset=utf-8'):
        b=b.encode() if isinstance(b,str) else b; self.send_response(c); self.send_header('Content-Type',ct); self.send_header('Cache-Control','no-store'); self.send_header('X-Robots-Tag','noindex'); self.end_headers(); self.wfile.write(b)
    def sok(self): return bool(SYNC_KEY) and hmac.compare_digest(self.headers.get('X-Sync-Key',''),SYNC_KEY)
    def ctx(self):
        t=load('tokens',{}); inv={v:k for k,v in t.get('asesores',{}).items()}
        return urllib.parse.urlparse(self.path).path.rstrip('/').split('/'),t,inv
    def do_HEAD(self): self.send_response(200); self.end_headers()
    def do_GET(self):
        if self.path=='/healthz': return self.send(200,'ok','text/plain')
        if self.path=='/logo.jpg': return self.send(200,open(os.path.join(BASE,'logo.jpg'),'rb').read(),'image/jpeg')
        if self.path=='/sync/respuestas':
            if not self.sok(): return self.send(403,'{}','application/json')
            with LOCK: return self.send(200,json.dumps(load('respuestas',{}),ensure_ascii=False),'application/json')
        p,t,inv=self.ctx(); of={o['id']:o for o in load('oficinas',[])}; R=load('respuestas',{}); A=load('asignacion',{})
        if len(p)==3 and p[1]=='a' and p[2] in inv:
            a=inv[p[2]]; l=[of[i] for i in A.get(a,[]) if i in of]; hechas=sum(1 for o in l if R.get(o['id'],{}).get('contactado'))
            return self.send(200,page(a,f"Hola, {e(a.split()[0])}. Tienes {len(l)} oficina(s) por llamar · {hechas} ya registrada(s).",''.join(card(o,R.get(o['id']),p[2]) for o in l)))
        if len(p)==3 and p[1]=='admin' and p[2]==t.get('admin'):
            rows=''.join(f"<tr><td>{e(a)}</td><td>{e(of[i]['oficina'])}</td><td>{e(R.get(i,{}).get('contactado',''))}</td><td>{e(R.get(i,{}).get('acepto',''))}</td><td>{e(R.get(i,{}).get('persona',''))}</td><td>{e(R.get(i,{}).get('nota',''))}</td></tr>" for a,ids in A.items() for i in ids if i in of)
            conf=sum(1 for r in R.values() if r.get('acepto')=='si')
            return self.send(200,page('Admin',f"Alianzas confirmadas: {conf}",f"<table border=1 cellpadding=4 style='background:#fff;font-size:13px'><tr><th>Asesora</th><th>Oficina</th><th>Contactado</th><th>Aceptó</th><th>Persona</th><th>Nota</th></tr>{rows}</table>"))
        self.send(404,page('No encontrado','Enlace no válido','<p>Este enlace no es válido.</p>'))
    def do_POST(self):
        try: d=json.loads(self.rfile.read(min(int(self.headers.get('Content-Length',0)),20_000_000)))
        except Exception: return self.send(400,'{}','application/json')
        if self.path=='/sync/data':
            if not(REMOTE and self.sok()): return self.send(403,'{}','application/json')
            with LOCK:
                for k in ('oficinas','tokens','asignacion','inmuebles'):
                    if k in d: wj(k,d[k])
                if 'respuestas' in d: wj('respuestas',merge(d['respuestas'],load('respuestas',{})))
            return self.send(200,'{"ok":true}','application/json')
        p,t,inv=self.ctx()
        if not(len(p)==4 and p[1]=='a' and p[2] in inv and p[3]=='guardar'): return self.send(404,'{}','application/json')
        a=inv[p[2]]
        if d.get('id') not in load('asignacion',{}).get(a,[]): return self.send(400,'{"error":"Oficina no válida"}','application/json')
        c,ac=d.get('contactado',''),d.get('acepto','')
        if c not in('si','no') : return self.send(400,'{"error":"Marca si la contactaste"}','application/json')
        if ac not in('','si','no'): return self.send(400,'{}','application/json')
        pe=(d.get('persona') or '').strip()[:120]
        if ac=='si' and not pe: return self.send(400,'{"error":"Escribe el nombre de la persona que aceptó"}','application/json')
        rec={'asesora':a,'contactado':c,'acepto':ac,'persona':pe,'nota':(d.get('nota') or '').strip()[:1500],'at':datetime.datetime.now(CCS).isoformat(timespec='seconds')}
        with LOCK:
            R=load('respuestas',{}); old=R.get(d['id'])
            if old: h=old.pop('historial',[]); rec['historial']=(h+[old])[-10:]
            R[d['id']]=rec; wj('respuestas',R)
        self.send(200,'{"ok":true}','application/json')
    def log_message(self,*a): pass
if __name__=='__main__':
    if not REMOTE:
        t=load('tokens',{}); A=load('asignacion',{})
        with open(os.path.join(BASE,'enlaces.txt'),'w') as f:
            f.write(f"BASE = https://alianzas.grupoinmobiliarioforrent.com (local http://127.0.0.1:{PORT})\n\nADMIN: BASE/admin/{t['admin']}\n\n")
            for a,tk in t['asesores'].items(): f.write(f"{a} ({len(A.get(a,[]))}): BASE/a/{tk}\n")
    ThreadingHTTPServer(('0.0.0.0',PORT),H).serve_forever()
