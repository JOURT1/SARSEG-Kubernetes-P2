# SARSEG en Kubernetes

Práctica P2 de configuración de clúster, Deployment y ReplicaSet. Se despliega
Grafana para observar infraestructura de laboratorio relacionada con SARSEG,
un sistema de registro de asistencia con API .NET, PostgreSQL e interfaz Ionic/Angular.

El código de la aplicación original no es necesario para desplegar esta plataforma.
Este repositorio contiene únicamente infraestructura y documentación de la práctica.

## Alcance

- Clúster local kind sobre Docker Desktop.
- Grafana con dos réplicas, controladas por Deployment y ReplicaSet.
- Prometheus y kube-state-metrics para obtener métricas reales de Kubernetes.
- Exposición local por Service NodePort.
- Pruebas de escalado, recuperación de un Pod, actualización gradual y rollback.
- Informe y evidencias verificables.

Consulta [el plan de trabajo](docs/PLAN-DE-TRABAJO.md). Los resultados se incorporan
por avance en ramas separadas y commits con un propósito concreto.
