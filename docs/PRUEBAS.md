# Protocolo de validación

La prueba modifica únicamente el Deployment grafana y elimina un Pod del clúster
local de esta práctica. No opera sobre otro contexto ni namespace.

```powershell
python scripts/test_lab.py --render
```

El parámetro opcional --render exporta imágenes reales del tablero mediante
Grafana Image Renderer. Sin ese parámetro se ejecutan todas las pruebas de
Kubernetes y HTTP sin necesitar el servicio de exportación.

El script conserva los comandos, códigos de salida, estados JSON, UIDs de Pods,
referencias de propietario, eventos y un muestreo de salud aproximadamente cada
segundo. Comprueba la recuperación del número de réplicas disponibles y que los
Pods estén Ready; no usa solamente phase=Running como criterio.

El rollout modifica una anotación de spec.template. No cambia la versión de
Grafana. Esto permite observar el mecanismo de revisión, nuevo ReplicaSet y
rollback sin atribuirle una actualización de software que no ocurrió.

Las evidencias existentes no se sobrescriben: para repetir, usa --output con
otro directorio. En GitHub Actions se crea un clúster efímero y los registros se
guardan como artefacto. Los resultados de la ejecución local y de CI se reportan
por separado.

El muestreo de HTTP solo permite afirmar que esas solicitudes respondieron;
no demuestra que no existieran interrupciones entre muestras.
