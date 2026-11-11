# Guía de entrega de la actividad P2

## Archivo para subir al aula

[Informe SARSEG Kubernetes P2 en PDF](../output/pdf/Informe-SARSEG-Kubernetes-P2.pdf).
El informe ampliado tiene treinta y seis páginas y veintiséis capturas con sus
explicaciones. Incluye carátula con logo oficial UDLA, Jhoel Suárez, Ingeniería
de Software, Procesos de Software y Mónica Fernanda Sanchez Rosero.

Se usa APA séptima edición: papel carta, márgenes de 2,54 cm, Times New Roman
de 12 puntos, interlineado doble, sangría inicial de 1,27 cm, número de página
superior derecho, figuras numeradas con título en cursiva, citas autor-fecha
y referencias con sangría francesa. El logotipo es la adaptación de carátula
solicitada por el autor.

Enlace del repositorio público:
https://github.com/JOURT1/SARSEG-Kubernetes-P2

## Correspondencia con los entregables

| Requisito de la actividad | Dónde se acredita |
|---|---|
| Plataforma diferente al primer Pod de clase | Grafana 12.3.0; clase usa Nginx |
| Configuración del clúster | cluster/kind.yaml y evidencias/ejecucion-final/nodos.json |
| Aplicar Deployment | k8s/grafana.yaml; replicas, probes y RollingUpdate |
| Aplicar ReplicaSet | ownerReferences, escalado, reposición y estados JSON |
| Exponer plataforma | NodePort 30300 a loopback 13000; grafana-health.json |
| Capturas | Veintiséis imágenes de GitHub, bitácora de comandos y Grafana, de principio a fin |
| Indicar usos | docs/METRICAS.md y conclusión del informe |
| Repositorio público | JOURT1/SARSEG-Kubernetes-P2 |
| Ramas y commits separados | Ramas de avance conservadas, commits e integraciones por pull request |
| Evidencia verificable | Comandos, estados, HTTP, UIDs, CI y SHA256SUMS |

## Recorrido breve para explicar la práctica

1. Mostrar el repositorio, el README y los pull requests por avance.
2. Abrir http://127.0.0.1:13000 y explicar las métricas del laboratorio.
3. Ejecutar kubectl con contexto kind-sarseg-p2 y namespace sarseg-observabilidad.
4. Mostrar Deployment, ReplicaSets, Pods y Service.
5. Explicar que escalar mantiene el ReplicaSet y cambiar la plantilla crea otro.
6. Mostrar UIDs del Pod eliminado y su reemplazo y el resultado del rollback.
7. Distinguir lo probado de una futura instrumentación de la API SARSEG.

Para una demostración nueva, usa python scripts/test_lab.py --output tmp/demo.
Para repetir capturas, primero ejecuta scripts/Export-Dashboard.ps1 y agrega
--render al comando de prueba. La evidencia original no se sobrescribe.

## Generación del informe

scripts/build_report.py construye el PDF y docs/INFORME.md desde los resultados
verificados. Su implementación ampliada está en scripts/build_report_apa7.py.
Requiere Python con reportlab y Pillow, y las fuentes Times New Roman de Windows.
En esta entrega el PDF se renderizó con Poppler para su revisión visual.

## Recorrido reproducido desde cero

scripts/walkthrough.py crea únicamente el clúster sarseg-p2-evidencia, con el
mismo despliegue y un puerto distinto, 13010. Conserva dieciocho fases en
evidencias/recorrido-apa7/pasos.json y una bitácora HTML consultable con un servidor
local. Las capturas del visor se identifican como registros; las de GitHub y
Grafana se identifican como capturas directas o exportaciones de la plataforma.

La reproducción obtiene once comprobaciones y 109/109 muestras correctas.
La ejecución original final de 113/113 y la inicial con un fallo se conservan
por separado. La documentación no atribuye los distintos UIDs al mismo Pod.

El archivo fuente privado de SARSEG no se copia ni se necesita para ejecutar
las imágenes oficiales del monitoreo. Tampoco se incluyen los PDFs de clase,
credenciales locales ni kubeconfig.
