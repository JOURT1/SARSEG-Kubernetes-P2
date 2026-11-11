"""Genera el informe PDF y su version Markdown desde evidencias verificadas."""
from __future__ import annotations
import datetime as dt
from html import escape
import json
from pathlib import Path
import subprocess

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate, PageBreak, PageTemplate, Paragraph, Preformatted, Spacer, Table, TableStyle
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String

ROOT = Path(__file__).resolve().parents[1]
REPO = 'https://github.com/JOURT1/SARSEG-Kubernetes-P2'
EVIDENCE = ROOT / 'docs/evidencias'
FINAL = EVIDENCE / 'ejecucion-final'
OUT = ROOT / 'output/pdf/Informe-SARSEG-Kubernetes-P2.pdf'
R = json.loads((FINAL / 'resultados.json').read_text(encoding='utf-8'))
FIRST = json.loads((EVIDENCE / 'ejecucion/resultados.json').read_text(encoding='utf-8'))
assert R['success'] and all(c['passed'] for c in R['checks'].values()), 'No generar informe de exito sin pruebas correctas'
CI_PATH = EVIDENCE / 'github-actions.json'
CI = json.loads(CI_PATH.read_text(encoding='utf-8')) if CI_PATH.exists() else {}
OWN = R['ownership']
REC = R['recovery']
ROLL = R['rollout']
HTTP = R['http_sampling']
fonts = Path('C:/Windows/Fonts')
pdfmetrics.registerFont(TTFont('Arial', str(fonts / 'arial.ttf')))
pdfmetrics.registerFont(TTFont('ArialBold', str(fonts / 'arialbd.ttf')))
pdfmetrics.registerFont(TTFont('Consolas', str(fonts / 'consola.ttf')))
pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='ArialBold', italic='Arial', boldItalic='ArialBold')
styles = getSampleStyleSheet()
for name in ['Normal', 'BodyText', 'Title', 'Heading1', 'Heading2', 'Heading3']:
    styles[name].fontName = 'ArialBold' if name in ['Title', 'Heading1', 'Heading2', 'Heading3'] else 'Arial'
    styles[name].textColor = colors.black
styles['Title'].fontSize = 23
styles['Title'].leading = 28
styles['Title'].spaceAfter = 14
styles['Title'].alignment = TA_LEFT
styles['Heading1'].fontSize = 16
styles['Heading1'].leading = 20
styles['Heading1'].spaceAfter = 10
styles['Heading2'].fontSize = 11.5
styles['Heading2'].leading = 15
styles['Heading2'].spaceBefore = 10
styles['Heading2'].spaceAfter = 5
styles['BodyText'].fontSize = 10.3
styles['BodyText'].leading = 14.5
styles['BodyText'].spaceAfter = 8
styles.add(ParagraphStyle(name='SmallText', fontName='Arial', fontSize=8.4, leading=11.5, spaceAfter=6, textColor=colors.HexColor('#333333')))
styles.add(ParagraphStyle(name='Cell', fontName='Arial', fontSize=8.9, leading=12))
styles.add(ParagraphStyle(name='CellHead', fontName='ArialBold', fontSize=8.9, leading=12, textColor=colors.white))
styles.add(ParagraphStyle(name='CodeBlock', fontName='Consolas', fontSize=8.1, leading=10.8, spaceBefore=4, spaceAfter=8, backColor=colors.HexColor('#f2f4f6'), borderPadding=8))
styles.add(ParagraphStyle(name='Caption', fontName='Arial', fontSize=8.8, leading=11.5, spaceBefore=5, textColor=colors.HexColor('#333333')))
story = []


def p(text, style='BodyText'):
    story.append(Paragraph(text, styles[style]))


def title(text):
    p(text, 'Heading1')


def heading(text):
    p(text, 'Heading2')


def code(text):
    story.append(Preformatted(text, styles['CodeBlock']))


def table(headers, rows, widths):
    cells = [[Paragraph(escape(str(c)), styles['CellHead']) for c in headers]]
    cells += [[Paragraph(escape(str(c)), styles['Cell']) for c in row] for row in rows]
    t = Table(cells, colWidths=[w * mm for w in widths], hAlign='LEFT', repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#273848')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f2f4f6')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor('#273848')),
        ('LINEBELOW', (0, -1), (-1, -1), 0.3, colors.HexColor('#b9c2ca')),
    ]))
    story.append(t)
    story.append(Spacer(1, 5 * mm))


