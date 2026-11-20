"""APA 7 student report with authentic native-interface screenshots."""
from html import escape
import json
from pathlib import Path
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Flowable, Frame, Image, KeepTogether, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle

LAB=Path(__file__).resolve().parents[1]
E=LAB/'docs/evidencias'
WALK=E/'capturas-reales'
CAPS=WALK
OUT=LAB/'output/pdf/Informe-SARSEG-Spinnaker-P2.pdf'
META=json.loads((LAB/'docs/DATOS-INFORME.json').read_text(encoding='utf-8'))
STEPS=json.loads((WALK/'pasos.json').read_text(encoding='utf-8'))

RESULTS=json.loads((E/'results.json').read_text())
STATE=json.loads((E/'git-state.json').read_text())
REPO='https://github.com/JOURT1/SARSEG-Kubernetes-P2'
TITLE='Automatización de la configuración continua de SARSEG mediante Spinnaker y Kubernetes'
WIDTH,HEIGHT=letter
MARGIN=72
TW=WIDTH-144
TH=HEIGHT-144
for face,file in [('TimesAPA','times.ttf'),('TimesAPABold','timesbd.ttf'),('TimesAPAItalic','timesi.ttf'),('TimesAPABoldItalic','timesbi.ttf')]:
    pdfmetrics.registerFont(TTFont(face,str(Path('C:/Windows/Fonts')/file)))
pdfmetrics.registerFontFamily('TimesAPA',normal='TimesAPA',bold='TimesAPABold',italic='TimesAPAItalic',boldItalic='TimesAPABoldItalic')
S={
'body':ParagraphStyle('APA body',fontName='TimesAPA',fontSize=12,leading=24,firstLineIndent=36),
'plain':ParagraphStyle('APA plain',fontName='TimesAPA',fontSize=12,leading=24),
'center':ParagraphStyle('APA center',fontName='TimesAPA',fontSize=12,leading=24,alignment=TA_CENTER),
'title':ParagraphStyle('APA title',fontName='TimesAPABold',fontSize=12,leading=24,alignment=TA_CENTER,keepWithNext=True),
'step':ParagraphStyle('APA step',fontName='TimesAPABold',fontSize=12,leading=24,keepWithNext=True),
'figure':ParagraphStyle('APA figure',fontName='TimesAPABold',fontSize=12,leading=24,keepWithNext=True),
'figure_title':ParagraphStyle('APA figure title',fontName='TimesAPAItalic',fontSize=12,leading=24,keepWithNext=True),
'note':ParagraphStyle('APA note',fontName='TimesAPA',fontSize=12,leading=24),
'reference':ParagraphStyle('APA reference',fontName='TimesAPA',fontSize=12,leading=24,leftIndent=36,firstLineIndent=-36,splitLongWords=True),
'cell':ParagraphStyle('APA cell',fontName='TimesAPA',fontSize=10.5,leading=14),
'cell_bold':ParagraphStyle('APA cell bold',fontName='TimesAPABold',fontSize=10.5,leading=14)}
STORY=[]
MD=[]
FIGURES=[]
def para(text,style='body',target=None):
    p=Paragraph(text,S[style]);(STORY if target is None else target).append(p);return p
def prose(text):
    para(text);MD.append(text)
def heading(title,new=False):
    if new:STORY.append(PageBreak())
    para(escape(title),'title');MD.append('\n## '+title+'\n')
def table(number,title,headers,rows,widths):
    para('Tabla '+str(number),'figure');para(escape(title),'figure_title')
    data=[[Paragraph(escape(str(x)),S['cell_bold']) for x in headers]]
    data.extend([Paragraph(escape(str(x)),S['cell']) for x in row] for row in rows)
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('LINEABOVE',(0,0),(-1,0),.8,colors.black),('LINEBELOW',(0,0),(-1,0),.6,colors.black),('LINEBELOW',(0,-1),(-1,-1),.8,colors.black)]))
    STORY.append(t)
    MD.extend(['\n**Tabla '+str(number)+'. '+title+'**\n','| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|'])
    MD.extend('| '+' | '.join(str(x) for x in row)+' |' for row in rows)
