# Evidencias originales de la ejecución

La ampliación del informe con 26 pasos ilustrados está en
[recorrido APA 7](recorrido-apa7/README.md). Conserva las pruebas originales y
añade lecturas documentales del 20 de noviembre de 2026, sin reinstalar el
clúster ni repetir o simular el escalamiento.

Fecha local: **19 de noviembre de 2026, America/Guayaquil**. Los registros
internos usan UTC, por eso sus marcas comienzan por 2026-11-20.

| Captura | Evidencia |
|---|---|
| 01-inicial.jpg | Deployment 2/2, HPA mínimo 2/máximo 5/CPU 50%, NodePort |
| 02-sarseg-web.jpg | Página real SARSEG servida desde Kubernetes |
| 03-spinnaker-pipeline.jpg | Interfaz nativa Deck: pipeline correcto y SHA de prueba |
| 04-git-sincronizado.jpg | Estado Kubernetes después del despliegue automático |
| 05-carga-cinco.jpg | Cinco Pods Ready, HPA actual/deseado 5 y CPU sobre objetivo |
| 06-reduccion-dos.jpg | Retorno automático: Deployment y HPA nuevamente en 2 |
| 07-github-publico.jpg | Repositorio y rama accesibles sin iniciar sesión |

Las capturas 01, 04, 05 y 06 muestran un **visor resumido de registros reales**,
identificado como tal en la propia imagen. `build_evidence_views.py` genera
los archivos `.compact.html` a partir de los `.json` originales, sin consultar
ni simular nuevos estados. Los `.html` sin `compact` muestran las salidas
completas. Todas las capturas fueron tomadas con el navegador.

`results.json` contiene las once verificaciones aprobadas. `git-state.json`
conserva el SHA, la rama y la ejecución confirmados; `git-execution.json` es
la respuesta completa de Gate y contiene los manifiestos resueltos. La
ejecución inicial está en `initial-execution.json`.

`metrics.json` contiene métricas reales; `hpa-up.json` y `hpa-down.json`
conservan las muestras del escalamiento. La última muestra de reducción
confirma también el estado del HPA después de actualizarse su contador.
`load-job.yml` es la carga HTTP utilizada; el Job se eliminó al terminar.

Las contraseñas y respuestas de autenticación se excluyen de la evidencia.
`SHA256SUMS.txt` permite verificar la integridad de los archivos de esta carpeta.
