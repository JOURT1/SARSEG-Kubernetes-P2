# SARSEG en Kubernetes

Práctica P2 de configuración de clúster, Deployment y ReplicaSet. Se despliega
Grafana para observar infraestructura de laboratorio relacionada con SARSEG,
un sistema de registro de asistencia con API .NET, PostgreSQL e interfaz Ionic/Angular.

El código de la aplicación original no es necesario para desplegar esta plataforma.
Este repositorio contiene únicamente infraestructura y documentación de la práctica.

## Entrega

- [Informe PDF con capturas y enlace público](output/pdf/Informe-SARSEG-Kubernetes-P2.pdf).
- [Informe en Markdown](docs/INFORME.md).
- [Guía de entrega y correspondencia con la consigna](docs/ENTREGA.md).
- [Evidencias originales y hashes](docs/evidencias/README.md).

## Inicio rápido

Con Docker Desktop Linux iniciado, PowerShell 7 y kubectl 1.32:

```powershell
.\scripts\Start-Lab.ps1
```

Abre [Grafana local](http://127.0.0.1:13000). El puerto está limitado a loopback.
Se muestra el tablero SARSEG con métricas reales de infraestructura. La API
privada de asistencia no está desplegada en este laboratorio.

Para repetir las pruebas sin sobrescribir la entrega:

```powershell
python scripts/test_lab.py --output tmp/repeticion
```

Consulta [reproducción y exportación de capturas](docs/REPRODUCCION.md).

## Alcance

- Clúster local kind sobre Docker Desktop.
- Grafana con dos réplicas, controladas por Deployment y ReplicaSet.
- Prometheus y kube-state-metrics para obtener métricas reales de Kubernetes.
- Exposición local por Service NodePort.
- Pruebas de escalado, recuperación de un Pod, actualización gradual y rollback.
- Informe y evidencias verificables.

## Resultados comprobados

La ejecución final aprobó once comprobaciones y 113 de 113 muestras de salud
HTTP. Se verificaron escalado 2 a 3 a 2, sustitución de un Pod con UID diferente,
nuevo ReplicaSet por cambio de plantilla y rollback. La actualización conserva
la versión de Grafana y cambia una anotación de spec.template.

La primera ejecución observó una conexión interrumpida durante el rollout;
se conserva su evidencia y la corrección de drenaje en [incidencias](docs/INCIDENCIAS.md).

[GitHub Actions también completó el protocolo en un clúster independiente](https://github.com/JOURT1/SARSEG-Kubernetes-P2/actions/runs/42963098362).
El muestreo de solicitudes no equivale a una garantía de disponibilidad absoluta.

## Organización del trabajo

| Rama conservada | Avance |
|---|---|
| main | Integración de entregables |
| codex/infraestructura-kubernetes | Clúster, despliegue y exposición, PR 1 |
| codex/metricas-sarseg | Fuentes reales y tablero, PR 2 |
| codex/pruebas-deployment-replicaset | Pruebas, correcciones y evidencia, PR 3 |
| codex/informe-evidencias | Informe, referencias y guía de entrega, PR 4 |

Los [pull requests](https://github.com/JOURT1/SARSEG-Kubernetes-P2/pulls?q=is%3Apr)
conservan los commits por avance y se integran mediante merge commits.
Consulta también [plan](docs/PLAN-DE-TRABAJO.md), [arquitectura](docs/ARQUITECTURA.md),
[métricas y usos](docs/METRICAS.md) y [protocolo de pruebas](docs/PRUEBAS.md).

## Límites

Los dashboards son de solo lectura y se reconstruyen desde ConfigMaps.
Grafana usa SQLite efímera independiente por Pod y Prometheus tiene almacenamiento
efímero. El clúster depende de una computadora; las réplicas no representan alta
disponibilidad productiva ni replicación de la base de datos.
