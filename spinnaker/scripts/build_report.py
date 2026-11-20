"""Build the delivery report from verified results and original screenshots."""
from datetime import datetime
from html import escape
import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from PIL import Image as PILImage

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "docs/evidencias"
OUT = ROOT / "output/pdf/Informe-SARSEG-Spinnaker-P2.pdf"
for face, file in [("Arial", "arial.ttf"), ("Arial-Bold", "arialbd.ttf")]:
    pdfmetrics.registerFont(TTFont(face, "C:/Windows/Fonts/" + file))
S = getSampleStyleSheet()
S.add(ParagraphStyle(name="TitleLab", fontName="Arial-Bold", fontSize=30, leading=36, textColor=colors.HexColor("#102d46"), spaceAfter=18))
S.add(ParagraphStyle(name="H1Lab", fontName="Arial-Bold", fontSize=21, leading=26, textColor=colors.HexColor("#102d46"), spaceAfter=15))
S.add(ParagraphStyle(name="BodyLab", fontName="Arial", fontSize=11, leading=16, spaceAfter=10))
S.add(ParagraphStyle(name="SmallLab", fontName="Arial", fontSize=9, leading=12, spaceAfter=7))
S.add(ParagraphStyle(name="CaptionLab", fontName="Arial", fontSize=9, leading=12, textColor=colors.HexColor("#40596b"), spaceAfter=8))
S.add(ParagraphStyle(name="CellLab", fontName="Arial", fontSize=10, leading=14))
STORY = []


def p(text, style="BodyLab"):
    STORY.append(Paragraph(text, S[style]))


def page(title):
    if STORY:
        STORY.append(PageBreak())
    p(title, "H1Lab")


def table(rows, widths):
    data = [[Paragraph(escape(str(x)), S["CellLab"]) for x in row] for row in rows]
    t = Table(data, colWidths=widths, hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e5eef4")), ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LINEBELOW", (0,0), (-1,0), .8, colors.HexColor("#6e92aa")), ("LINEBELOW", (0,1), (-1,-1), .3, colors.HexColor("#d7e0e6")),
        ("LEFTPADDING", (0,0), (-1,-1), 9), ("RIGHTPADDING", (0,0), (-1,-1), 9), ("TOPPADDING", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 8)]))
    STORY.append(t)


def figure(filename, caption, maxheight=370):
    path = E / filename
    with PILImage.open(path) as image:
        width, height = image.size
    factor = min(750 / width, maxheight / height)
    STORY.append(Image(str(path), width * factor, height * factor, hAlign="CENTER"))
    STORY.append(Spacer(1, 9))
    p(caption, "CaptionLab")


def footer(canvas, doc):
    canvas.setStrokeColor(colors.HexColor("#bed0dd"))
    canvas.line(42, 32, 800, 32)
    canvas.setFont("Arial", 8)
    canvas.setFillColor(colors.HexColor("#40596b"))
    canvas.drawString(42, 20, "SARSEG · Spinnaker y Kubernetes · Práctica P2 · Laboratorio local")
    canvas.drawRightString(800, 20, str(doc.page))


