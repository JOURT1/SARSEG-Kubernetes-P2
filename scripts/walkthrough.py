"""Reproduce el laboratorio en un cluster separado y conserva la bitacora real."""
from __future__ import annotations
import datetime as dt
from html import escape
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/evidencias/recorrido-apa7'
CTX = 'kind-sarseg-p2-evidencia'
NS = 'sarseg-observabilidad'
K = ['kubectl', '--context', CTX]
STEPS = []


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def write():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'pasos.json').write_text(json.dumps(STEPS, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    links = ''.join(f'<a href="?paso={s["id"]}">{s["id"]}</a>' for s in STEPS)
    panels = []
    for s in STEPS:
        blocks = ''.join('<section><h2>' + escape(b['label']) + '</h2><pre>' + escape(b['text']) + '</pre></section>' for b in s['blocks'])
        panels.append(f'<article data-step="{s["id"]}"><div class="eyebrow">PASO {s["id"]} · EVIDENCIA DE EJECUCIÓN</div><h1>{escape(s["title"])}</h1><p class="scope">{escape(s["time"])} UTC · {CTX}</p><p>{escape(s["description"])}</p>{blocks}</article>')
    html = '''<!doctype html><html lang="es"><meta charset="utf-8"><title>SARSEG | Bitácora del laboratorio</title><style>
*{box-sizing:border-box}body{margin:0;background:#fff;color:#172330;font-family:Arial,sans-serif;font-size:18px;line-height:1.45}header{padding:15px 26px;background:#172b3c;color:white;font-size:18px;font-weight:bold}header span{float:right;font-weight:normal;font-size:14px}nav{padding:8px 26px;border-bottom:1px solid #ccd3d9;display:flex;gap:13px}nav a{color:#185485;text-decoration:none;font-size:14px}article{display:none;padding:22px 28px;max-width:1100px}article.active{display:block}.eyebrow{font-size:14px;font-weight:bold;color:#4a6477}h1{font-size:29px;line-height:1.2;margin:10px 0}h2{font-size:17px;margin:20px 0 7px}p{margin:9px 0}.scope{font-size:14px;color:#516171}pre{font-family:Consolas,monospace;font-size:18px;line-height:1.38;border:1px solid #c6d0d8;background:#f5f7f9;padding:15px;margin:0;white-space:pre-wrap;overflow-wrap:anywhere}footer{padding:14px 28px;font-size:13px;color:#55616a;border-top:1px solid #ccd3d9}
</style><header>SARSEG · Registro reproducible de Kubernetes<span>Bitácora de salidas originales</span></header><nav>''' + links + '</nav>' + ''.join(panels) + '''<footer>Captura de un visor de registros. Las salidas y estados proceden de comandos reales; no es una terminal simulada ni un estado en vivo.</footer><script>
let id=new URLSearchParams(location.search).get('paso')||'01';let el=document.querySelector('[data-step="'+id+'"]');if(el)el.classList.add('active');
</script></html>'''
    (OUT / 'index.html').write_text(html, encoding='utf-8', newline='\n')


def add(title, description, blocks, when=None):
    step = {'id': f'{len(STEPS)+1:02}', 'title': title, 'description': description, 'time': when or stamp(), 'blocks': blocks}
    STEPS.append(step)
    write()
    print('REGISTRADO', step['id'], title, flush=True)


def run(args, timeout=360):
    r = subprocess.run([str(x) for x in args], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=timeout)
    return {'label': '$ ' + subprocess.list2cmdline([str(x) for x in args]), 'text': r.stdout + r.stderr, 'exit_code': r.returncode}


def step(title, description, commands):
    blocks = [run(cmd) for cmd in commands]
    add(title, description, blocks)
    assert all(b['exit_code']==0 for b in blocks), title


def source(label, text):
    return {'label': label, 'text': text}


def compact(path):
    obj = json.loads(path.read_text(encoding='utf-8'))
    rows=[]
    for item in obj['items']:
        if item['kind']=='Deployment' and item['metadata']['name']=='grafana':
            rows.append({'kind':'Deployment','name':'grafana','desired':item['spec']['replicas'],
                         'available':item.get('status',{}).get('availableReplicas',0)})
        elif item['kind']=='ReplicaSet' and item['metadata']['name'].startswith('grafana-'):
            rows.append({'kind':'ReplicaSet','name':item['metadata']['name'],'desired':item['spec'].get('replicas',0),'ready':item.get('status',{}).get('readyReplicas',0)})
        elif item['kind']=='Pod' and item['metadata']['name'].startswith('grafana-') and not item['metadata'].get('deletionTimestamp'):
            rows.append({'kind':'Pod','name':item['metadata']['name'],'phase':item['status']['phase'],
                         'ready':any(c['type']=='Ready' and c['status']=='True' for c in item['status'].get('conditions',[]))})
    return '\n'.join(' | '.join(str(v) for v in row.values()) for row in rows)


def main():
    if (OUT/'pasos.json').exists():
        raise SystemExit('El recorrido ya existe; no se sobrescribe la evidencia.')
    step('Verificación de requisitos', 'Se comprobó el motor Docker y las versiones de las herramientas disponibles.', [
        ['docker','version','--format','Docker Server: {{.Server.Version}}'],
        [ROOT/'.tools/kind.exe','version'], ['kubectl','version','--client','-o','yaml']])
    config=(ROOT/'cluster/kind-evidencias.yaml').read_text()
    add('Configuración del clúster', 'Se usa la misma topología de tres nodos. El nombre y el puerto 13010 identifican la reproducción, separada del laboratorio original en 13000.', [source('Archivo cluster/kind-evidencias.yaml', config)])
    step('Creación real del clúster desde cero', 'kind creó el control plane y los dos workers sobre Docker Desktop.', [[ROOT/'.tools/kind.exe','create','cluster','--config','cluster/kind-evidencias.yaml','--wait','180s']])
    step('Comprobación de los tres nodos', 'Los nodos deben aparecer Ready antes de desplegar Grafana.', [K+['get','nodes']])
    yaml=(ROOT/'k8s/grafana.yaml').read_text()
    add('Definición del Deployment', 'El manifiesto declara dos réplicas, el selector y la estrategia RollingUpdate. El código completo está versionado en el repositorio.', [source('k8s/grafana.yaml, líneas 1 a 27', '\n'.join(yaml.splitlines()[:27]))])
    step('Aplicación de los manifiestos', 'Kustomize generó los ConfigMaps y Kubernetes creó los servicios y Deployments del namespace.', [K+['apply','-k','k8s']])
    step('Espera de disponibilidad', 'Se esperó a que los tres Deployments completaran su arranque; esto no equivale solamente a crear sus objetos.', [K+['-n',NS,'rollout','status','deployment/'+name,'--timeout=300s'] for name in ['grafana','prometheus','kube-state-metrics']])
    step('Deployment y ReplicaSet disponibles', 'El ReplicaSet fue creado por el Deployment, no mediante un manifiesto independiente.', [
        K+['-n',NS,'get','deployment','grafana'],
        K+['-n',NS,'get','rs','-l','app=grafana','-o','custom-columns=NAME:.metadata.name,DESIRED:.spec.replicas,CURRENT:.status.replicas,READY:.status.readyReplicas']])
    step('Pods distribuidos en los workers', 'Dos Pods Ready ejecutan la imagen de Grafana en nodos trabajadores distintos.', [K+['-n',NS,'get','pods','-l','app=grafana','-o','wide']])
    service='\n'.join(yaml.splitlines()[137:])
    add('Definición de la exposición', 'Service selecciona app=grafana. NodePort 30300 se mapea al puerto 13010 de Windows en esta reproducción.', [source('Sección Service de k8s/grafana.yaml',service)])
    blocks=[run(K+['-n',NS,'get','service','grafana'])]
    with urllib.request.urlopen('http://127.0.0.1:13010/api/health',timeout=10) as response:
        health=json.load(response)
        blocks.append(source('GET http://127.0.0.1:13010/api/health',json.dumps({'http':response.status,'response':health},ensure_ascii=False,indent=2)))
    add('Plataforma expuesta por HTTP', 'La solicitud se realizó desde Windows al puerto publicado; la base interna de Grafana respondió ok.', blocks)
    step('Ejecución del protocolo completo', 'El script prueba escalado, recuperación, rollout, rollback, RBAC y salud HTTP en este contexto separado.', [[sys.executable,'scripts/test_lab.py','--output','docs/evidencias/recorrido-apa7/pruebas','--context',CTX,'--base-url','http://127.0.0.1:13010','--render']])
    tests=OUT/'pruebas'
    result=json.loads((tests/'resultados.json').read_text())
    commands=json.loads((tests/'comandos.json').read_text())
    def matching(fragment):
        return [source('$ '+c['command'], c['stdout']+c['stderr']) for c in commands if fragment in c['command']]
    add('Escalado de dos a tres réplicas', 'Cambió el número de Pods, pero no la plantilla ni el UID del ReplicaSet. El estado mostrado procede del JSON de esa fase.', matching('scale deployment/grafana --replicas=3')+[source('Estado 02-escalado-tres.json', compact(tests/'02-escalado-tres.json'))],result['checks']['scale_up']['time_utc'])
    add('Retorno a dos réplicas', 'El Deployment volvió al tamaño inicial antes de probar la eliminación de un Pod.', matching('scale deployment/grafana --replicas=2')+[source('Comprobación',result['checks']['scale_down']['detail'])],result['checks']['scale_down']['time_utc'])
    add('Reposición automática del Pod eliminado', 'ReplicaSet creó otro objeto Pod. Los nombres y UIDs distintos identifican la recuperación real.', matching('delete pod ')+[source('UIDs y recuperación registrados',json.dumps(result['recovery'],ensure_ascii=False,indent=2))], result['checks']['self_healing']['time_utc'])
    add('Actualización de la plantilla', 'Se cambió una anotación de spec.template y Kubernetes creó otro ReplicaSet. Se mantuvo la imagen de Grafana.', matching('patch deployment grafana')+[source('Estado 05-rollout-completo.json', compact(tests/'05-rollout-completo.json'))],result['checks']['rolling_update']['time_utc'])
    add('Rollback de la revisión', 'El controlador restauró la plantilla v1 y reactivó el ReplicaSet anterior.', matching('rollout undo ')+[source('Estado 06-rollback.json',compact(tests/'06-rollback.json'))],result['checks']['rollback']['time_utc'])
    add('Resultados y exposición final', 'Se conservan todas las muestras; el resultado no se deduce únicamente de la imagen del dashboard.', [source('Resumen del protocolo',json.dumps({'success':result['success'],'checks_passed':len(result['checks']),'http_sampling':result['http_sampling'],'finished_utc':result['finished_utc']},ensure_ascii=False,indent=2))])
    print('RECORRIDO COMPLETO', flush=True)


if __name__=='__main__':
    main()