def photo(step):
    n=step['number'];path=CAPS/step['file'];assert path.exists(),path
    flows=[]
    if n==1:para('Procedimiento paso a paso','title',flows)
    para(f"Paso {n}. {escape(step['title'])}",'step',flows)
    para(step['description']+f' (Figura {n}).','body',flows)
    flows.append(Spacer(1,12))
    para('Figura '+str(n),'figure',flows)
    para(escape(step['title']),'figure_title',flows)
    note='Captura directa de '+('GitHub' if 'github.com' in step['source'] else 'SARSEG' if ':14800' in step['source'] else 'Spinnaker Deck' if ':14900' in step['source'] else 'Headlamp conectado al clúster local')+'. Tomada el 20 de noviembre de 2026. Elaboración propia. Se conserva la imagen completa, sin modificar su contenido.'
    np=Paragraph('<i>Nota.</i> '+escape(note),S['note'])
    overhead=sum(f.wrap(TW,TH)[1] for f in flows)+np.wrap(TW,TH)[1]+8
    with PILImage.open(path) as src:iw,ih=src.size
    scale=min(TW/iw,(TH-overhead)/ih)
    assert scale>0,(n,overhead)
    im=Image(str(path),width=iw*scale,height=ih*scale,hAlign='LEFT')
    flows.extend([im,Spacer(1,8),np]);STORY.extend([PageBreak(),KeepTogether(flows)])
    FIGURES.append({**step,'image':path.relative_to(LAB).as_posix(),'note':note})
    MD.extend(['\n### Paso '+str(n)+'. '+step['title']+'\n',step['description'],'\n**Figura '+str(n)+'**\n\n*'+step['title']+'*\n','!['+step['title']+'](evidencias/capturas-reales/'+step['file']+')','\nNota. '+note+' Fuente: '+step['source']+'\n'])

def page_number(c,doc):
    c.saveState();c.setFont('TimesAPA',12);c.drawRightString(WIDTH-MARGIN,HEIGHT-36,str(doc.page));c.restoreState()
class APAReport(BaseDocTemplate):
    def afterFlowable(self,f):
        if isinstance(f,Paragraph) and f.style.name in ['APA title','APA step']:
            self.counter=getattr(self,'counter',0)+1;k='section-'+str(self.counter)
            self.canv.bookmarkPage(k);self.canv.addOutlineEntry(f.getPlainText(),k,level=0,closed=False)