def main():
    results = json.loads((E / "results.json").read_text(encoding="utf-8"))
    assert len(results) == 11 and all(x["passed"] for x in results), "The report requires 11 passing integration checks"
    state = json.loads((E / "git-state.json").read_text())
    execution = json.loads((E / "git-execution.json").read_text())
    up = json.loads((E / "hpa-up.json").read_text())[-1]
    down = json.loads((E / "hpa-down.json").read_text())[-1]
    cpu = up["hpa"]["currentMetrics"][0]["resource"]["current"]["averageUtilization"]
    p("AUTOMATIZACIÓN DE LA<br/>CONFIGURACIÓN CONTINUA", "TitleLab")
    p("Despliegue de SARSEG con Spinnaker y Kubernetes", "H1Lab")
    p("Práctica P2 · 10% · Adaptación de la herramienta Argo CD a Spinnaker")
    p("Autor: Jhoel Suárez<br/>Fecha de la ejecución: 19 de noviembre de 2026 (America/Guayaquil)")
    STORY.append(Spacer(1, 20))
    table([["Entrega", "Contenido"], ["Repositorio público", "github.com/JOURT1/SARSEG-Kubernetes-P2 · carpeta spinnaker"],
           ["Aplicación", "Web SARSEG Ionic/Angular + API ASP.NET Core + PostgreSQL local"],
           ["Resultado", "11 comprobaciones aprobadas; despliegue automático desde Git y HPA 2 → 5 → 2"],
           ["Ejecución", "Docker Desktop Linux, kind, Spinnaker 2026.4.1 y Metrics Server v0.8.1"]], [170, 580])
    p('<br/><link href="https://github.com/JOURT1/SARSEG-Kubernetes-P2/tree/codex/spinnaker-local/spinnaker" color="#146487">Abrir los manifiestos, pipeline, scripts y evidencias en GitHub</link>')

    page("1. Objetivo y alcance de la adaptación")
    p("Automatizar el despliegue de una aplicación web en Kubernetes usando Git como fuente de verdad. Se reemplaza Argo CD por Spinnaker, manteniendo Deployment, Service NodePort, HPA y detección automática de cambios del repositorio.")
    table([["Consigna", "Implementación comprobada"], ["Deployment", "2 réplicas iniciales; etiquetas y selector app=sarseg-web; puerto 8080; CPU y memoria con requests/limits."],
        ["Service", "NodePort 30380; port 80; targetPort http, definido como 8080 en el Pod. Acceso HTTP 200 por localhost:14800."],
        ["HPA", "autoscaling/v2; Deployment sarseg-web; mínimo 2 y máximo 5; CPU 50%; aumento y reducción observados."],
        ["Integración Git", "Sondeo local cada 20 s; pipeline de Spinnaker con tres etapas Deploy (Manifest). URL de artefactos fijada al SHA."],
        ["Entregables", "Repositorio público, rama de trabajo, commits separados, pull request, informe PDF y capturas con archivos originales."]], [170, 580])
    p("<br/>Es un laboratorio de desarrollo, gratuito y local. No se crean recursos de nube ni se publica la aplicación en Internet. La interfaz Spinnaker no requiere registro de una cuenta comercial.")

    page("2. Arquitectura y automatización")
    table([["Origen / componente", "Responsabilidad"], ["GitHub público · spinnaker/k8s/", "Fuente de los tres YAML; cada ejecución usa un SHA completo e inmutable."],
        ["Adaptador Git local", "Compara el contenido cada 20 s. Si cambia, inicia el pipeline mediante Gate. No aplica YAML, no usa kubectl ni kubeconfig."],
        ["Spinnaker", "Gate recibe la solicitud; Orca coordina; Clouddriver descarga los artefactos HTTP y despliega en sarseg-dev. Front50 conserva la configuración."],
        ["Kubernetes", "Deployment/ReplicaSet mantienen los Pods. Service dirige el tráfico. HPA usa CPU de Metrics Server para variar de 2 a 5."],
        ["Persistencia y apoyo", "MySQL conserva ejecuciones de Spinnaker; Redis administra la cola. PostgreSQL y una API única soportan la web SARSEG."]], [210, 540])
    p("<br/><b>Diferencia frente a Argo CD.</b> Spinnaker no ofrece el mismo controlador Automated Sync. Aquí la automatización se implementa con sondeo Git y un pipeline real de Spinnaker. No hay corrección periódica de desvíos manuales ni eliminación automática al borrar un archivo de Git.")
    p("El adaptador sólo confirma la revisión al recibir SUCCEEDED. Una ejecución fallida no se marca como desplegada. La configuración mínima ejecuta cinco servicios Spinnaker, MySQL y Redis; omite servicios de bake, canarios y CI que no se necesitan.")

    page("3. Configuración de los manifiestos")
    table([["Archivo / campo", "Valor y propósito"], ["deployment.yml · replicas / selector", "2; app=sarseg-web tanto en matchLabels como en las etiquetas de los Pods."],
        ["deployment.yml · imagen / puerto", "sarseg-web:9984bc57, construida desde el código SARSEG; containerPort 8080 con nombre http."],
        ["deployment.yml · recursos", "requests: CPU 25m, memoria 32Mi. limits: CPU 250m, memoria 128Mi. Probes HTTP de vida y disponibilidad."],
        ["deployment.yml · capacidad", "strategy.spinnaker.io/use-source-capacity=true conserva la capacidad existente cuando HPA controla las réplicas."],
        ["service.yml", "type=NodePort; nodePort=30380; port=80; targetPort=http; selector app=sarseg-web."],
        ["hpa.yml", "minReplicas=2; maxReplicas=5; CPU averageUtilization=50; scaleTargetRef Deployment/sarseg-web."],
        ["Métricas y reducción", "Metrics Server v0.8.1. Ventana de estabilización de reducción: 60 s. El valor 50% se calcula respecto de CPU requests, no del límite."]], [245, 505])
    p("<br/>Los YAML completos están en el repositorio. La API, PostgreSQL y la plataforma se preparan como infraestructura de apoyo. Los tres recursos evaluados se instalan mediante Spinnaker, sin kubectl apply manual sobre ellos.")

    page("4. Estado inicial: dos réplicas")
    figure("01-inicial.jpg", "Figura 1. Captura del visor resumido de registros originales de kubectl: Deployment 2/2, NodePort, HPA y métricas de los Pods. El JSON del mismo nombre conserva hora, comandos y salidas.", 395)

    page("5. Aplicación SARSEG accesible")
    figure("02-sarseg-web.jpg", "Figura 2. Interfaz real de SARSEG servida desde Kubernetes por el NodePort. Se comprobó HTTP 200, /health/ready y login administrativo HTTP 200, sin publicar contraseñas o respuestas de autenticación.", 365)
    p("Acceso local: <link href=\"http://127.0.0.1:14800\" color=\"#146487\">http://127.0.0.1:14800</link>. Las imágenes se construyeron desde el commit 9984bc57 del proyecto privado original; el repositorio de esta entrega conserva únicamente infraestructura y documentación.", "SmallLab")

    page("6. Pipeline ejecutado por Spinnaker")
    figure("03-spinnaker-pipeline.jpg", "Figura 3. Interfaz original de Deck: las etapas Deploy deployment.yml, Deploy service.yml y Deploy hpa.yml terminan en SUCCEEDED.", 345)
    p("Ejecución comprobada: " + escape(execution["id"]) + ". El JSON completo de Gate se conserva como git-execution.json.", "SmallLab")

    page("7. Prueba de cambio Git automático")
    p("Se publicó un commit que modifica sarseg.edu/revision en la plantilla de Pods. El sondeo detectó el cambio, inició una nueva ejecución de Spinnaker y el Deployment reflejó la nueva revisión sin aplicar los manifiestos manualmente.")
    p("Commit de la prueba: <b>" + state["sha"] + "</b><br/>Rama: " + escape(state["branch"]) + "<br/>Ejecución: " + escape(state["execution"]), "SmallLab")
    figure("04-git-sincronizado.jpg", "Figura 4. Estado registrado tras el despliegue del cambio Git. La prueba verifica que el SHA confirmado y la anotación ejecutada corresponden al commit publicado.", 320)

    page("8. HPA: incremento automático bajo carga")
    figure("05-carga-cinco.jpg", "Figura 5. Job temporal de solicitudes HTTP a la web. Se observan cinco Pods web listos y el incremento originado por CPU, sin ejecutar kubectl scale.", 385)
    p(f"Última muestra de aumento: CPU {cpu}% de requests, objetivo 50%; Deployment Ready=5. Archivo hpa-up.json: serie original de muestras y condiciones del controlador.", "SmallLab")

    page("9. HPA: reducción después de retirar la carga")
    figure("06-reduccion-dos.jpg", "Figura 6. Tras eliminar el Job de carga, el HPA reduce la capacidad a dos Pods listos. Las muestras y eventos originales se conservan en hpa-down.json y events.txt.", 385)
    p("Estado final comprobado: Deployment replicas=2 y readyReplicas=2. La reducción respeta la ventana de estabilización configurada; no es instantánea.", "SmallLab")

    page("10. Resultados, reproducción y referencias")
    table([["Verificación", "Resultado"], ["Deployment, recursos, selectores, NodePort y HPA", "5 comprobaciones aprobadas, incluyendo la disponibilidad web/API"],
        ["SARSEG y Metrics Server", "Login real HTTP 200 y métricas disponibles"], ["Cambio Git y pipeline", "SHA esperado desplegado automáticamente; tres etapas SUCCEEDED"],
        ["HPA", "Aumento 2 → 5 y reducción 5 → 2; ambas comprobaciones aprobadas"], ["Total", "11 de 11 comprobaciones aprobadas"]], [330, 420])
    p("<br/>Reproducción: instalar requirements.txt y ejecutar spinnaker/scripts/Start-Lab.ps1. Para la prueba completa: python spinnaker/scripts/verify_lab.py --publish-change. Se requiere acceso al código privado original para reconstruir las imágenes SARSEG.", "SmallLab")
    p("Incidencias resueltas: se ajustó el enlace de artefactos al modelo de la versión instalada; se añadió espera de PostgreSQL antes de iniciar la API. Los reinicios iniciales de servicios Spinnaker ocurrieron mientras MySQL se preparaba. La entrega usa ejecuciones posteriores correctas.", "SmallLab")
    for label, url in [
        ("Instalador mínimo oficial y licencia", "https://github.com/spinnaker/spinnaker/tree/1b3ed435fe5341b41dcbbdce999cb771145166a8/spinnaker-kustomize"),
        ("Spinnaker: artefactos HTTP", "https://spinnaker.io/docs/reference/artifacts/types/http-file/"),
        ("Spinnaker: proveedor Kubernetes y capacidad", "https://spinnaker.io/docs/reference/providers/kubernetes/"),
        ("Kubernetes: Horizontal Pod Autoscaler", "https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/"),
        ("Metrics Server v0.8.1", "https://github.com/kubernetes-sigs/metrics-server/tree/v0.8.1")]:
        p('<link href="' + url + '" color="#146487">' + label + '</link>', "SmallLab")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT), pagesize=landscape(A4), leftMargin=42, rightMargin=42, topMargin=36, bottomMargin=45,
                            title="SARSEG: configuración continua con Spinnaker", author="Jhoel Suárez")
    doc.build(STORY, onFirstPage=footer, onLaterPages=footer)
    print(OUT)


if __name__ == "__main__":
    main()
