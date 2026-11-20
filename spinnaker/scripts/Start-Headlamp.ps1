param([string]$Context = 'kind-sarseg-spinnaker', [int]$Port = 14666)
$ErrorActionPreference = 'Stop'
$labRoot = Split-Path $PSScriptRoot -Parent
$repoRoot = Split-Path $labRoot -Parent
$statePath = Join-Path $repoRoot '.local/spinnaker'
New-Item -ItemType Directory -Force -Path $statePath | Out-Null
kubectl --context $Context apply -f (Join-Path $labRoot 'platform/headlamp-readonly.yml')
if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar Headlamp.' }
kubectl --context $Context -n kube-system rollout status deployment/headlamp --timeout=180s
if ($LASTEXITCODE -ne 0) { throw 'Headlamp no está disponible.' }
$readerToken = kubectl --context $Context -n kube-system create token headlamp-reader --duration=2h
if ($LASTEXITCODE -ne 0) { throw 'No se pudo obtener el token temporal.' }
$readerToken | Set-Content -LiteralPath (Join-Path $statePath 'headlamp-token.txt') -NoNewline
$forwardProcess = Start-Process kubectl -ArgumentList @('--context', $Context, '-n', 'kube-system', 'port-forward', 'service/headlamp', "${Port}:80", '--address', '127.0.0.1') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $statePath 'headlamp-forward.log') -RedirectStandardError (Join-Path $statePath 'headlamp-forward-error.log')
$forwardProcess.Id | Set-Content (Join-Path $statePath 'headlamp-forward.pid')
Write-Output "Headlamp: http://127.0.0.1:$Port. Token temporal en .local/spinnaker/headlamp-token.txt (excluido de Git)."