def page(template='Portrait'):
    story.append(NextPageTemplate(template))
    story.append(PageBreak())


def capture(path, label, caption):
    page('Landscape')
    title(label)
    story.append(Image(str(path), width=245 * mm, height=245 * 950 / 1500 * mm, hAlign='CENTER'))
    p(caption, 'Caption')


def link(label, url):
    return f'<link href="{escape(url, quote=True)}" color="#185587">{escape(label)}</link>'


def architecture():
    d = Drawing(175 * mm, 66 * mm)
    def box(x, y, w, h, lines, fill='#f2f4f6'):
        d.add(Rect(x * mm, y * mm, w * mm, h * mm, rx=3, ry=3, fillColor=colors.HexColor(fill), strokeColor=colors.HexColor('#738496'), strokeWidth=.7))
        for i, s in enumerate(lines):
            d.add(String((x + w / 2) * mm, (y + h / 2 + (len(lines)-1)*2 - i*4) * mm, s, fontName='Arial', fontSize=8.5, textAnchor='middle'))
    def arrow(x1, y1, x2, y2):
        d.add(Line(x1 * mm, y1 * mm, x2 * mm, y2 * mm, strokeColor=colors.HexColor('#273848'), strokeWidth=1))
        d.add(Polygon([x2*mm, y2*mm, (x2-2)*mm, (y2+1.2)*mm, (x2-2)*mm, (y2-1.2)*mm], fillColor=colors.HexColor('#273848'), strokeColor=None))
    box(0, 44, 43, 18, ['Windows', '127.0.0.1:13000'])
    box(53, 44, 55, 18, ['Service NodePort', '30300 -> 3000'])
    box(118, 44, 55, 18, ['Grafana', '2 Pods en 2 workers'])
    arrow(43, 53, 53, 53)
    arrow(108, 53, 118, 53)
    box(0, 6, 43, 21, ['API Kubernetes', 'namespace SARSEG'])
    box(53, 6, 55, 21, ['kube-state-metrics', 'lectura limitada'])
    box(118, 6, 55, 21, ['Prometheus', 'scrape cada 5 s'])
    arrow(43, 16, 53, 16)
    arrow(108, 16, 118, 16)
    d.add(Line(146*mm, 27*mm, 146*mm, 44*mm, strokeColor=colors.HexColor('#273848')))
    d.add(String(142*mm, 34*mm, 'consulta', fontName='Arial', fontSize=7.5, textAnchor='end'))
    return d


def footer(canvas, doc):
    width, height = canvas._pagesize
    canvas.saveState()
    canvas.setFont('Arial', 8)
    canvas.setFillColor(colors.HexColor('#555555'))
    canvas.drawString(17 * mm, 9 * mm, 'SARSEG  |  Kubernetes  |  P2')
    canvas.drawRightString(width - 17 * mm, 9 * mm, str(doc.page))
    canvas.restoreState()


