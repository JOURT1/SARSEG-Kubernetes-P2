"""Read-only documentation pass. Preserve historical tests and date each read.

The HTML pages are explicitly labelled viewers of actual records or source
files. They do not impersonate terminals or native application interfaces.
"""
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import subprocess
import urllib.request
import yaml

LAB = Path(__file__).resolve().parents[1]
REPO = LAB.parent
ORIGINAL = LAB / 'docs/evidencias'
OUT = ORIGINAL / 'recorrido-apa7'
K = ['kubectl', '--context', 'kind-sarseg-spinnaker']
STEPS = []


def run(args, expected=0):
    p = subprocess.run([str(x) for x in args], cwd=REPO, capture_output=True,
                       encoding='utf-8', text=True, timeout=40)
    assert p.returncode == expected, (args, p.stdout, p.stderr)
    return {'command': subprocess.list2cmdline([str(x) for x in args]),
            'output': p.stdout + p.stderr, 'exitCode': p.returncode}


def read(relative):
    return (LAB / relative).read_text(encoding='utf-8')


def api(path):
    url = path if path.startswith('https://') else 'http://127.0.0.1:14884' + path
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'SARSEG-academic-report'}), timeout=30) as r:
        return json.load(r)


def add(key, title, category, source, blocks, facts=None, note=''):
    item = {'id':key, 'title':title, 'category':category, 'source':source,
            'capturedAt':datetime.now(timezone.utc).isoformat(), 'blocks':blocks,
            'facts':facts or [], 'note':note}
    STEPS.append(item)
    return item


def block(label, content):
    return {'command':label, 'output':content, 'exitCode':None}


