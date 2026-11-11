param([switch]$OpenBrowser)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $repoRoot
$kindPath = Join-Path $repoRoot '.tools\kind.exe'
if (-not (Test-Path $kindPath)) {
    New-Item -ItemType Directory -Path (Split-Path $kindPath) -Force | Out-Null
    $release = 'https://github.com/kubernetes-sigs/kind/releases/download/v0.27.0'
    Invoke-WebRequest "$release/kind-windows-amd64" -OutFile $kindPath
    $checksum = (Invoke-WebRequest "$release/kind-windows-amd64.sha256sum").Content
    if ($checksum -is [byte[]]) { $checksum = [Text.Encoding]::UTF8.GetString($checksum) }
    $expectedHash = ($checksum.Trim() -split '\s+')[0]
    if ((Get-FileHash $kindPath -Algorithm SHA256).Hash.ToLower() -ne $expectedHash) {
        throw 'La descarga de kind no coincide con el SHA256 oficial.'
    }
}
docker info --format '{{.ServerVersion}}'
if ($LASTEXITCODE -ne 0) { throw 'Inicia Docker Desktop con contenedores Linux.' }
$clusters = & $kindPath get clusters
if ($clusters -notcontains 'sarseg-p2') {
    & $kindPath create cluster --config cluster/kind.yaml --wait 180s
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el cluster.' }
}
function Invoke-Kubectl {
    & kubectl --context kind-sarseg-p2 @args
    if ($LASTEXITCODE -ne 0) { throw "kubectl fallo: $args" }
}
Invoke-Kubectl apply -f k8s/namespace.yaml
Invoke-Kubectl apply -f k8s
Invoke-Kubectl -n sarseg-observabilidad rollout status deployment/grafana --timeout=300s
Invoke-Kubectl get nodes
Invoke-Kubectl -n sarseg-observabilidad get deployments,replicasets,pods,services -o wide
$health = Invoke-RestMethod 'http://127.0.0.1:13000/api/health'
if ($health.database -ne 'ok') { throw 'Grafana no responde con database=ok.' }
Write-Host 'Grafana disponible en http://127.0.0.1:13000'
if ($OpenBrowser) { Start-Process 'http://127.0.0.1:13000' -WindowStyle Hidden }