date_local = dt.datetime.fromisoformat(R['finished_utc']).astimezone(dt.timezone(dt.timedelta(hours=-5)))
date_label = date_local.strftime('%d/%m/%Y')
p('Configuración de un clúster Kubernetes para SARSEG', 'Title')
p('Grafana con Deployment y ReplicaSet', 'Heading2')
p(f'Actividad Configuración de cluster Docker Swarm o Kubernetes · 15 por ciento P2<br/>Autor del repositorio JOURT1 · {date_label} · Zona horaria America/Guayaquil', 'SmallText')
p('Se desplegó Grafana como plataforma de observabilidad para un laboratorio vinculado con SARSEG. Se verificaron dos réplicas distribuidas en dos workers, exposición por NodePort, escalado, reposición automática de un Pod, actualización gradual y rollback. Los resultados se sustentan en estados de Kubernetes, solicitudes HTTP y capturas reales exportadas del tablero.')
p('<b>Repositorio público</b><br/>' + link(REPO, REPO))
heading('Alcance y relación con SARSEG')
p('SARSEG es un sistema de registro de asistencia con API .NET, PostgreSQL e interfaz Ionic/Angular. Grafana permite observar infraestructura y, con instrumentación posterior, podría mostrar latencia de la API, errores y trabajos de reportes. Para esta actividad no se necesita copiar el código fuente de la aplicación: se utilizan imágenes oficiales de la plataforma de monitoreo.')
p('La práctica mide recursos reales de su namespace de observabilidad. No despliega la API privada de SARSEG ni presenta métricas de estudiantes o de la base de datos del sistema. El repositorio original conserva su visibilidad privada.')
heading('Resultado verificado')
table(['Criterio', 'Resultado'], [
    ['Clúster', '1 control plane y 2 workers Ready; Kubernetes 1.32.2'],
    ['Plataforma', 'Grafana 12.3.0 con Deployment y dos Pods Ready'],
    ['Métricas', 'Prometheus 3.5.0 y kube-state-metrics 2.16.0; tres fuentes UP'],
    ['Exposición', 'http://127.0.0.1:13000 mediante NodePort 30300'],
    ['Pruebas finales', f"{len(R['checks'])} comprobaciones aprobadas; {HTTP['successful']}/{HTTP['total']} muestras de salud correctas"],
], [45, 131])
p('El laboratorio corre sobre Docker Desktop con kind. Las réplicas demuestran mecanismos de Kubernetes en una computadora; no constituyen una instalación de alta disponibilidad de producción.', 'SmallText')

page()
title('Arquitectura y configuración declarativa')
story.append(architecture())
heading('Deployment ReplicaSet y Pod')
p('El Deployment declara el estado deseado y gestiona las revisiones de la plantilla. Un ReplicaSet mantiene el número de Pods de una plantilla concreta. El Pod es la unidad que ejecuta el contenedor. La relación se comprobó por ownerReferences: Deployment → ReplicaSet → Pods. No se creó un ReplicaSet independiente que compitiera por el mismo selector.')
p('El Service selecciona app=grafana y dirige tráfico únicamente a endpoints listos. Las probes comprueban /api/health y la afinidad excluye el control plane del reparto entre workers. El escalado modifica replicas; cambiar spec.template provoca una nueva revisión y otro ReplicaSet.')
table(['Parámetro', 'Valor y finalidad'], [
    ['Réplicas y distribución', 'replicas: 2; maxSkew: 1 entre los workers'],
    ['Actualización', 'RollingUpdate; maxSurge: 1; maxUnavailable: 0'],
    ['Terminación', 'preStop: sleep 10; terminationGracePeriodSeconds: 30'],
    ['Recursos por Pod Grafana', 'Solicitud 100m CPU y 160Mi; límite 500m CPU y 512Mi'],
    ['Acceso y datos', 'Viewer anónimo local; dashboards y datasource desde ConfigMaps'],
], [48, 128])
code('spec:\n  replicas: 2\n  strategy:\n    type: RollingUpdate\n    rollingUpdate: {maxSurge: 1, maxUnavailable: 0}\n  selector:\n    matchLabels: {app: grafana}')
p('Configuración completa y reproducible: ' + link('k8s/grafana.yaml', REPO + '/blob/main/k8s/grafana.yaml') + ' y ' + link('cluster/kind.yaml', REPO + '/blob/main/cluster/kind.yaml') + '.', 'SmallText')

capture(EVIDENCE / 'capturas/01-grafana-base.png', 'Grafana expuesto y fuentes activas', 'Figura 1. Exportación PNG real de Grafana Image Renderer antes del protocolo. Se observan dos réplicas deseadas y disponibles, cuatro Pods de infraestructura y tres fuentes UP. La exposición desde Windows se verificó además con HTTP 200 en /api/health. El PNG original está en docs/evidencias/capturas/01-grafana-base.png.')

