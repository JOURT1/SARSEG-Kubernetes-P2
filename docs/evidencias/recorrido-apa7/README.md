# Reproducción completa para el informe APA 7

Se creó desde cero un clúster independiente llamado sarseg-p2-evidencia. La
implementación original sarseg-p2 permanece separada. Los manifiestos de las
plataformas son los mismos; el nombre y el puerto publicado cambian para
evitar interferencias: contexto kind-sarseg-p2-evidencia y puerto 13010.

## Evidencia de principio a fin

- pasos.json: dieciocho fases, con comandos ejecutados, códigos de salida,
  salidas originales, archivos de configuración y estados observados.
- index.html: visor de lectura para consultar esas fases.
- pruebas: protocolo completo, estados JSON, UIDs, eventos, muestras HTTP y
  capturas de Grafana durante el arranque, escalado y cierre.
- ../apa7: veinticuatro capturas adicionales del navegador, de GitHub y del visor.
- ../../INDICE-FIGURAS.json: índice de las veintiséis figuras del informe.

Para consultar la bitácora desde la raíz del repositorio:

```powershell
python -m http.server 18090 --bind 127.0.0.1 --directory docs/evidencias/recorrido-apa7
```

Abre http://127.0.0.1:18090/?paso=01. El visor muestra registros conservados;
no se presenta como una terminal real ni como el estado actual del clúster.
Los originales permiten contrastar lo mostrado en cada captura.

## Resultado

Once comprobaciones aprobadas y 109 de 109 muestras HTTP correctas. Se creó
el clúster, se esperaron tres nodos Ready, se desplegó Grafana y se verificaron
dos réplicas, exposición, escalado 2 a 3 a 2, reposición de Pod, nuevo ReplicaSet
y rollback. La versión de la imagen se mantuvo en Grafana 12.3.0.

Las horas se conservan en UTC. Las mediciones y los UIDs pertenecen a esta
reproducción y no se mezclan con los de la ejecución original de 113/113.

## Repetición y limpieza opcional

scripts/walkthrough.py conserva la evidencia y no sobrescribe un recorrido
existente. Requiere Docker Linux, kubectl, Python y kind en .tools/kind.exe.
Para una nueva prueba sobre este clúster, utiliza test_lab.py con un directorio
de salida distinto, --context kind-sarseg-p2-evidencia y --base-url
http://127.0.0.1:13010. Las capturas opcionales requieren el renderer local.

El clúster de la reproducción puede eliminarse cuando ya no sea necesario con
kind delete cluster --name sarseg-p2-evidencia. Eso descarta sus datos efímeros,
pero no los registros ni las capturas ya guardados en el repositorio.
