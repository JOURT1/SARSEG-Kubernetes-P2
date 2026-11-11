# Métricas y usos en SARSEG

## Flujo implementado

La API de Kubernetes entrega el estado del namespace a kube-state-metrics.
Prometheus recoge esas métricas cada cinco segundos y Grafana las consulta
mediante una fuente de datos provisionada. No se generan datos sintéticos.

kube-state-metrics solo recibe permisos list y watch sobre Pods, Deployments y
ReplicaSets del namespace sarseg-observabilidad. No usa ClusterRole ni puede
leer Secrets. Prometheus y Grafana no reciben token de ServiceAccount.

## Qué muestra el tablero

- Réplicas deseadas, disponibles y actualizadas del Deployment grafana.
- Pods de infraestructura Running y reinicios de sus contenedores.
- Historial de réplicas durante escalado, actualización y recuperación.
- Estado de las tres fuentes de métricas recogidas por Prometheus.

## Aplicación al sistema de asistencia

Esta práctica establece una plataforma reutilizable para observar SARSEG. En una
integración posterior, la API .NET podría exportar contadores HTTP, histogramas de
latencia, profundidad de trabajos de reportes y errores de acceso a PostgreSQL.
Grafana permitiría correlacionar esos indicadores con picos de registro de
asistencia y generación de reportes PDF o XLSX.

La API de SARSEG no está instrumentada ni desplegada en este laboratorio. No se
muestran asistencia de estudiantes, datos personales, latencias de negocio ni
consultas a la base de producción. Los paneles implementados miden únicamente
recursos reales del namespace de monitoreo.

## Persistencia y disponibilidad

Dos réplicas protegen frente a la pérdida de un Pod y permiten una actualización
gradual. El clúster sigue dependiendo de una computadora, Docker y un control
plane. Prometheus tiene una réplica y almacenamiento efímero. Grafana usa SQLite
independiente por Pod y dashboards de solo lectura reconstruidos desde ConfigMap.
No se afirma tolerancia a fallos de la computadora ni alta disponibilidad de datos.