def execution_summary(ex):
    return {'id':ex['id'], 'status':ex['status'], 'startTime':ex.get('startTime'),
        'endTime':ex.get('endTime'), 'parameters':ex['trigger'].get('parameters'),
        'stages':[{'name':s['name'],'status':s['status'], 'source':s['context'].get('manifestArtifact',{}).get('reference')}
                  for s in ex['stages'] if s['type']=='deployManifest']}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    add('01','Repositorio y organización del trabajo','Lectura actual', 'Git local y GitHub público',
        [run(['git','remote','-v']), run(['git','branch','--list','main','codex/spinnaker-*'])],
        [['Repositorio','JOURT1/SARSEG-Kubernetes-P2'], ['Carpeta de la práctica','spinnaker/']],
        'La instalación y las pruebas funcionales se ejecutaron entre el 19 y el 20 de noviembre. Esta toma documenta su trazabilidad.')
    add('02','Docker y herramientas disponibles','Lectura actual','Docker, kind y kubectl',[
        run(['docker','version','--format','Docker Engine: {{.Server.Version}}']),
        run(['docker','info','--format','CPU disponibles: {{.NCPU}} | Memoria: {{.MemTotal}} bytes']),
        run(['.tools/kind.exe','version']), run(K+['version','--client'])])
    add('03','Configuración del clúster local','Archivo versionado','spinnaker/cluster.yml',
        [block('cluster.yml', read('cluster.yml'))], note='El archivo fija el clúster sarseg-spinnaker, Kubernetes v1.32.2 y los puertos limitados a 127.0.0.1. Se documenta la configuración utilizada; no se afirma que esta captura muestre una nueva creación.')
    add('04','Verificación del nodo y del contenedor','Lectura actual','Kubernetes y Docker',[
        run(K+['get','nodes','-o','wide']),
        run(['docker','ps','--filter','name=sarseg-spinnaker','--format','{{.Names}} | {{.Status}} | {{.Ports}}'])])
    add('05','Imágenes reales de SARSEG construidas','Lectura actual','Docker y commit privado de SARSEG',[
        run(['docker','image','inspect','sarseg-web:9984bc57','sarseg-api:9984bc57','--format','{{.RepoTags}}\nID: {{.Id}}\nCreada: {{.Created}}\nTamaño: {{.Size}} bytes\n']),
        run(['git','-C','.local/sarseg-source','rev-parse','HEAD'])], note='Inspección de las imágenes compiladas en la implementación. El código fuente privado no se publica en el repositorio del informe.')
    add('06','Namespaces, secretos locales y permisos','Lectura actual','Kubernetes RBAC y exclusión Git',[
        run(K+['get','namespace','spinnaker','sarseg-dev']),
        run(['git','check-ignore','.local/spinnaker/credentials.json']),
        run(K+['auth','can-i','create','deployments','-n','sarseg-dev','--as=system:serviceaccount:spinnaker:clouddriver']),
        run(K+['auth','can-i','create','deployments','-n','default','--as=system:serviceaccount:spinnaker:clouddriver'],expected=1)],
        [['Escritura en sarseg-dev','Permitida'],['Escritura en default','Denegada'],['Contraseñas','No incluidas en la captura ni en Git']])
    add('07','Plataforma mínima de Spinnaker disponible','Lectura actual','Kubernetes namespace spinnaker',[
        run(K+['-n','spinnaker','get','deployments']), run(K+['-n','spinnaker','get','pods'])],
        [['Servicios Spinnaker','Deck, Gate, Orca, Clouddriver y Front50'],['Apoyo','MySQL y Redis']],
        'Se comprueba la disponibilidad de los servicios instalados. El instalador y su procedencia están versionados en platform/.')
    add('08','Metrics Server y mediciones de CPU','Lectura actual','API metrics.k8s.io',[
        run(K+['get','apiservice','v1beta1.metrics.k8s.io']),
        run(K+['-n','kube-system','get','deployment','metrics-server']),
        run(K+['-n','sarseg-dev','top','pods','-l','app=sarseg-web'])])
    lines=read('k8s/deployment.yml').splitlines()
    add('09','Deployment: réplicas, etiquetas y selector','Archivo versionado','spinnaker/k8s/deployment.yml',
        [block('deployment.yml · fragmento de identidad y selector','\n'.join(lines[:18]))],
        [['Réplicas iniciales','2'],['Selector','app: sarseg-web'],['Namespace','sarseg-dev']],
        'El archivo completo se incluye en el Apéndice A. La anotación use-source-capacity conserva la capacidad administrada por el HPA en despliegues posteriores.')
    add('10','Deployment: puerto y recursos por Pod','Archivo versionado','spinnaker/k8s/deployment.yml',
        [block('deployment.yml · fragmento del contenedor','\n'.join(lines[32:51]))],
        [['Requests','CPU 25m; memoria 32Mi'],['Limits','CPU 250m; memoria 128Mi'],['Probes','HTTP de disponibilidad y vida sobre /']])
    add('11','Service: exposición mediante NodePort','Archivo versionado','spinnaker/k8s/service.yml',
        [block('service.yml',read('k8s/service.yml'))],
        [['Ruta de tráfico','Windows:14800 → NodePort:30380 → Service:80 → Pod:http/8080']])
    add('12','HPA: política de escalamiento por CPU','Archivo versionado','spinnaker/k8s/hpa.yml',
        [block('hpa.yml · objetivo y límites','\n'.join(read('k8s/hpa.yml').splitlines()[:24]))],
        [['Mínimo / máximo','2 / 5 réplicas'],['Objetivo','50% de la CPU solicitada'],['Estabilización al reducir','60 segundos']])
    app=api('/applications/sarseg')
    add('13','Aplicación y cuenta Kubernetes en Spinnaker','Lectura actual','Gate API y configuración de Clouddriver',
        [block('GET /applications/sarseg · atributos seleccionados',json.dumps({k:app.get('attributes',app).get(k) for k in ['name','description','cloudProviders']},ensure_ascii=False,indent=2))],
        [['Aplicación','sarseg'],['Cuenta Kubernetes','sarseg-local'],['Namespace permitido','sarseg-dev'],['Cuenta de artefactos HTTP','public-git-http']])
    pipeline=json.loads(read('pipeline.json'))
    add('14','Pipeline: tres etapas Deploy (Manifest)','Archivo versionado','spinnaker/pipeline.json',[],
        [[s['name'],s['manifestArtifact']['reference']] for s in pipeline['stages']],
        'Cada etapa resuelve el archivo desde una URL fijada por parameters.gitSha. Los tres archivos se leen directamente desde GitHub por Spinnaker.')
    add('15','Sondeo Git y disparo automático del pipeline','Lectura actual y archivo versionado','git_watch.py y registro local del sondeo',
        [block('watch.stderr.log · últimas entradas públicas','\n'.join((REPO/'.local/spinnaker/watch.stderr.log').read_text().splitlines()[-4:]))],
        [['Intervalo','20 segundos'],['Comparación','Contenido de deployment.yml, service.yml y hpa.yml'],['Acción','POST a Gate para iniciar Orca'],['Confirmación','Sólo se guarda la revisión cuando SUCCEEDED']],
        'El adaptador no ejecuta kubectl ni aplica recursos. No equivale al self-healing continuo de Argo CD.')
    failed=json.loads((REPO/'.local/spinnaker/failed-execution.json').read_text())
    errors=[]
    for s in failed['stages']:
        if s['context'].get('exception'):
            errors.extend(s['context']['exception'].get('details',{}).get('errors',[]))
    add('16','Incidencia inicial y corrección de artefactos','Registro histórico','failed-execution.json y corrección d38b21b',
        [block('Resumen de la ejecución inicial fallida',json.dumps({'execution':failed['id'],'status':failed['status'],'errors':errors},indent=2))],
        [['Corrección','Definir el artefacto HTTP en cada etapa y resolver su URL con gitSha'],['Verificación posterior','Las tres etapas finalizaron en SUCCEEDED']],
        'Se conserva el error real sin el stack trace completo. La captura explica una incidencia resuelta; no representa el estado final.')
    initial=json.loads(read('docs/evidencias/initial-execution.json'))
    add('17','Primer despliegue completo desde Git','Registro histórico','docs/evidencias/initial-execution.json',
        [block('Gate · resumen de ejecución',json.dumps(execution_summary(initial),indent=2))],
        [['Resultado',initial['status']]], note='Se presentan los datos preservados de la primera ejecución exitosa, anteriores al cambio Git de la prueba.')
    health={}
    for path in ['/','/health/ready']:
        with urllib.request.urlopen('http://127.0.0.1:14800'+path,timeout=15) as response:
            health[path]={'HTTP':response.status}
            if path!='/':health[path]['body']=json.load(response)
    add('18','Comprobación HTTP por el NodePort','Lectura actual','http://127.0.0.1:14800',
        [block('Respuestas HTTP reales',json.dumps(health,indent=2))],
        [['URL de SARSEG','http://127.0.0.1:14800'],['API y PostgreSQL','Readiness ready']],
        'La prueba de login HTTP 200 está conservada en results.json; sus contraseñas y respuesta se excluyeron de la evidencia.')
    add('19','Aplicación SARSEG en el navegador','Captura directa','http://127.0.0.1:14800',[],note='Esta figura utiliza una captura directa del navegador de la aplicación real.')
    add('20','Publicación del cambio Git de la prueba','Registro Git histórico','commit 3a1c721e4f71729f628d267d52264f96a1944ab5',
        [run(['git','show','--format=short','--no-ext-diff','3a1c721','--','spinnaker/k8s/deployment.yml'])],
        note='El commit cambia sarseg.edu/revision. La prueba original verifica el nuevo SHA y la anotación aplicada sin kubectl apply manual de los tres manifiestos.')
    proof=json.loads(read('docs/evidencias/git-execution.json'))
    add('21','Spinnaker despliega automáticamente la revisión','Captura directa y registro histórico','Gate execution '+proof['id'],
        [block('Ejecución comprobada',json.dumps(execution_summary(proof),indent=2))],
        [['Estado',proof['status']],['SHA',proof['trigger']['parameters']['gitSha']]],
        'La figura muestra la interfaz nativa de Deck en la ejecución correspondiente al commit de la prueba.')
    load=yaml.safe_load(read('docs/evidencias/load-job.yml'))
    c=load['spec']['template']['spec']['containers'][0]
    add('22','Generación de carga HTTP temporal','Archivo y registro históricos','docs/evidencias/load-job.yml',
        [block('Contenedor de carga · configuración preservada',yaml.safe_dump({k:c[k] for k in ['name','image','resources']},sort_keys=False))],
        [['Destino HTTP','http://sarseg-web/'],['Concurrencia','48 trabajadores'],['Duración máxima','240 segundos; se retira al observar el escalado'],['Método de escalado','HPA por CPU; no se ejecuta kubectl scale']],
        'El Job de carga ya fue eliminado al finalizar la prueba; esta captura documenta el archivo realmente utilizado.')
    for key,original,title in [('23','05-carga-cinco','HPA: incremento automático a cinco réplicas'),('24','06-reduccion-dos','HPA: retorno automático a dos réplicas')]:
        data=json.loads(read('docs/evidencias/'+original+'.json'))
        h=yaml.safe_load(data['blocks'][2]['output'])
        add(key,title,'Registro histórico','docs/evidencias/'+original+'.json',data['blocks'],
            [['Hora de la prueba',data['time']],['HPA actual / deseado',f"{h['status']['currentReplicas']} / {h['status']['desiredReplicas']}"],['CPU objetivo','50%']],
            'La figura reutiliza la captura verificada de la ejecución original y conserva su fecha. No se presenta como una nueva prueba de carga.')
    final=json.loads((REPO/'.local/spinnaker/watch-state.json').read_text())
    final_ex=api(final['execution'])
    pr8=api('https://api.github.com/repos/JOURT1/SARSEG-Kubernetes-P2/pulls/8')
    pr9=api('https://api.github.com/repos/JOURT1/SARSEG-Kubernetes-P2/pulls/9')
    ci=api('https://api.github.com/repos/JOURT1/SARSEG-Kubernetes-P2/actions/runs/44677978819')
    add('25','Integración en main y validación final','Lectura actual y ejecuciones anteriores','GitHub PR 8, PR 9 y Gate',[],
        [['PR #8',str(pr8['merged'])+' · informe y evidencias'],['PR #9',str(pr9['merged'])+' · integración principal'],
         ['GitHub Actions',ci['conclusion']],['Rama desplegada',final['branch']],['SHA desplegado',final['sha']],['Spinnaker',final_ex['status']]],
        'Los PR 8 y 9 corresponden a la implementación funcional. La actualización APA se documenta en una rama posterior sin modificar el despliegue.')
    repo=api('https://api.github.com/repos/JOURT1/SARSEG-Kubernetes-P2')
    add('26','Repositorio público y archivos de entrega','Lectura actual','GitHub público',[],
        [['Visibilidad',repo['visibility']],['Ruta','spinnaker/k8s/'],['Archivos','deployment.yml, service.yml, hpa.yml'],['Informe','spinnaker/output/pdf/Informe-SARSEG-Spinnaker-P2.pdf']],
        'La figura utiliza una captura directa de GitHub y el acceso público se verifica además con su API.')
    (OUT/'pasos.json').write_text(json.dumps(STEPS,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    (OUT/'ejecucion-final-main.json').write_text(json.dumps(execution_summary(final_ex),ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    for step in STEPS:
        visible_facts=step['facts']
        view_blocks=step['blocks']
        if step['id'] in ['09','10','11','12']:
            visible_facts=[]
        if step['id']=='07':
            view_blocks=step['blocks'][-1:]
        if step['id']=='17':
            summary=execution_summary(initial)
            visible_facts=[['Ejecución',summary['id']],['Estado',summary['status']]]+[[s['name'],s['status']] for s in summary['stages']]
            view_blocks=[]
        facts=''.join('<tr><th>'+escape(str(k))+'</th><td>'+escape(str(v))+'</td></tr>' for k,v in visible_facts)
        blocks=[]
        for b in view_blocks:
            content=b['output']
            # Long records are preserved in JSON; the photographed view is an explicit excerpt.
            if len(content.splitlines())>24:
                content='\n'.join(content.splitlines()[:21])+'\n[Registro completo en pasos.json]'
            blocks.append('<section><h2>'+escape(b['command'])+'</h2><pre>'+escape(content)+'</pre></section>')
        # Keep the figure readable. Detailed commands remain in the original JSON.
        content=''.join(blocks)
        page=f'''<!doctype html><html lang="es"><meta charset="utf-8"><title>Paso {step['id']} · {escape(step['title'])}</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:white;color:#172a3b;font:19px Arial}}main{{width:820px;padding:20px}}header{{font-size:12px;letter-spacing:1px;color:#52677a}}h1{{font-size:25px;line-height:1.2;margin:9px 0 12px}}.meta{{font-size:12px;color:#52677a;margin:8px 0 12px}}table{{border-collapse:collapse;width:100%;font-size:18px;margin:10px 0}}th,td{{padding:7px;border-bottom:1px solid #ccd8e0;text-align:left;vertical-align:top;overflow-wrap:anywhere}}th{{width:220px;background:#f2f5f7}}h2{{font:13px Consolas;margin:11px 0 5px}}pre{{font:17px/1.25 Consolas;background:#f4f7f9;border:1px solid #d1dce3;padding:10px;white-space:pre-wrap;overflow-wrap:anywhere;margin:0}}footer{{border-top:1px solid #bdcbd5;margin-top:12px;padding-top:8px;font-size:12px;line-height:1.35}}.note{{font-size:13px;line-height:1.35}}</style>
<main id="evidence"><header>SARSEG · SPINNAKER · REGISTRO DOCUMENTAL</header><h1>Paso {step['id']}. {escape(step['title'])}</h1><div class="meta">{escape(step['category'])} · Lectura documental: {step['capturedAt']} UTC</div>
{'<table>'+facts+'</table>' if facts else ''}{content}<p class="note">{escape(step['note'])}</p>
<footer>Visor de registros reales o archivos versionados; no es una terminal ni una interfaz nativa.<br/>Fuente: {escape(step['source'])}. Datos completos: pasos.json, paso {step['id']}.</footer></main></html>'''
        if step['id']=='12':
            page=page.replace('pre{font:17px/1.25','pre{font:16px/1.2')
        (OUT/(step['id']+'.html')).write_text(page,encoding='utf-8',newline='\n')
    print(f'Collected {len(STEPS)} documented steps without modifying the cluster')


if __name__=='__main__':
    main()