page()
title('Escalado y recuperación de un Pod')
heading('Escalado observado')
p('Se ejecutó kubectl scale deployment/grafana --replicas=3. Se esperaron tres Pods Ready y tres réplicas disponibles. El UID del ReplicaSet activo permaneció igual, lo que confirma que escalar no modifica la plantilla. Después se restauró el estado de dos réplicas.')
code("$ctx = 'kind-sarseg-p2'\n$ns = 'sarseg-observabilidad'\nkubectl --context $ctx -n $ns scale deployment/grafana --replicas=3\n# Despues de comprobar 3 replicas Ready\nkubectl --context $ctx -n $ns scale deployment/grafana --replicas=2")
heading('Propiedad verificada en la ejecución final')
table(['Objeto', 'Nombre y referencia'], [
    ['Deployment', OWN['deployment'] + '; UID ' + OWN['deployment_uid']],
    ['ReplicaSet activo', OWN['replicaset'] + '; owner UID del Deployment'],
    ['Pod inicial 1', OWN['pods'][0]['name'] + '; nodo ' + OWN['pods'][0]['node']],
    ['Pod inicial 2', OWN['pods'][1]['name'] + '; nodo ' + OWN['pods'][1]['node']],
], [39, 137])
heading('Recuperación automática')
p(f"Se eliminó el Pod <b>{REC['deleted_pod']}</b> con kubectl delete pod --wait=false. El ReplicaSet creó un reemplazo y recuperó dos réplicas disponibles en aproximadamente <b>{REC['elapsed_seconds']} segundos</b>, según el tiempo medido por el script. La medición incluye el sondeo y el arranque; no es un SLA.")
new_pod = REC['new_pods'][0]
code('Pod eliminado\n' + REC['deleted_pod'] + '\nUID ' + REC['deleted_uid'] + '\n\nPod de reemplazo\n' + new_pod['name'] + '\nUID ' + new_pod['uid'])
p('Los UIDs diferentes prueban que se creó otro objeto Pod. El criterio de aceptación exige Ready y availableReplicas, además del estado Running. Los archivos 02-escalado-tres y 03-recuperacion conservan las salidas y estados JSON.', 'SmallText')

capture(FINAL / 'capturas/02-grafana-tres-replicas.png', 'Grafana escalado a tres réplicas', 'Figura 2. Captura exportada durante la ejecución final, una vez alcanzadas tres réplicas disponibles. Prometheus registra el cambio de estado real de Kubernetes. El incremento de Pods Running incluye los recursos del laboratorio; no representa estudiantes ni sesiones de asistencia.')

page()
title('Actualización gradual rollback y salud HTTP')
p('La prueba cambió la anotación sarseg.io/revision-laboratorio de v1 a v2-prueba-p2 dentro de spec.template. La imagen continuó siendo grafana/grafana:12.3.0. Se demuestra el mecanismo de actualización de plantilla; no se afirma haber actualizado la versión del software.')
table(['Momento', 'ReplicaSet y resultado'], [
    ['Antes de actualizar', ROLL['before_rs'] + '; dos réplicas disponibles'],
    ['Después del rollout', ROLL['after_rs'] + '; nuevo UID y dos réplicas disponibles'],
    ['Rollback', ROLL['rollback_rs'] + '; plantilla v1 y ReplicaSet original reactivado'],
], [42, 134])
code("$ctx = 'kind-sarseg-p2'\n$ns = 'sarseg-observabilidad'\nkubectl --context $ctx -n $ns rollout status deployment/grafana\nkubectl --context $ctx -n $ns rollout undo deployment/grafana "+\
     "--to-revision=" + ROLL['initial_revision'])
heading('Hallazgo conservado y corrección')
p('La primera ejecución detectó RemoteDisconnected en una solicitud durante el rollout y se marcó como no aprobada. El evento es compatible con una carrera entre la retirada del endpoint y la terminación del proceso. Se añadió un hook preStop de diez segundos para dar tiempo al drenaje y se repitió todo el protocolo. Se conserva la evidencia de ambas ejecuciones.')
table(['Ejecución', 'Muestras correctas', 'Resultado'], [
    ['Primera, sin preStop', f"{FIRST['http_sampling']['successful']}/{FIRST['http_sampling']['total']}", 'Una conexión interrumpida'],
    ['Final, con preStop', f"{HTTP['successful']}/{HTTP['total']}", 'Todas las muestras HTTP 200 y database=ok'],
], [52, 45, 79])
p('El muestreo se realiza aproximadamente cada segundo durante escalado, eliminación de Pod, rollout y rollback. Permite afirmar que esas solicitudes respondieron correctamente; no demuestra ausencia de interrupciones entre muestras ni disponibilidad de producción.')
p('Evidencias: resultados.json, http-muestreo.json, historial-rollout.txt y estados 04, 05 y 06 de docs/evidencias/ejecucion-final. Los ReplicaSets antiguos con cero réplicas se conservan para el historial y el rollback.', 'SmallText')

