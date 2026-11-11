# Reproducción en Windows

## Requisitos

Docker Desktop iniciado con motor Linux, kubectl 1.32 y PowerShell. kind 0.27.0
se descarga desde el repositorio oficial y se valida con su SHA256. El clúster
usa Kubernetes 1.32.2 para coincidir con el cliente disponible en la computadora.
Son versiones fijadas para reproducir esta práctica, no una recomendación de
versiones para producción.

Desde la raíz del repositorio:

```powershell
.\scripts\Start-Lab.ps1
```

Abre http://127.0.0.1:13000. El puerto se publica solo en loopback. No se necesita
port-forward ni dirección IP de Minikube. El NodePort del manifiesto es 30300 y
el puerto publicado por kind en Windows es 13000; no son el mismo puerto.

## Inspección

```powershell
kubectl --context kind-sarseg-p2 get nodes -o wide
kubectl --context kind-sarseg-p2 -n sarseg-observabilidad get deploy,rs,pod,svc -o wide
kubectl --context kind-sarseg-p2 -n sarseg-observabilidad describe deployment grafana
Invoke-RestMethod http://127.0.0.1:13000/api/health
```

Todos los comandos identifican el contexto y el namespace para evitar operar
sobre otro clúster. El script no modifica proyectos de aplicación existentes.

## Recreación y limpieza opcional

Los recursos consumen CPU y memoria mientras Docker está iniciado. Para eliminar
exclusivamente este laboratorio cuando ya no se necesite:

```powershell
.\.tools\kind.exe delete cluster --name sarseg-p2
```

Ese comando descarta los datos efímeros del laboratorio. Los manifiestos,
dashboards y evidencias permanecen en el repositorio. Start-Lab.ps1 permite recrearlo.
