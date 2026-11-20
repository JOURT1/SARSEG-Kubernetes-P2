# SARSEG: configuración continua con Spinnaker

Práctica P2 (10%). Adaptación de la consigna de Argo CD a **Spinnaker local**,
según la herramienta solicitada. Docker Desktop ejecuta un clúster kind
independiente y todos los accesos se publican únicamente en `127.0.0.1`.

## Entrega

- [Informe PDF en formato APA 7 con 26 figuras](output/pdf/Informe-SARSEG-Spinnaker-P2.pdf).
- [Informe y correspondencia con la consigna](docs/INFORME.md).
- [Deployment](k8s/deployment.yml), [Service](k8s/service.yml) y [HPA](k8s/hpa.yml).
- [Pipeline exportado de Spinnaker](pipeline.json).
- [Resultados y evidencias originales](docs/evidencias/).
- Repositorio público: <https://github.com/JOURT1/SARSEG-Kubernetes-P2>.

El informe ampliado incluye carátula con el logotipo oficial de la UDLA y autor
Joel Suárez, procedimiento en 26 pasos ilustrados, 15 referencias y los tres
YAML completos como apéndice. Las capturas distinguen interfaces nativas,
archivos versionados y registros originales de las pruebas. El recorrido está
en [evidencias APA 7](docs/evidencias/recorrido-apa7/).

## Qué se implementa

La aplicación es la web real Ionic/Angular de SARSEG, acompañada por su API
ASP.NET Core y una base PostgreSQL de prueba independiente. Las imágenes
`sarseg-web:9984bc57` y `sarseg-api:9984bc57` se construyen desde el commit
`9984bc57f1e7252793f146a40542a60940b16463` del repositorio privado original.
El código privado y las credenciales permanecen fuera de este repositorio público.

| Requisito | Implementación |
|---|---|
| Deployment inicial | 2 réplicas, selector `app: sarseg-web`, puerto 8080 |
| Recursos por Pod web | requests: CPU 25m / memoria 32Mi; limits: CPU 250m / memoria 128Mi |
| Service | NodePort 30380; puerto 80; targetPort `http` (8080) |
| HPA | autoscaling/v2; mínimo 2, máximo 5, CPU objetivo 50% |
| Métricas | Metrics Server v0.8.1, API metrics.k8s.io comprobada |
| Despliegue automatizado | Sondeo Git cada 20 s -> Gate -> Orca -> Clouddriver |
| Fuente de verdad | Los tres YAML de `spinnaker/k8s/` en GitHub |
| Trazabilidad | URL de cada artefacto fijada a un SHA Git completo |

Spinnaker ejecuta **tres etapas Deploy (Manifest)** y descarga directamente los
YAML desde `raw.githubusercontent.com`. El adaptador de sondeo no usa kubectl,
no tiene kubeconfig y no aplica recursos. Sólo inicia el pipeline por Gate.
Compara el contenido de los tres archivos y confirma el SHA únicamente cuando
la ejecución termina en `SUCCEEDED`; si falla, reintenta.

Spinnaker no tiene el interruptor Automated Sync de Argo CD. Esta implementación
equivale a **desplegar automáticamente los cambios de Git** mediante un adaptador
local, sin webhooks públicos. No incorpora la corrección periódica de cambios
manuales ni el borrado automático de recursos eliminados en Git. El HPA controla
las réplicas después del primer despliegue: `use-source-capacity: 'true'` impide
que otro despliegue restablezca dos durante una prueba de carga.

## Ejecutar

Requisitos: Docker Desktop en modo Linux con memoria disponible (la guía
oficial recomienda 16 GB), PowerShell 7, Git, Python 3 y kubectl. Para construir
SARSEG se requiere permiso de lectura del repositorio privado original.
No se requiere una cuenta comercial de Spinnaker ni una cuenta cloud.

```powershell
python -m pip install -r spinnaker/requirements.txt
.\spinnaker\scripts\Start-Lab.ps1
```

El script verifica la descarga de kind v0.27.0, construye las imágenes, crea
Secret locales, instala la plataforma y Metrics Server, configura el pipeline
y deja el sondeo en segundo plano. Para reutilizar imágenes ya construidas:

```powershell
.\spinnaker\scripts\Start-Lab.ps1 -SkipBuild
```

| Acceso | Dirección |
|---|---|
| SARSEG | <http://127.0.0.1:14800> |
| Interfaz original de Spinnaker | <http://127.0.0.1:14900/#/applications/sarseg/executions> |
| Gate API | <http://127.0.0.1:14884> |

Los secretos de desarrollo quedan en `.local/spinnaker/credentials.json`,
ignorado por Git. Allí se conserva la contraseña aleatoria del usuario `admin`
de SARSEG. Spinnaker usa acceso sin autenticación sólo dentro del laboratorio
local limitado a loopback; no existe una cuenta externa que registrar.

## Cambios y pruebas

El sondeo sigue `main` por defecto, o la rama indicada por `-Branch`.
La rama de implementación y demostración es `codex/spinnaker-local`.
Para repetir una demostración con commits en una rama de trabajo, inicia
el sondeo con `-Branch codex/spinnaker-local` antes de ejecutar las pruebas.

```powershell
# Publica un cambio real y comprueba el despliegue; después genera carga HTTP.
python spinnaker/scripts/verify_lab.py --publish-change
```

Este comando crea un commit separado en la rama actual, lo publica y verifica
que el sondeo despliegue su revisión. Usa un Job HTTP temporal para comprobar
2 -> 5 -> 2 réplicas por CPU. No ejecuta `kubectl scale`. Conserva JSON, salidas
de kubectl y capturas. La toma realizada por el agente usa su navegador para
las capturas y conserva los mismos registros originales.

Para detener conservando los datos:

```powershell
.\spinnaker\scripts\Stop-Lab.ps1
```

Para volver a encender el clúster conservado, ejecuta
`docker start sarseg-spinnaker-control-plane` antes del script de inicio.
No se modifican ni eliminan los clústeres de las prácticas anteriores.

## Plataforma mínima de esta práctica

Spinnaker 2026.4.1: Deck, Gate, Orca, Clouddriver y Front50. MySQL conserva
configuración y ejecuciones; Redis mantiene la cola. No se ejecutan Echo,
Fiat, Igor, Rosco, Kayenta o Keel. No se hacen bakes, canarios, integraciones CI
ni autenticación externa. La base de despliegue oficial y su licencia se
documentan en [procedencia](platform/SOURCE.md).

Sólo los tres recursos de la consigna se despliegan mediante el pipeline.
El clúster, la plataforma, Metrics Server y la base/API de apoyo se preparan
como infraestructura de laboratorio por el script de inicio. Los permisos de
escritura de Clouddriver se limitan a `sarseg-dev`.

## Referencias

- [Instalación mínima oficial](https://github.com/spinnaker/spinnaker/tree/1b3ed435fe5341b41dcbbdce999cb771145166a8/spinnaker-kustomize).
- [Artefactos HTTP](https://spinnaker.io/docs/reference/artifacts/types/http-file/).
- [Proveedor Kubernetes y use-source-capacity](https://spinnaker.io/docs/reference/providers/kubernetes/).
- [HPA de Kubernetes](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/).
- [Metrics Server](https://github.com/kubernetes-sigs/metrics-server/tree/v0.8.1).