capture(FINAL / 'capturas/03-grafana-final.png', 'Estado final después del rollback', 'Figura 3. Captura exportada al finalizar el protocolo: dos réplicas deseadas y disponibles, fuentes UP e historial de cambios durante las pruebas. Los picos transitorios de Pods pueden incluir objetos en terminación. La disponibilidad se valida con Ready y availableReplicas, no solo con el contador Running.')

page()
title('Historial de trabajo y reproducción')
p('Los avances se publicaron en ramas separadas con commits de alcance concreto. Se conservaron los cambios correctivos y el primer resultado fallido. Los pull requests usan merge commits para mantener visible el desarrollo; no se simulan revisores ni fechas de trabajo.')
table(['Rama', 'Avance y pull request'], [
    ['main', 'Alcance inicial y recepción de los avances integrados'],
    ['codex/infraestructura-kubernetes', 'Clúster, manifiestos y arranque; PR 1'],
    ['codex/metricas-sarseg', 'Métricas, ConfigMaps, tablero y afinidad; PR 2'],
    ['codex/pruebas-deployment-replicaset', 'Pruebas, corrección de drenaje y evidencias; PR 3'],
    ['codex/informe-evidencias', 'Informe, referencias e índice de entrega; PR 4'],
], [88, 88])
p('Trazabilidad: ' + ' · '.join(link('PR ' + str(i), REPO + '/pull/' + str(i)) for i in range(1, 5)) + ' · ' + link('Historial de commits', REPO + '/commits/main') + ' · ' + link('Ramas', REPO + '/branches') + '.', 'SmallText')
heading('Verificación independiente en GitHub Actions')
if CI.get('conclusion') == 'success':
    p('El workflow creó otro clúster en un runner Linux, desplegó los manifiestos y ejecutó el protocolo real sin renderer. La ejecución terminó correctamente: ' + link(str(CI['run_id']), CI['url']) + '. Los registros están disponibles como artefacto de la ejecución.')
else:
    p('El repositorio incluye un workflow que crea un clúster en Linux y ejecuta el protocolo real. Su estado al corte del informe es ' + escape(str(CI.get('status', 'no verificado'))) + '. Los resultados locales no se presentan como éxito de CI.')
heading('Inicio desde una copia nueva')
code('git clone https://github.com/JOURT1/SARSEG-Kubernetes-P2.git\ncd SARSEG-Kubernetes-P2\n.\\scripts\\Start-Lab.ps1\n\n# Abrir http://127.0.0.1:13000\n# Prueba nueva sin sobrescribir la evidencia entregada\npython scripts/test_lab.py --output tmp/repeticion')
p('Requisitos: Docker Desktop con motor Linux, PowerShell 7, kubectl 1.32 y Python 3 para las pruebas. Start-Lab.ps1 descarga kind 0.27.0 y valida el SHA256 oficial. Para capturas opcionales se ejecuta Export-Dashboard.ps1 y se agrega --render a las pruebas. Todos los comandos de Kubernetes especifican contexto y namespace.', 'SmallText')

