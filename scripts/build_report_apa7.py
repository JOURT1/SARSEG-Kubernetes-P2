"""Informe estudiantil APA 7 con evidencias reales de todo el recorrido."""
from __future__ import annotations
import json
from html import escape
from pathlib import Path

from PIL import Image as PillowImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle

ROOT=Path(__file__).resolve().parents[1]
REPO='https://github.com/JOURT1/SARSEG-Kubernetes-P2'
EVIDENCE=ROOT/'docs/evidencias'
WALK=EVIDENCE/'recorrido-apa7'
CAPS=EVIDENCE/'apa7'
META=json.loads((ROOT/'docs/DATOS-INFORME.json').read_text(encoding='utf-8'))
RESULT=json.loads((WALK/'pruebas/resultados.json').read_text(encoding='utf-8'))
ORIGINAL=json.loads((EVIDENCE/'ejecucion-final/resultados.json').read_text(encoding='utf-8'))
FIRST=json.loads((EVIDENCE/'ejecucion/resultados.json').read_text(encoding='utf-8'))
RAW_STEPS=json.loads((WALK/'pasos.json').read_text(encoding='utf-8'))
OUT=ROOT/'output/pdf/Informe-SARSEG-Kubernetes-P2.pdf'
TITLE='Configuración de un clúster Kubernetes y despliegue de Grafana para SARSEG con Deployment y ReplicaSet'
FONT_DIR=Path('C:/Windows/Fonts')
for name,file in [('TimesAPA','times.ttf'),('TimesAPABold','timesbd.ttf'),('TimesAPAItalic','timesi.ttf'),('TimesAPABoldItalic','timesbi.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONT_DIR/file)))
pdfmetrics.registerFontFamily('TimesAPA',normal='TimesAPA',bold='TimesAPABold',italic='TimesAPAItalic',boldItalic='TimesAPABoldItalic')
WIDTH,HEIGHT=letter
MARGIN=72
TEXT_WIDTH=WIDTH-2*MARGIN
TEXT_HEIGHT=HEIGHT-2*MARGIN
STYLES={
 'body':ParagraphStyle('APA body',fontName='TimesAPA',fontSize=12,leading=24,alignment=TA_LEFT,firstLineIndent=36,spaceBefore=0,spaceAfter=0),
 'plain':ParagraphStyle('APA plain',fontName='TimesAPA',fontSize=12,leading=24,alignment=TA_LEFT,spaceBefore=0,spaceAfter=0),
 'center':ParagraphStyle('APA center',fontName='TimesAPA',fontSize=12,leading=24,alignment=TA_CENTER,spaceBefore=0,spaceAfter=0),
 'title':ParagraphStyle('APA title',fontName='TimesAPABold',fontSize=12,leading=24,alignment=TA_CENTER,spaceBefore=0,spaceAfter=0,keepWithNext=True),
 'h2':ParagraphStyle('APA level 2',fontName='TimesAPABold',fontSize=12,leading=24,alignment=TA_LEFT,spaceBefore=0,spaceAfter=0,keepWithNext=True),
 'number':ParagraphStyle('APA figure number',fontName='TimesAPABold',fontSize=12,leading=24,spaceBefore=0,spaceAfter=0,keepWithNext=True),
 'figure_title':ParagraphStyle('APA figure title',fontName='TimesAPAItalic',fontSize=12,leading=24,spaceBefore=0,spaceAfter=0,keepWithNext=True),
 'note':ParagraphStyle('APA figure note',fontName='TimesAPA',fontSize=12,leading=24,spaceBefore=0,spaceAfter=0),
 'reference':ParagraphStyle('APA reference',fontName='TimesAPA',fontSize=12,leading=24,alignment=TA_LEFT,leftIndent=36,firstLineIndent=-36,spaceBefore=0,spaceAfter=0,splitLongWords=True),
 'cell':ParagraphStyle('APA table cell',fontName='TimesAPA',fontSize=10.5,leading=14,spaceBefore=0,spaceAfter=0),
 'cell_head':ParagraphStyle('APA table header',fontName='TimesAPABold',fontSize=10.5,leading=14,spaceBefore=0,spaceAfter=0),
}
STORY=[]
MD=[]
FIGURES=[]


def para(text,style='body',target=None):
    p=Paragraph(text,STYLES[style])
    (STORY if target is None else target).append(p)
    return p


def section(text,new_page=False):
    if new_page: STORY.append(PageBreak())
    para(escape(text),'title')
    MD.append('\n## '+text+'\n')


def prose(text):
    para(text)
    MD.append(text)


def href(label,url):
    return '<link href="'+escape(url,quote=True)+'" color="black">'+escape(label)+'</link>'


def apa_table(number,title,headers,rows,widths):
    para('Tabla '+str(number),'number')
    para(escape(title),'figure_title')
    data=[[Paragraph(escape(str(c)),STYLES['cell_head']) for c in headers]]
    data.extend([Paragraph(escape(str(c)),STYLES['cell']) for c in row] for row in rows)
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([
      ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
      ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
      ('LINEABOVE',(0,0),(-1,0),.8,colors.black),('LINEBELOW',(0,0),(-1,0),.6,colors.black),
      ('LINEBELOW',(0,-1),(-1,-1),.8,colors.black),
    ]))
    STORY.append(t)
    STORY.append(Spacer(1,24))
    MD.extend(['\n**Tabla '+str(number)+'. '+title+'**\n','| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|'])
    MD.extend('| '+' | '.join(str(x) for x in row)+' |' for row in rows)


def photo_step(step_title,description,path,figure_title,note,source):
    number=len(FIGURES)+1
    if 'Figura '+str(number) not in description:
        description=description.rstrip('. ')+' (Figura '+str(number)+').'
    path=Path(path)
    assert path.exists(),path
    flows=[]
    para(escape(step_title),'h2',flows)
    para(description,'body',flows)
    flows.append(Spacer(1,24))
    para('Figura '+str(number),'number',flows)
    para(escape(figure_title),'figure_title',flows)
    note_para=Paragraph('<i>Nota.</i> '+note,STYLES['note'])
    overhead=sum(f.wrap(TEXT_WIDTH,TEXT_HEIGHT)[1] for f in flows)+note_para.wrap(TEXT_WIDTH,TEXT_HEIGHT)[1]+4
    with PillowImage.open(path) as im: iw,ih=im.size
    max_height=TEXT_HEIGHT-overhead
    assert max_height>180,(step_title,max_height)
    scale=min(TEXT_WIDTH/iw,max_height/ih)
    picture=Image(str(path),width=iw*scale,height=ih*scale,hAlign='LEFT')
    flows.extend([picture,note_para])
    STORY.extend([PageBreak(),KeepTogether(flows)])
    rel=path.relative_to(ROOT).as_posix()
    FIGURES.append({'number':number,'title':figure_title,'image':rel,'source':source,'step':step_title})
    MD.extend(['\n### '+step_title+'\n',description,f'\n**Figura {number}**\n\n*{figure_title}*\n',f'![{figure_title}]({path.relative_to(ROOT/"docs").as_posix()})' if path.is_relative_to(ROOT/'docs') else f'![{figure_title}]({rel})','\nNota. '+note+'\n'])


def bit_step(report_number,raw_id,title,description):
    photo_step(f'Paso {report_number} {title}',description,CAPS/f'paso-{raw_id}.jpg',
               RAW_STEPS[int(raw_id)-1]['title'],
               'Captura del visor de la bitácora del paso '+raw_id+'. La salida original se conserva en pasos.json.',
               'docs/evidencias/recorrido-apa7/pasos.json#'+raw_id)


def page_number(canvas,doc):
    canvas.saveState()
    canvas.setFont('TimesAPA',12)
    canvas.setFillColor(colors.black)
    canvas.drawRightString(WIDTH-MARGIN,HEIGHT-36,str(doc.page))
    canvas.restoreState()


class APAReport(BaseDocTemplate):
    def afterFlowable(self,flowable):
        if isinstance(flowable,Paragraph) and flowable.style.name in ['APA title','APA level 2']:
            self.outline_count=getattr(self,'outline_count',0)+1
            key='seccion-'+str(self.outline_count)
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(flowable.getPlainText(),key,level=0,closed=False)


def main():
    STORY.clear()
    MD.clear()
    FIGURES.clear()
    assert RESULT['success'] and len(RESULT['checks'])==11
    assert RESULT['http_sampling']['failed']==0
    STORY.append(Spacer(1,12))
    STORY.append(Image(str(ROOT/'docs/assets/udla-logo-oficial.png'),width=300,height=100,hAlign='CENTER'))
    STORY.append(Spacer(1,24))
    para(TITLE,'title')
    STORY.append(Spacer(1,24))
    for key in ['autor','carrera','universidad','asignatura','docente','fecha']:
        para(escape(META[key]),'center')
    STORY.append(Spacer(1,24))
    para('Configuración de clúster Docker Swarm o Kubernetes<br/>15% P2','center')
    MD.extend(['# '+TITLE,'\n'+META['autor']+'\n','\n'+META['universidad']+' · '+META['carrera']+'\n','\nAsignatura: '+META['asignatura']+'\n','\nDocente: '+META['docente']+'\n','\n'+META['fecha']+'\n'])

    section(TITLE,True)
    prose('El presente informe documenta el despliegue de Grafana en un clúster local de Kubernetes para el contexto de SARSEG, sistema de registro de asistencia con API .NET, PostgreSQL e interfaz Ionic/Angular. La práctica aplica Deployment y ReplicaSet, comprueba la ejecución de los Pods y expone la plataforma mediante un Service NodePort. La secuencia incluye preparación, configuración, despliegue, acceso, escalado, recuperación, actualización y reversión.')
    prose('Se eligió Grafana porque es una plataforma distinta del Nginx utilizado como primer Pod en el material de clase (<i>Intro Kubernetes</i>, s. f.). Grafana permite visualizar métricas operativas y relacionarlas con el funcionamiento de un sistema. En esta entrega se observan recursos reales de la infraestructura del laboratorio; la API privada de SARSEG no se despliega ni se presenta como instrumentada.')
    para('Objetivo y entregable','h2')
    prose('El objetivo es demostrar cómo un Deployment administra ReplicaSets y cómo estos mantienen el número de Pods deseado. Se entrega un informe con capturas de principio a fin, configuración reproducible, interpretación de resultados, usos y enlace a un repositorio público con ramas y commits por avance.')
    para('Repositorio público','h2')
    para(href(REPO,REPO),'plain')
    MD.append('\nRepositorio público: '+REPO+'\n')

    section('Fundamento técnico',True)
    para('Pod','h2')
    prose('Un Pod agrupa los contenedores que Kubernetes programa y ejecuta en un nodo. En esta práctica cada Pod de Grafana contiene una instancia de la imagen grafana/grafana:12.3.0. Se exige que esté Ready para recibir tráfico; observar únicamente el estado Running no demuestra disponibilidad de la aplicación (Kubernetes, s. f.-b).')
    para('Deployment','h2')
    prose('Deployment declara la cantidad de réplicas y la plantilla de los Pods. También coordina las revisiones y la actualización gradual. El laboratorio establece dos réplicas, RollingUpdate, maxSurge de uno y maxUnavailable de cero. Cambiar spec.template genera una revisión, mientras que escalar modifica la cantidad deseada sin cambiar la plantilla (Kubernetes, s. f.-a).')
    para('ReplicaSet','h2')
    prose('ReplicaSet mantiene el número de Pods de una plantilla mediante un selector. Su aplicación se comprueba con ownerReferences, escalado y reposición de un Pod con UID nuevo. No se crea otro ReplicaSet independiente con el mismo selector, porque el Deployment ya administra ese controlador (Kubernetes, s. f.-c).')
    para('Service y punto de acceso','h2')
    prose('Service proporciona un punto estable de acceso a los Pods seleccionados. Aquí el NodePort 30300 se comunica con el puerto 3000 de Grafana. kind publica ese NodePort en Windows mediante un mapeo de puerto limitado a loopback (Kubernetes, s. f.-d; Kubernetes SIGs, s. f.).')

    section('Diseño y método de documentación',True)
    prose('La implementación original permanece en el contexto kind-sarseg-p2 y el puerto 13000. Para capturar el inicio desde cero se realizó una reproducción separada: kind-sarseg-p2-evidencia y puerto 13010. Solo cambian el nombre del clúster y el puerto del equipo; los manifiestos de la plataforma y las versiones son los mismos. La Tabla 1 resume la configuración.')
    apa_table(1,'Componentes y decisiones de configuración',['Componente','Configuración'],[
      ['Clúster','kind 0.27.0, Kubernetes 1.32.2, un control plane y dos workers'],
      ['Namespace','sarseg-observabilidad'],['Grafana','Imagen 12.3.0 y dos réplicas distribuidas entre workers'],
      ['Métricas','Prometheus 3.5.0 y kube-state-metrics 2.16.0'],
      ['Disponibilidad','Probes /api/health; minReadySeconds de cinco'],
      ['Actualización','RollingUpdate; maxSurge: 1 y maxUnavailable: 0'],
      ['Terminación','preStop de diez segundos y gracia de treinta segundos'],
      ['Exposición','NodePort 30300; localhost 13000 original o 13010 reproducción'],
    ],[116,TEXT_WIDTH-116])
    section('Método y trazabilidad de la evidencia',True)
    prose('Los tableros y las fuentes de datos se provisionan desde ConfigMaps versionados, siguiendo el mecanismo de configuración por archivos de Grafana (Grafana Labs, s. f.-a). El proceso registra las versiones utilizadas, crea el clúster, aplica los recursos, espera disponibilidad y ejecuta las pruebas de controladores y exposición.')
    prose('Se conservan comandos, salidas, fechas UTC y estados JSON. Las capturas de la bitácora muestran esos registros en un visor de lectura; se distinguen de las capturas directas de GitHub y Grafana. Las imágenes del tablero durante las pruebas se exportan mediante el servicio oficial de renderizado de Grafana (Grafana Labs, s. f.-c).')
    prose('Las evidencias de la primera implementación y las de la reproducción se mantienen separadas. Las referencias de propietario y los UIDs pertenecen a cada ejecución, por lo que no se combinan como si correspondieran al mismo Pod. El resultado se interpreta junto con los datos originales y no únicamente con una imagen.')
    prose('El logotipo de la carátula se obtuvo del recurso institucional oficial de la Universidad de Las Américas (s. f.). Se conserva su proporción y color; su inclusión es la adaptación institucional solicitada para esta entrega académica.')

    section('Correspondencia con la consigna',True)
    prose('La Tabla 2 vincula cada requisito con una evidencia concreta. Las imágenes siguientes están ordenadas por el proceso de implementación, no por la fecha de consulta de una página del repositorio.')
    apa_table(2,'Requisitos y evidencias verificables',['Requisito','Cumplimiento y evidencia'],[
      ['Plataforma distinta de la vista en clase','Grafana; imagen, Pods Ready y tablero visible'],
      ['Aplicar Deployment','Manifiesto, dos réplicas, actualización y rollback'],
      ['Aplicar ReplicaSet','Propietario de Pods, mismo controlador al escalar y reposición con UID nuevo'],
      ['Indicar usos','Monitoreo de infraestructura y usos propuestos para SARSEG'],
      ['Repositorio público','Enlace accesible sin autenticación y captura de la etiqueta Public'],
      ['Capturas de todo el proceso','Requisitos, creación, configuración, despliegue, acceso y pruebas'],
      ['Evidenciar configuración y exposición','YAML, kubectl apply, estado Ready, Service y respuesta HTTP'],
      ['Ramas y commits por avance','Ramas preservadas, mensajes de commits y pull requests separados'],
    ],[145,TEXT_WIDTH-145])
    prose('Las capturas acreditan visibilidad, comandos y funcionamiento. Los archivos originales y sus hashes permiten contrastar cada figura con el registro conservado en docs/evidencias (Suárez, 2026).')

    photo_step('Paso 1 Acceso al repositorio público','Se creó el repositorio de la práctica. En la Figura 1 se observa su visibilidad Public, la estructura de carpetas y el acceso al código y a las evidencias.',CAPS/'01-repositorio-publico.jpg','Repositorio público de la práctica','Captura de GitHub consultado sin iniciar sesión. El enlace está incluido al comienzo del informe.',REPO)
    photo_step('Paso 2 Organización por ramas','Los avances se separaron en infraestructura, métricas, pruebas e informe. Se conservaron las ramas y se agregó una rama para esta ampliación documental; cada cambio mantiene su propio historial.',CAPS/'02-ramas-avances.jpg','Ramas conservadas por avance','Captura de la vista Branches. Las referencias de los pull requests permiten revisar las integraciones.',REPO+'/branches')
    photo_step('Paso 3 Historial de commits','El historial registra cambios de configuración, automatización, correcciones y entrega. Esta separación permite reconocer qué se modificó y evita concentrar toda la actividad en un único commit.',CAPS/'03-historial-commits.jpg','Historial de cambios y merges','Fragmento del historial de main. El repositorio conserva los commits completos y sus fechas reales.',REPO+'/commits/main/')
    bit_step(4,'01','Verificación de requisitos','Se verificaron Docker Server 28.1.1, kind 0.27.0 y kubectl 1.32.2. Esta comprobación confirma que existe un motor Linux accesible antes de crear los nodos.')
    bit_step(5,'02','Definición del clúster','El archivo declara un control plane y dos workers. extraPortMappings une NodePort 30300 con el puerto local 13010, limitado a 127.0.0.1 para la reproducción.')
    bit_step(6,'03','Creación desde cero','Se ejecutó kind create cluster con el archivo de evidencias. La salida registra preparación de nodos, inicio del control plane, red, unión de workers y estado listo.')
    bit_step(7,'04','Verificación de nodos Ready','Antes de desplegar la plataforma se consultó kubectl get nodes. Los tres nodos aparecen Ready y utilizan Kubernetes 1.32.2; crear el clúster no sustituye esta comprobación.')
    bit_step(8,'05','Configuración del Deployment','El manifiesto declara replicas: 2, selector app=grafana y estrategia RollingUpdate. El selector coincide con las etiquetas de la plantilla, condición necesaria para administrar los Pods correctos.')
    bit_step(9,'06','Aplicación de los recursos','kubectl apply -k k8s creó el namespace, permisos de lectura, ConfigMaps, Services y Deployments. La configuración declarativa permite repetir el despliegue desde los mismos archivos.')
    bit_step(10,'07','Espera de disponibilidad','Se esperó el rollout de Grafana, Prometheus y kube-state-metrics. La comprobación exige réplicas disponibles y evita declarar éxito cuando solo existen objetos creados o contenedores arrancando.')
    bit_step(11,'08','Comprobación de Deployment y ReplicaSet','Grafana muestra dos réplicas disponibles. Su ReplicaSet presenta DESIRED, CURRENT y READY iguales a dos; el script también comprueba la propiedad del controlador mediante ownerReferences.')
    bit_step(12,'09','Comprobación de los Pods','Los dos Pods de Grafana aparecen Ready y se distribuyen en workers distintos. El reparto procede de la afinidad y de la restricción de distribución definidas en el Deployment.')
    bit_step(13,'10','Configuración de Service','El Service NodePort selecciona app=grafana, publica el puerto 3000 y reserva NodePort 30300. El mapeo de kind permite acceder desde Windows sin ejecutar port-forward.')
    bit_step(14,'11','Validación del acceso HTTP','Se consultó el Service y se solicitó /api/health a través de 127.0.0.1:13010. La respuesta HTTP 200 y database: ok acreditan acceso desde el equipo a la plataforma expuesta.')
    photo_step('Paso 15 Consulta directa del endpoint','El endpoint de salud se abrió también en el navegador. La respuesta identifica Grafana 12.3.0 y confirma el estado de su base interna; no representa la salud de la API privada de SARSEG.',CAPS/'25-salud-http-navegador.jpg','Respuesta real de salud de Grafana','Captura directa de /api/health en el puerto de la reproducción. El código HTTP se conserva en la bitácora.','http://127.0.0.1:13010/api/health')
    photo_step('Paso 16 Apertura de la plataforma','Grafana cargó el tablero provisionado con dos réplicas deseadas y disponibles. Prometheus recoge métricas reales del namespace; las fuentes activas aparecen con valor uno.',WALK/'pruebas/capturas/01-grafana-inicial.png','Tablero inicial de Grafana','Exportación real de Grafana Image Renderer durante la reproducción; no se emplean métricas de negocio simuladas.','docs/evidencias/recorrido-apa7/pruebas/capturas/01-grafana-inicial.png')
    bit_step(17,'12','Ejecución del protocolo','Se ejecutó test_lab.py con contexto y puerto explícitos. El protocolo conserva once comprobaciones: clúster, propiedad, exposición, métricas, RBAC, escalado, recuperación, actualización, rollback y muestreo HTTP.')
    bit_step(18,'13','Escalado a tres réplicas','kubectl scale elevó Grafana de dos a tres Pods Ready. El UID del ReplicaSet se mantuvo: cambió la cantidad deseada, pero no la plantilla del Deployment.')
    photo_step('Paso 19 Observación del escalado','El tablero mostró tres réplicas deseadas y disponibles después de esperar el estado Ready. La variación del gráfico corresponde al cambio aplicado en Kubernetes y recogido por Prometheus.',WALK/'pruebas/capturas/02-grafana-tres-replicas.png','Grafana con tres réplicas','Exportación tomada durante la fase de escalado. El estado JSON de la misma fase está preservado.','docs/evidencias/recorrido-apa7/pruebas/02-escalado-tres.json')
    bit_step(20,'14','Restauración de dos réplicas','Se redujo el Deployment a dos réplicas y se verificó que ambas quedaran disponibles. La reducción controlada permite observar el ajuste al estado deseado antes de la prueba de recuperación.')
    bit_step(21,'15','Reposición de un Pod','Se eliminó un Pod de prueba y ReplicaSet creó otro con un UID diferente. El registro conserva el objeto eliminado, su reemplazo y el tiempo hasta recuperar dos réplicas disponibles.')
    bit_step(22,'16','Actualización gradual','Se cambió la anotación de spec.template de v1 a v2-prueba-p2. El Deployment creó un ReplicaSet nuevo y completó RollingUpdate; la imagen continuó siendo Grafana 12.3.0.')
    bit_step(23,'17','Rollback','rollout undo restauró la revisión inicial de esta reproducción. El ReplicaSet original volvió a dos réplicas y el de la plantilla de prueba quedó en cero, conservado para el historial.')
    photo_step('Paso 24 Verificación final en Grafana','Después del rollback se comprobó nuevamente el tablero en el navegador. Se observan dos réplicas disponibles, cuatro Pods de infraestructura y las tres fuentes activas.',CAPS/'26-grafana-final-navegador.jpg','Grafana después de la reversión','Captura directa del navegador al concluir el recorrido. El historial del gráfico conserva las variaciones de las pruebas.','http://127.0.0.1:13010/d/sarseg-operacion/sarseg')
    bit_step(25,'18','Revisión del resultado registrado','El archivo final confirma once comprobaciones aprobadas y 109 de 109 solicitudes HTTP correctas. Se conserva cada muestra y se comprueba el resultado del protocolo, además de observar las capturas.')
    photo_step('Paso 26 Verificación independiente en CI','GitHub Actions creó otro clúster en Linux y ejecutó el protocolo. La ejecución mostrada terminó correctamente y conserva su artefacto de registros; es una validación separada de la computadora Windows.',CAPS/'24-github-actions.jpg','Ejecución exitosa de GitHub Actions','Captura de una ejecución pública del workflow. El enlace permite consultar la conclusión y el artefacto.',REPO+'/actions/runs/42964113968')

    section('Resultados e interpretación',True)
    prose('La Tabla 3 resume los resultados de la reproducción documentada.')
    apa_table(3,'Resultados de la reproducción documentada',['Prueba','Resultado observado'],[
      ['Clúster','Tres nodos Ready'],['Estado inicial y final','Dos réplicas disponibles en workers distintos'],
      ['Escalado','Dos a tres y retorno a dos; mismo UID de ReplicaSet'],
      ['Recuperación','Pod nuevo con UID diferente; '+str(RESULT['recovery']['elapsed_seconds'])+' segundos medidos'],
      ['Actualización','Nuevo ReplicaSet '+RESULT['rollout']['after_rs']],
      ['Rollback','Reactivación de '+RESULT['rollout']['rollback_rs']],
      ['HTTP','109 de 109 muestras con HTTP 200 y database: ok'],
      ['Permisos','kube-state-metrics puede listar Pods y no puede listar Secrets'],
    ],[125,TEXT_WIDTH-125])
    prose('La implementación original tuvo una primera ejecución con 110 respuestas correctas de 111 y un RemoteDisconnected durante el rollout. Se añadió preStop de diez segundos para permitir el drenaje y se repitió el protocolo: la ejecución original final obtuvo 113 de 113 respuestas correctas. La reproducción de las figuras obtuvo 109 de 109. Son ejecuciones distintas, identificadas por contexto y fechas; no se mezclan sus UIDs ni sus mediciones.')
    prose('Se midió la salud aproximadamente cada segundo. Las muestras correctas no garantizan continuidad entre solicitudes. El cambio de plantilla prueba el rollout y el rollback; la imagen de Grafana mantuvo la versión 12.3.0.')

    section('Usos de la plataforma en SARSEG',True)
    prose('En el alcance implementado, Grafana muestra réplicas deseadas, disponibles y actualizadas, cantidad de Pods de infraestructura, reinicios y disponibilidad de las fuentes. Esto permite reconocer si un cambio de configuración se completó y si el sistema recuperó la cantidad esperada de instancias. La Tabla 4 distingue esos usos de las ampliaciones propuestas.')
    apa_table(4,'Usos actuales y ampliaciones posibles',['Uso','Aplicación al sistema de asistencia','Estado'],[
      ['Infraestructura','Réplicas, Pods, reinicios y recuperación de Grafana','Implementado'],
      ['Atención de solicitudes','Latencia y errores HTTP de la API .NET','Requiere instrumentar SARSEG'],
      ['Reportes','Duración y fallos de generación de PDF o XLSX','Propuesto'],
      ['Base de datos','Conexiones, consultas lentas y errores de PostgreSQL','Propuesto'],
      ['Capacidad','Correlación con picos de entrada o salida de asistencia','Propuesto'],
    ],[90,235,TEXT_WIDTH-325])
    prose('Los usos futuros requieren métricas de la API y de sus dependencias. No se presentan marcas individuales, datos personales ni indicadores de estudiantes. La incorporación de SARSEG a este monitoreo debe distinguirse de la demostración de los controladores de Kubernetes, que sí fue ejecutada.')

    section('Limitaciones y conclusiones',True)
    prose('El laboratorio depende de una computadora, Docker Desktop y un único control plane por clúster. Las dos réplicas permiten demostrar reposición y actualización de Pods, pero no representan tolerancia al fallo del equipo. Prometheus usa una réplica y almacenamiento efímero; su historial se pierde si se elimina el entorno.')
    prose('Grafana utiliza SQLite independiente y efímera por Pod, mientras los dashboards y la fuente de datos se reconstruyen desde ConfigMaps. No se habilitan ediciones de tableros ni alertas persistentes. Una instalación productiva de Grafana con alta disponibilidad requiere una base PostgreSQL o MySQL compartida y un diseño de autenticación, almacenamiento y redundancia (Grafana Labs, s. f.-b).')
    prose('La actividad cumple los requisitos de desplegar una plataforma distinta del ejemplo de clase, aplicar Deployment y ReplicaSet, explicar usos y entregar configuración y capturas con repositorio público. La secuencia muestra creación del clúster, disponibilidad, exposición, escalado, reposición y reversión. Las evidencias originales y la reproducción documentada permiten verificar tanto el estado deseado como el comportamiento real de Kubernetes.')
    para('Acceso a la entrega','h2')
    para(href(REPO,REPO),'plain')
    prose('Los manifiestos están en cluster y k8s; los scripts están en scripts; las capturas, los estados y los comandos se encuentran en docs/evidencias. SHA256SUMS.txt permite contrastar los archivos. Las ramas y los pull requests preservan los avances y las correcciones, incluida esta ampliación del informe.')

    section('Referencias',True)
    refs=[
      'Grafana Labs. (s. f.-a). <i>Provision Grafana</i>. Recuperado el 11 de noviembre de 2026, de https://grafana.com/docs/grafana/latest/administration/provisioning/',
      'Grafana Labs. (s. f.-b). <i>Set up Grafana for high availability</i>. Recuperado el 11 de noviembre de 2026, de https://grafana.com/docs/grafana/latest/setup-grafana/set-up-for-high-availability/',
      'Grafana Labs. (s. f.-c). <i>Set up image rendering</i>. Recuperado el 11 de noviembre de 2026, de https://grafana.com/docs/grafana/latest/setup-grafana/image-rendering/',
      '<i>Intro Kubernetes</i>. (s. f.). [Diapositivas de clase]. Procesos de Software, UDLA Brightspace. https://udla.brightspace.com/d2l/home/870697',
      'Kubernetes. (s. f.-a). <i>Deployments</i>. Recuperado el 11 de noviembre de 2026, de https://kubernetes.io/docs/concepts/workloads/controllers/deployment/',
      'Kubernetes. (s. f.-b). <i>Pods</i>. Recuperado el 11 de noviembre de 2026, de https://kubernetes.io/docs/concepts/workloads/pods/',
      'Kubernetes. (s. f.-c). <i>ReplicaSet</i>. Recuperado el 11 de noviembre de 2026, de https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/',
      'Kubernetes. (s. f.-d). <i>Service</i>. Recuperado el 11 de noviembre de 2026, de https://kubernetes.io/docs/concepts/services-networking/service/',
      'Kubernetes SIGs. (s. f.). <i>Configuration</i>. kind. Recuperado el 11 de noviembre de 2026, de https://kind.sigs.k8s.io/docs/user/configuration/',
      'Suárez, J. (2026). <i>SARSEG Kubernetes P2</i> [Repositorio de código y evidencias]. GitHub. '+REPO,
      'Universidad de Las Américas. (s. f.). <i>Marca UDLA</i>. https://www.udla.edu.ec/la-udla/marca-udla/',
    ]
    for ref in refs:
        # Cada referencia es un bloque para conservar su sangria francesa.
        import re
        marked=re.sub(r'(https://[^ <]+)',lambda m:href(m.group(1),m.group(1)),ref)
        STORY.append(KeepTogether([Paragraph(marked,STYLES['reference'])]))
    MD.extend('\n'+r for r in refs)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    doc=APAReport(str(OUT),pagesize=letter,leftMargin=MARGIN,rightMargin=MARGIN,topMargin=MARGIN,bottomMargin=MARGIN,
        title=TITLE,author=META['autor'],subject='Procesos de Software APA 7 Deployment ReplicaSet Grafana')
    frame=Frame(MARGIN,MARGIN,TEXT_WIDTH,TEXT_HEIGHT,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id='APA7',frames=[frame],onPage=page_number,pagesize=letter)])
    doc.build(STORY)
    (ROOT/'docs/INFORME.md').write_text('\n\n'.join(MD),encoding='utf-8',newline='\n')
    (ROOT/'docs/INDICE-FIGURAS.json').write_text(json.dumps(FIGURES,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps({'pdf':str(OUT),'capturas':len(FIGURES),'autor':META['autor']},ensure_ascii=False))


if __name__=='__main__':
    main()
