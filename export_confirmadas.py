#!/usr/bin/env python3
"""respuestas.json -> reports/alianzas_confirmadas.csv (Aceptó=sí, con fecha/hora Caracas) + alianzas_registro.csv (todas)."""
import json,csv,os
B=os.path.dirname(os.path.abspath(__file__)); R=json.load(open(os.path.join(B,'respuestas.json'))) if os.path.exists(os.path.join(B,'respuestas.json')) else {}
of={o['id']:o for o in json.load(open(os.path.join(B,'oficinas.json')))}
H=['fecha_hora_caracas','oficina','correo','telefono','persona_que_acepto','asesora','nota']
def row(i,r): o=of.get(i,{}); return [r['at'][:19].replace('T',' '),o.get('oficina',i),o.get('correo',''),o.get('telefono',''),r.get('persona',''),r.get('asesora',''),r.get('nota','')]
out='/workspace/forrent/reports/'
with open(out+'alianzas_confirmadas.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(H); [w.writerow(row(i,r)) for i,r in sorted(R.items(),key=lambda x:x[1]['at']) if r.get('acepto')=='si']
with open(out+'alianzas_registro_llamadas.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(H[:5]+['asesora','contactado','acepto','nota']); [w.writerow(row(i,r)[:6]+[r.get('contactado'),r.get('acepto'),r.get('nota')]) for i,r in sorted(R.items(),key=lambda x:x[1]['at'])]
print(sum(1 for r in R.values() if r.get('acepto')=='si'),'confirmadas')
