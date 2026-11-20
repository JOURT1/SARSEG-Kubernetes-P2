# Capturas reales del laboratorio SARSEG

Autor del informe: **Jhoel Suarez**. Fecha: 20 de noviembre de 2026.

Las 23 figuras del PDF son capturas directas de las interfaces de GitHub,
Spinnaker Deck, SARSEG y Headlamp conectado al clúster real sarseg-spinnaker.
Las imágenes originales se conservan completas. No contienen composiciones,
estados simulados, listados de código ni visores documentales hechos para el informe.

El orden del informe está definido en `pasos.json`, con título, descripción,
URL de origen, fecha UTC de captura y SHA-256. Los números de archivo reflejan
el orden de captura; el índice define el orden pedagógico del informe.

## Nueva prueba de carga

Se aplicó el Job HTTP temporal ya utilizado en el laboratorio. Se observó el
HPA en 2 réplicas, después en 5 con CPU 640% frente a objetivo 50%, y de nuevo
en 2 al retirar el Job. La capacidad no se cambió manualmente. El Deployment
confirmó 5 réplicas listas y disponibles durante la carga. Las pantallas
`19`, `23`, `24` y `25` documentan esta secuencia. Las muestras JSON de esta
sesión se conservan aquí como respaldo; no se presentan como capturas.

## Visor Kubernetes

Headlamp v0.46.0 procede de su distribución oficial. Se desplegó en kube-system
con una cuenta de servicio limitada a lectura y acceso a métricas. El acceso
se realiza mediante port-forward en 127.0.0.1:14666 y un token temporal de dos
horas guardado únicamente en .local, fuera de Git. No se utiliza ingreso público.
Spinnaker continúa siendo el responsable de los despliegues de SARSEG.

Fuente oficial: https://headlamp.dev/docs/latest/installation/in-cluster/

Las capturas adicionales de dos Pods y balanceadores en Deck se conservan
como evidencia complementaria aunque no se incluyan entre las 23 figuras.
