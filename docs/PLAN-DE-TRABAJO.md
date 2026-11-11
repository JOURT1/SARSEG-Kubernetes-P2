# Plan de trabajo y criterios de aceptación

## Objetivo académico

Actividad Configuración de cluster Docker Swarm o Kubernetes, 15 por ciento P2.
La alternativa elegida es Kubernetes. Grafana es la plataforma principal; el primer
Pod del material Intro Kubernetes usa Nginx, por lo que se emplea otra plataforma.

## Avances y ramas

| Avance | Rama | Entrega |
|---|---|---|
| 1 | main | Alcance inicial y criterios de aceptación |
| 2 | codex/infraestructura-kubernetes | Clúster, namespace, Grafana y exposición |
| 3 | codex/metricas-sarseg | Prometheus, kube-state-metrics y tablero |
| 4 | codex/pruebas-deployment-replicaset | Scripts, ejecución y registros de pruebas |
| 5 | codex/informe-evidencias | Informe, figuras, conclusiones y guía de entrega |

Cada rama tendrá commits por unidad de trabajo y una integración explícita en main.
Se conservarán las ramas remotas para revisar los avances. No se alterarán fechas
de commits ni se simularán colaboradores o revisiones.

## Criterios verificables

1. Nodos Ready y dos Pods de Grafana Ready.
2. Relación Deployment -> ReplicaSet -> Pod comprobada por ownerReferences.
3. Service NodePort accesible desde Windows y API de salud de Grafana con HTTP 200.
4. Escalado de dos a tres réplicas y restauración a dos.
5. Eliminación de un Pod de prueba y creación automática de otro con UID diferente.
6. Cambio de la plantilla del Deployment, nuevo ReplicaSet y rollback.
7. Métricas reales disponibles en Prometheus y tablero provisionado de Grafana.
8. Repositorio público, historial por avances e informe con evidencia y limitaciones.

## Límites del laboratorio

El laboratorio observa su propia infraestructura de monitoreo. No declara que la API
privada de SARSEG esté desplegada o instrumentada. Los usos futuros para latencia,
errores HTTP y reportes de asistencia se distinguen de lo ejecutado.

Se usa acceso anónimo de solo lectura limitado a loopback. La configuración de
Grafana se reconstruye desde Git y ConfigMaps. Las bases SQLite y series de
Prometheus son efímeras. Esto no constituye alta disponibilidad de producción.