page()
title('Usos límites y conclusiones')
heading('Usos que puede tener la plataforma')
p('En SARSEG, Grafana puede centralizar indicadores de operación y facilitar la detección de problemas durante horarios de entrada o salida. Al instrumentar la API .NET y sus dependencias se podrían añadir latencia HTTP, errores de autenticación agregados, tiempos de generación de PDF o XLSX y fallos de conexión con PostgreSQL. Los datos personales y las marcas individuales no son necesarios para esos paneles.')
p('Deployment permite repetir la configuración, escalar la capa de visualización y actualizar su plantilla con control de réplicas disponibles. ReplicaSet repone Pods eliminados o perdidos. Service mantiene un punto estable de acceso aunque cambien las IP y los nombres de los Pods. Estas funciones se comprobaron con cambios reales y referencias de propiedad.')
heading('Límites del resultado')
p('El clúster depende de una sola computadora y de Docker Desktop. Grafana usa SQLite efímera e independiente por réplica; los dashboards y la fuente de datos se reconstruyen desde ConfigMaps. Prometheus tiene una sola réplica y datos efímeros. No se habilitan edición de tableros ni alertas persistentes. Una solución productiva de Grafana en alta disponibilidad requiere una base compartida PostgreSQL o MySQL, autenticación y diseño de persistencia y redundancia.')
p('El acceso anónimo tiene rol Viewer y se publica únicamente en 127.0.0.1. kube-state-metrics dispone de lectura limitada al namespace; se verificó que no puede listar Secrets. No se despliega ni modifica el sistema privado de asistencia. Las métricas implementadas son de infraestructura del laboratorio.')
heading('Conclusión')
p(f"La ejecución final cumplió {len(R['checks'])} comprobaciones: clúster Ready, propiedad de recursos, exposición, métricas, RBAC, escalado, reposición de Pod, rollout, rollback y salud HTTP. Se recuperaron dos réplicas después de los cambios y se observaron {HTTP['successful']} respuestas correctas de {HTTP['total']} muestras. El hallazgo de la primera ejecución y su corrección muestran el proceso de validación y sus límites.")
heading('Fuentes y archivos de respaldo')
references = [
    ('Kubernetes Deployments', 'https://kubernetes.io/docs/concepts/workloads/controllers/deployment/'),
    ('Kubernetes ReplicaSet', 'https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/'),
    ('kind Configuration', 'https://kind.sigs.k8s.io/docs/user/configuration/'),
    ('Grafana Provisioning', 'https://grafana.com/docs/grafana/latest/administration/provisioning/'),
    ('Grafana High availability', 'https://grafana.com/docs/grafana/latest/setup-grafana/set-up-for-high-availability/'),
    ('Grafana Image rendering', 'https://grafana.com/docs/grafana/latest/setup-grafana/image-rendering/'),
]
for label, url in references:
    p(link(label, url), 'SmallText')
p('Material de clase consultado: Intro Kubernetes, páginas 6 a 10 y 13; Intro Docker, página 9; CD Intro, páginas 3 y 6; Intro Entrega Continua CD, página 4. El ejemplo de primer Pod usa Nginx, mientras esta práctica despliega Grafana. Los documentos de clase no se redistribuyen en el repositorio.', 'SmallText')
p('Respaldo verificable en docs/evidencias: ejecucion-final/resultados.json, estados JSON y TXT, comandos.json, eventos.txt, http-muestreo.json, capturas PNG y SHA256SUMS.txt. La ejecución inicial se conserva en ejecucion. Las imágenes son exportaciones reales de Grafana Image Renderer; las salidas de kubectl se identifican como registros de terminal.', 'SmallText')