REFERENCES=[
('American Psychological Association. (s. f.-a). <i>Figure setup.</i>','https://apastyle.apa.org/style-grammar-guidelines/tables-figures/figures'),
('American Psychological Association. (s. f.-b). <i>Title page setup.</i>','https://apastyle.apa.org/style-grammar-guidelines/paper-format/title-page'),
('Headlamp. (s. f.). <i>In-cluster.</i>','https://headlamp.dev/docs/latest/installation/in-cluster/'),
('Docker. (s. f.). <i>Docker Desktop.</i> Docker Docs.','https://docs.docker.com/desktop/'),
('JOURT1. (2026a). <i>Resultados y evidencias originales del laboratorio SARSEG con Spinnaker</i> [Conjunto de datos]. GitHub.',REPO+'/tree/main/spinnaker/docs/evidencias'),
('JOURT1. (2026b). <i>SARSEG Kubernetes P2: Laboratorio local de configuración continua con Spinnaker</i> [Repositorio de código]. GitHub.',REPO+'/tree/main/spinnaker'),
('Kubernetes. (s. f.-a). <i>Deployments.</i>','https://kubernetes.io/docs/concepts/workloads/controllers/deployment/'),
('Kubernetes. (s. f.-b). <i>Horizontal Pod autoscaling.</i>','https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/'),
('Kubernetes. (s. f.-c). <i>Resource management for Pods and containers.</i>','https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/'),
('Kubernetes. (s. f.-d). <i>Service.</i>','https://kubernetes.io/docs/concepts/services-networking/service/'),
('Kubernetes SIGs. (s. f.-a). <i>Configuration.</i> kind.','https://kind.sigs.k8s.io/docs/user/configuration/'),
('Kubernetes SIGs. (s. f.-b). <i>Metrics Server</i> (Versión 0.8.1) [Software]. GitHub.','https://github.com/kubernetes-sigs/metrics-server/tree/v0.8.1'),
('Spinnaker. (2026). <i>Spinnaker Kustomize</i> (Versión 2026.4.1) [Software]. GitHub.','https://github.com/spinnaker/spinnaker/tree/1b3ed435fe5341b41dcbbdce999cb771145166a8/spinnaker-kustomize'),
('Spinnaker. (s. f.-a). <i>HTTP file.</i>','https://spinnaker.io/docs/reference/artifacts/types/http-file/'),
('Spinnaker. (s. f.-b). <i>Kubernetes provider overview.</i>','https://spinnaker.io/docs/reference/providers/kubernetes/'),
('Universidad de Las Américas. (s. f.). <i>Marca UDLA.</i>','https://www.udla.edu.ec/la-udla/marca-udla/')]
def main():
    assert len(STEPS)==23 and len(RESULTS)==11 and all(x['passed'] for x in RESULTS)
    STORY.clear();MD.clear();FIGURES.clear()
    STORY.append(Spacer(1,12));STORY.append(Image(str(LAB/'docs/assets/udla-logo-oficial.png'),width=270,height=90,hAlign='CENTER'))
    STORY.append(Spacer(1,24));para(TITLE,'title');STORY.append(Spacer(1,24))
    for key in ['autor','carrera','universidad','asignatura','docente','fecha']:para(escape(META[key]),'center')
    STORY.append(Spacer(1,24));para(escape(META['actividad']),'center')
    STORY.append(Spacer(1,24));para('<b>Repositorio público</b>','center')
    para('<link href="'+REPO+'/tree/main/spinnaker">'+REPO+'</link>','center')
    MD.extend(['# '+TITLE,'\n'+META['autor']+'\n','\n'+META['universidad']+' · '+META['carrera']+'\n','\nAsignatura: '+META['asignatura']+'\n','\nDocente: '+META['docente']+'\n','\n'+META['fecha']+'\n'])
    heading(TITLE,True)
    prose('El presente informe documenta el despliegue automatizado de SARSEG en Kubernetes mediante Spinnaker. Se adapta la consigna de Argo CD a la herramienta solicitada, conservando Git como fuente de los manifiestos Deployment, Service NodePort y Horizontal Pod Autoscaler. La implementación incluye web Ionic/Angular, API ASP.NET Core y PostgreSQL de prueba (JOURT1, 2026b).')
    prose('La evidencia comprende preparación, configuración, registro de la aplicación, ejecución del pipeline, publicación de un cambio Git y escalamiento por consumo real de CPU. Los resultados originales conservan once comprobaciones aprobadas y la secuencia de réplicas 2 a 5 y de regreso a 2 (JOURT1, 2026a).')
    para('Objetivo general','step')
    prose('Implementar y verificar el despliegue automatizado de SARSEG desde Git mediante Spinnaker, usando recursos Kubernetes declarativos y escalamiento horizontal basado en CPU.')
    para('Objetivos específicos','step')
    prose('Configurar dos réplicas iniciales con recursos de CPU y memoria; exponer la aplicación por NodePort; habilitar Metrics Server y un HPA entre dos y cinco réplicas al 50% de CPU; comprobar el despliegue de un cambio Git y documentar cada paso con capturas y referencias.')
    heading('Fundamento técnico y adaptación de la consigna',True)
    prose('Un Deployment declara la plantilla y las réplicas de los Pods y administra sus revisiones (Kubernetes, s. f.-a). Un Service proporciona acceso estable a los Pods seleccionados; aquí se utiliza NodePort (Kubernetes, s. f.-d). El HPA ajusta las réplicas según métricas y calcula la utilización de CPU respecto de los requests configurados (Kubernetes, s. f.-b, s. f.-c).')
    prose('Spinnaker ejecuta el despliegue mediante un pipeline y su integración Kubernetes. Las etapas Deploy (Manifest) recuperan los archivos como artefactos HTTP. La referencia de cada archivo incorpora un SHA completo para que toda la ejecución use la misma revisión de Git (Spinnaker, s. f.-a, s. f.-b).')
    prose('Spinnaker no incorpora el mismo controlador Automated Sync de Argo CD. Se implementó un adaptador que consulta Git cada 20 segundos y solicita a Gate una ejecución cuando cambian los manifiestos. No ejecuta kubectl ni aplica recursos: el despliegue corresponde a Orca y Clouddriver. No se implementan corrección periódica de cambios manuales ni eliminación automática de recursos retirados de Git (JOURT1, 2026b).')
    prose('La anotación strategy.spinnaker.io/use-source-capacity conserva las réplicas existentes en despliegues posteriores. Así, Spinnaker no restablece dos instancias mientras el HPA administra la capacidad bajo carga (Spinnaker, s. f.-b).')
    heading('Método de implementación y documentación',True)
    prose('Se utilizó un clúster kind independiente dentro de Docker Desktop, sin crear servicios de nube. La plataforma mínima se basó en el instalador oficial de Spinnaker 2026.4.1. La Tabla 1 resume la configuración (Docker, s. f.; Kubernetes SIGs, s. f.-a; Spinnaker, 2026).')
    table(1,'Componentes y parámetros del laboratorio',['Componente','Configuración'],[
    ['Clúster','sarseg-spinnaker; Kubernetes v1.32.2; kind v0.27.0'],
    ['Spinnaker','2026.4.1; Deck, Gate, Orca, Clouddriver y Front50'],
    ['Apoyo','MySQL, Redis, API SARSEG y PostgreSQL de prueba'],
    ['Deployment web','Dos réplicas iniciales; puerto http/8080'],
    ['Requests / limits','CPU 25m / 250m; memoria 32Mi / 128Mi'],
    ['Service','NodePort 30380; port 80; targetPort http'],
    ['HPA','Mínimo 2; máximo 5; CPU 50%; reducción estable 60 s'],
    ['Acceso local','SARSEG 14800; Gate 14884; Deck 14900']],[120,TW-120])
    para('Trazabilidad y presentación de las figuras','step')
    prose('Las pruebas funcionales se realizaron entre el 19 y el 20 de noviembre de 2026. La ampliación documental se tomó el día 20. Se repitió la prueba de carga para capturar directamente las pantallas del HPA en dos, cinco y nuevamente dos réplicas. Todas las figuras de esta edición proceden de interfaces reales de GitHub, Spinnaker, Headlamp o SARSEG; no se utilizan visores documentales ni capturas de código. El índice registra URL, fecha UTC y huella SHA-256 de cada imagen.')
    prose('Se adopta carátula estudiantil, márgenes de 2,54 cm, Times New Roman de 12 puntos, interlineado doble, paginación superior y referencias con sangría francesa. Las figuras tienen número, título en cursiva y nota de fuente (American Psychological Association, s. f.-a, s. f.-b). El logotipo oficial es una adaptación institucional solicitada (Universidad de Las Américas, s. f.).')
    for step in STEPS:photo(step)
    heading('Resultados y discusión',True)
    labels=['Dos Pods iniciales Ready','Recursos y selectores coincidentes','Service NodePort accesible','HPA: mínimo 2, máximo 5 y CPU 50%','Web y API disponibles por HTTP','Login real HTTP 200','Métricas CPU/memoria disponibles','Nuevo SHA desplegado automáticamente','Tres etapas de Spinnaker SUCCEEDED','Incremento automático de 2 a 5','Reducción automática de 5 a 2']
    prose('Las once comprobaciones finalizaron correctamente. La Tabla 2 vincula cada condición con su resultado; las salidas completas se conservan en results.json y en los estados asociados del repositorio (JOURT1, 2026a).')
    table(2,'Verificaciones de integración de SARSEG y Spinnaker',['Comprobación','Resultado'],[[label,'Aprobado'] for label in labels],[350,118])
    STORY.append(Spacer(1,12))
    prose('El cambio Git verificado fue '+STATE['sha']+'. La ejecución '+STATE['execution'].removeprefix('/pipelines/')+' terminó en SUCCEEDED y aplicó la revisión esperada. La evidencia de carga muestra cinco Pods Ready; después de retirarla, Deployment y HPA volvieron a dos.')
    prose('La captura de esta edición registró 640% de utilización respecto de los requests. Esto no significa exceder el límite de CPU: el porcentaje se calcula sobre la solicitud de 25m por Pod. El objetivo del 50% equivale a 12,5m por Pod, por lo que la carga justificó el escalamiento (Kubernetes, s. f.-b, s. f.-c).')
    heading('Incidencias, límites y conclusiones',True)
    prose('La primera definición del pipeline no enlazó el artefacto esperado y terminó en TERMINAL. La corrección declaró el artefacto HTTP en la etapa y parametrizó su referencia con gitSha. Las ejecuciones posteriores verificaron los tres manifiestos. También se añadió una espera de PostgreSQL antes de iniciar la API para evitar fallos durante el arranque.')
    prose('La infraestructura se ejecuta en una computadora, con puertos limitados a loopback y configuración de desarrollo. La web y la API se construyen desde el repositorio privado original, cuyo código y credenciales no se publican. La reproducción completa requiere permiso para obtener ese código o disponer de las imágenes locales compiladas.')
    prose('Se cumplió el objetivo de desplegar SARSEG automáticamente desde Git con Spinnaker. El Deployment inició con dos réplicas, el Service permitió acceso por NodePort, Metrics Server suministró métricas y el HPA ajustó la capacidad de dos a cinco y nuevamente a dos. La detección Git quedó documentada como adaptación local con diferencias frente a Argo CD.')
    heading('Referencias',True)
    ordered_references=sorted(REFERENCES,key=lambda item:(item[0].split('. (')[0].casefold(),item[0]))
    for prefix,url in ordered_references:
        STORY.append(KeepTogether([Paragraph(prefix+' <link href="'+escape(url,quote=True)+'">'+escape(url)+'</link>',S['reference'])]))
        MD.append(prefix+' '+url+'\n')
    heading('Trazabilidad de la entrega',True)
    prose('El repositorio público reúne los tres manifiestos Kubernetes, el pipeline de Spinnaker, la configuración del laboratorio y este informe. La carpeta capturas-reales conserva las imágenes originales y un índice con fuente, fecha y huella de integridad. Los archivos de registros de las pruebas iniciales permanecen disponibles como material de respaldo, fuera de las figuras de esta edición.')
    prose('Headlamp se añadió únicamente para observar los recursos mediante una interfaz Kubernetes real. Usa una cuenta de servicio con permisos de lectura y un puerto limitado a la computadora local. No sustituye a Spinnaker: el pipeline continúa siendo el responsable de aplicar los manifiestos (Headlamp, s. f.; JOURT1, 2026b).')
    prose('Las credenciales y el código privado de la aplicación no forman parte de la entrega pública. La reproducción completa requiere acceso autorizado al repositorio original de SARSEG o a las imágenes compiladas. La implementación se conserva en ramas y commits separados.')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    doc=APAReport(str(OUT),pagesize=letter,leftMargin=72,rightMargin=72,topMargin=72,bottomMargin=72,title=TITLE,author=META['autor'],subject='Informe estudiantil APA 7 con 23 capturas reales de interfaces y referencias')
    frame=Frame(72,72,TW,TH,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0,id='apa')
    doc.addPageTemplates(PageTemplate(id='APA7',frames=[frame],onPage=page_number));doc.build(STORY)
    (LAB/'docs/INFORME.md').write_text('\n\n'.join(MD)+'\n',encoding='utf-8',newline='\n')
    (LAB/'docs/INDICE-FIGURAS.json').write_text(json.dumps(FIGURES,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(str(OUT)+'\n'+str(len(FIGURES))+' figuras; '+str(len(REFERENCES))+' referencias')
if __name__=='__main__':main()

