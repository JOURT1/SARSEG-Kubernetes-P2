# Arquitectura del laboratorio

## Organización del clúster

kind crea un control plane y dos workers como contenedores Linux sobre Docker
Desktop. Los dos Pods de Grafana se distribuyen entre los workers mediante
topologySpreadConstraints. Todos los recursos propios usan el namespace
sarseg-observabilidad.

## Jerarquía de control

El Deployment grafana declara dos réplicas y administra los ReplicaSets. Cada
ReplicaSet conserva la cantidad deseada de Pods de una plantilla concreta. La
propiedad se comprueba en metadata.ownerReferences, no solo en los nombres.

Al cambiar spec.template, el Deployment genera otro ReplicaSet. RollingUpdate
permite un Pod adicional y exige cero réplicas no disponibles. La readinessProbe
evita enviar tráfico a Pods que todavía no están listos. Un escalado cambia el
número de réplicas y no crea por sí mismo una nueva revisión de la plantilla.

El hook preStop espera diez segundos antes de terminar Grafana, con un periodo
de gracia total de treinta segundos. Esto da tiempo para que la retirada del
endpoint del Pod se propague antes de que el proceso deje de atender solicitudes.
maxUnavailable=0 por sí solo no garantiza que todas las conexiones HTTP terminen
correctamente durante una actualización.

No se crea un ReplicaSet independiente con el mismo selector: competiría con el
control del Deployment. El ReplicaSet administrado se observa y prueba directamente.

## Exposición

Windows 127.0.0.1:13000 -> mapeo de kind -> NodePort 30300 -> Service grafana:3000
-> puerto 3000 de cualquiera de los Pods Ready. El Service conserva un punto de
acceso estable aunque cambien los Pods y sus direcciones.

## Datos y límites

Los tableros y fuentes de datos se provisionan desde archivos versionados. Cada
réplica tiene una SQLite efímera independiente y solo se usa como visor anónimo.
No se habilitan ediciones de dashboards ni alertas con estado. Una instalación
productiva de Grafana con alta disponibilidad requiere una base PostgreSQL o
MySQL compartida y autenticación; este laboratorio no demuestra esa arquitectura.
