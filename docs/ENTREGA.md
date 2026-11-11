# Guía de entrega de la actividad P2

## Archivo para subir al aula

[Informe SARSEG Kubernetes P2 en PDF](../output/pdf/Informe-SARSEG-Kubernetes-P2.pdf).
El informe tiene nueve páginas, enlace público, arquitectura, configuración,
tres capturas reales, pruebas, usos, límites, fuentes y trazabilidad de ramas.

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
| Capturas | Tres PNG reales de la interfaz de Grafana incluidos en el informe |
| Indicar usos | docs/METRICAS.md y conclusión del informe |
| Repositorio público | JOURT1/SARSEG-Kubernetes-P2 |
| Ramas y commits separados | Cuatro ramas de avance y main, PR 1 a 4 |
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
verificados. Requiere Python con reportlab y las fuentes Arial y Consolas de
Windows. En esta entrega el PDF se renderizó con Poppler y se inspeccionaron sus
nueve páginas antes de publicarlo.

El archivo fuente privado de SARSEG no se copia ni se necesita para ejecutar
las imágenes oficiales del monitoreo. Tampoco se incluyen los PDFs de clase,
credenciales locales ni kubeconfig.
