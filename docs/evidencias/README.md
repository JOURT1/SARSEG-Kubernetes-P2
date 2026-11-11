# Índice de evidencias reales

## Ampliación del informe APA 7

La [reproducción desde cero](recorrido-apa7/README.md) conserva las dieciocho
fases del nuevo recorrido y sus 109/109 muestras correctas. Las capturas de
GitHub, bitácora y navegador se encuentran en apa7. El informe ampliado incluye
veintiséis figuras numeradas y sus explicaciones, además del logotipo oficial
de la UDLA en la carátula.

Las capturas del visor se identifican como registros conservados de comandos
reales. Se distinguen de las capturas directas de GitHub y Grafana y de las
exportaciones de Grafana Image Renderer. Los archivos y las fechas originales
se mantienen para contrastar cada fase.

## Ejecución final aprobada

La ejecución principal está en [ejecucion-final](ejecucion-final). Pasaron once
comprobaciones y las 113 muestras HTTP respondieron con 200 y database=ok.

| Archivo | Evidencia |
|---|---|
| resultados.json | Resumen, horas UTC, UIDs y resultados de cada comprobación |
| nodos.json | Tres nodos Ready y versiones del clúster |
| 01-inicial.json y .txt | Deployment, ReplicaSets, Pods, Service y endpoints iniciales |
| 02-escalado-tres.json y .txt | Tres réplicas listas, mismo ReplicaSet |
| 03-recuperacion.json y .txt | Reposición automática del Pod eliminado |
| 04-inicio-rollout.json y .txt | Estado durante el cambio de plantilla |
| 05-rollout-completo.json y .txt | ReplicaSet nuevo con dos réplicas disponibles |
| 06-rollback.json y .txt | Reactivación del ReplicaSet de la plantilla anterior |
| grafana-health.json | URL local, estado HTTP y respuesta real de salud |
| prometheus-up.json | Tres fuentes de métricas con valor 1 |
| dashboard-api.json | Tablero recuperado desde la API real de Grafana |
| comandos.json y .txt | Comandos completos, salidas, códigos de retorno y horas |
| eventos.txt | Eventos de Kubernetes, incluidos arranque y control de réplicas |
| http-muestreo.json | Cada solicitud de salud durante las pruebas |
| historial-rollout.txt | Revisiones mantenidas por Kubernetes |

## Capturas

- [Estado inicial](capturas/01-grafana-base.png).
- [Tres réplicas](ejecucion-final/capturas/02-grafana-tres-replicas.png).
- [Después del rollback](ejecucion-final/capturas/03-grafana-final.png).

Las imágenes PNG son exportaciones reales de la interfaz de Grafana mediante
el servicio oficial Grafana Image Renderer v5.12.10. El renderer es un contenedor
auxiliar de Docker y no altera las métricas del namespace de Kubernetes. Las
salidas de terminal se conservan como TXT y JSON; no se convierten en falsas
capturas de pantalla.

## Primera ejecución conservada

[ejecucion](ejecucion) conserva el primer protocolo: los controladores cumplieron
su función, pero una de 111 solicitudes terminó con RemoteDisconnected durante
el rollout. Se marcó success=false. La corrección de drenaje y la repetición se
explican en [incidencias](../INCIDENCIAS.md).

## Validación independiente

[GitHub Actions](https://github.com/JOURT1/SARSEG-Kubernetes-P2/actions/runs/42963098362)
creó otro clúster en Linux y completó el protocolo sin renderer. El resumen de
esa ejecución se conserva en [github-actions.json](github-actions.json). No se
confunden sus resultados con los del equipo Windows.

Las fechas de los registros son UTC. America/Guayaquil corresponde a UTC menos
cinco horas. Los hashes SHA256 se encuentran en SHA256SUMS.txt y permiten
comprobar que los archivos descargados coinciden con los entregados.
Los archivos de texto se normalizan a UTF8 con saltos LF antes de calcularlos.