OUT.parent.mkdir(parents=True, exist_ok=True)
doc = BaseDocTemplate(str(OUT), pagesize=A4, title='Configuración de un clúster Kubernetes para SARSEG', author='JOURT1', subject='Deployment ReplicaSet Grafana P2', leftMargin=17*mm, rightMargin=17*mm, topMargin=16*mm, bottomMargin=16*mm)
portrait_frame = Frame(17*mm, 16*mm, 176*mm, 265*mm, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
landscape_frame = Frame(15*mm, 14*mm, 267*mm, 182*mm, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
doc.addPageTemplates([PageTemplate(id='Portrait', frames=[portrait_frame], onPage=footer, pagesize=A4), PageTemplate(id='Landscape', frames=[landscape_frame], onPage=footer, pagesize=landscape(A4))])
doc.build(story)

markdown = f'''# Configuración de un clúster Kubernetes para SARSEG

Actividad 15% P2. Autor del repositorio: JOURT1. Fecha: {date_label}.

Repositorio público: {REPO}

Informe con las figuras y el detalle de la práctica: [PDF](../output/pdf/Informe-SARSEG-Kubernetes-P2.pdf).

## Objetivo y alcance

Se despliega Grafana, plataforma diferente al Nginx del primer Pod de clase, con
Deployment, ReplicaSet y Service NodePort. Se utilizan imágenes oficiales y no
se copia el código privado de SARSEG. El contexto es el monitoreo operativo de
un sistema de asistencia con API .NET, PostgreSQL e Ionic/Angular.

## Configuración

- kind 0.27.0 con Kubernetes 1.32.2, un control plane y dos workers.
- Namespace sarseg-observabilidad.
- Grafana 12.3.0, dos réplicas distribuidas entre workers.
- RollingUpdate, maxSurge=1, maxUnavailable=0, probes de /api/health.
- preStop de diez segundos y gracia de treinta segundos.
- NodePort 30300 mapeado a http://127.0.0.1:13000.
- Prometheus 3.5.0 y kube-state-metrics 2.16.0; RBAC de lectura del namespace.
- ConfigMaps generados con Kustomize y dashboard provisionado de solo lectura.

## Resultado de la ejecución final

- {len(R['checks'])} comprobaciones aprobadas.
- Tres nodos Ready y dos réplicas disponibles al cierre.
- Escalado 2 a 3 a 2 sin cambiar el UID del ReplicaSet.
- Reposición de {REC['deleted_pod']} por {new_pod['name']} con UID diferente.
- Recuperación medida en aproximadamente {REC['elapsed_seconds']} segundos.
- Rollout desde {ROLL['before_rs']} a {ROLL['after_rs']}.
- Rollback que reactiva {ROLL['rollback_rs']} y restaura la plantilla v1.
- {HTTP['successful']}/{HTTP['total']} muestras HTTP 200 y database=ok durante las pruebas.

La actualización cambia una anotación de spec.template y conserva la misma
imagen de Grafana. El muestreo aproximadamente cada segundo no garantiza
disponibilidad entre solicitudes.

## Capturas reales

![Grafana inicial](evidencias/capturas/01-grafana-base.png)

![Tres réplicas](evidencias/ejecucion-final/capturas/02-grafana-tres-replicas.png)

![Estado final](evidencias/ejecucion-final/capturas/03-grafana-final.png)

Son exportaciones reales de la interfaz mediante Grafana Image Renderer. Los
registros de kubectl están en TXT y JSON; no se presentan como capturas.

## Hallazgo y mejora

La primera ejecución registró {FIRST['http_sampling']['successful']}/{FIRST['http_sampling']['total']}
solicitudes correctas y un RemoteDisconnected durante el rollout. El resultado
no aprobado se conserva en evidencias/ejecucion. Se agregó preStop para dar
tiempo al drenaje y se repitió el protocolo completo, conservando la ejecución
final por separado. Véase [incidencias](INCIDENCIAS.md).

## Usos y límites

Grafana puede mostrar latencia y errores HTTP, generación de reportes y estado
de PostgreSQL cuando se instrumente SARSEG. En esta entrega solo se observan
recursos reales de infraestructura; la API privada no está desplegada.

Dos Pods permiten demostrar reposición y actualizaciones. La computadora y el
control plane siguen siendo puntos únicos de fallo. Grafana usa SQLite efímera
independiente y configuración reconstruida desde Git; Prometheus es efímero.
Alta disponibilidad productiva requiere una base compartida y otro diseño de
autenticación, almacenamiento y redundancia.

## Historial y reproducción

Se conservan main y cuatro ramas de avance, con commits y PR separados:
[infraestructura]({REPO}/pull/1), [métricas]({REPO}/pull/2),
[pruebas]({REPO}/pull/3), [informe]({REPO}/pull/4).

Inicio: `scripts/Start-Lab.ps1`. Prueba nueva: `python scripts/test_lab.py --output tmp/repeticion`.
Consulte [reproducción](REPRODUCCION.md), [arquitectura](ARQUITECTURA.md),
[métricas](METRICAS.md), [pruebas](PRUEBAS.md) y [evidencias](evidencias/README.md).

## Referencias

''' + '\n'.join(f'- [{label}]({url})' for label, url in references) + '''

Material de clase consultado: Intro Kubernetes, Intro Docker, CD Intro e Intro
Entrega Continua CD. No se redistribuyen los PDFs originales.
'''
(ROOT / 'docs/INFORME.md').write_text(markdown, encoding='utf-8')
print(str(OUT))
