param([string]$Branch = 'main', [switch]$SkipBuild)
$ErrorActionPreference = 'Stop'
$labRoot = Split-Path $PSScriptRoot -Parent
$repoRoot = Split-Path $labRoot -Parent
Set-Location $repoRoot
$kindPath = Join-Path $repoRoot '.tools/kind.exe'
function Run-Checked([scriptblock]$Command) {
    & $Command
    if ($LASTEXITCODE -ne 0) { throw 'El comando anterior fallo.' }
}
Run-Checked { docker info --format '{{.ServerVersion}}' }
if (-not (Test-Path $kindPath)) {
    New-Item -ItemType Directory -Force (Split-Path $kindPath) | Out-Null
    $release = 'https://github.com/kubernetes-sigs/kind/releases/download/v0.27.0'
    Invoke-WebRequest "$release/kind-windows-amd64" -OutFile $kindPath
    $checksum = (Invoke-WebRequest "$release/kind-windows-amd64.sha256sum").Content
    if ($checksum -is [byte[]]) { $checksum = [Text.Encoding]::UTF8.GetString($checksum) }
    if ((Get-FileHash $kindPath -Algorithm SHA256).Hash.ToLower() -ne ($checksum.Trim() -split '\s+')[0]) { throw 'SHA256 de kind incorrecto.' }
}
$clusters = & $kindPath get clusters
if ($clusters -notcontains 'sarseg-spinnaker') {
    Run-Checked { & $kindPath create cluster --config spinnaker/cluster.yml --wait 180s }
}
if (-not $SkipBuild) {
    $source = Join-Path $repoRoot '.local/sarseg-source'
    if (-not (Test-Path $source)) { Run-Checked { git clone https://github.com/JOURT1/SARSEG.git $source } }
    Run-Checked { git -C $source checkout 9984bc57f1e7252793f146a40542a60940b16463 }
    Run-Checked { docker build -f "$source/deploy/web.Dockerfile" -t sarseg-web:9984bc57 $source }
    Run-Checked { docker build -f "$source/deploy/api.Dockerfile" -t sarseg-api:9984bc57 $source }
}
Run-Checked { & $kindPath load docker-image sarseg-web:9984bc57 sarseg-api:9984bc57 --name sarseg-spinnaker }
Run-Checked { python spinnaker/scripts/bootstrap.py }
Run-Checked { kubectl --context kind-sarseg-spinnaker apply -f spinnaker/platform/sarseg-backend.yml }
foreach ($name in @('mysql','redis','clouddriver','front50','orca','gate','deck')) {
    Run-Checked { kubectl --context kind-sarseg-spinnaker -n spinnaker rollout status "deployment/$name" --timeout=900s }
}
Run-Checked { kubectl --context kind-sarseg-spinnaker -n kube-system rollout status deployment/metrics-server --timeout=180s }
Run-Checked { python spinnaker/scripts/configure_pipeline.py }
$runtime = Join-Path $repoRoot '.local/spinnaker'
$pidPath = Join-Path $runtime 'watch.pid'
$watchRunning = $false
if (Test-Path $pidPath) {
    $oldPid = [int](Get-Content $pidPath)
    $oldProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$oldPid"
    $watchRunning = $null -ne $oldProcess -and $oldProcess.CommandLine -like '*git_watch.py*'
    if ($watchRunning -and $oldProcess.CommandLine -notlike "*--branch $Branch*") {
        Stop-Process -Id $oldPid
        $watchRunning = $false
    }
}
if (-not $watchRunning) {
    $process = Start-Process python -ArgumentList @('spinnaker/scripts/git_watch.py','--branch',$Branch) -WorkingDirectory $repoRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput "$runtime/watch.stdout.log" -RedirectStandardError "$runtime/watch.stderr.log"
    $process.Id | Set-Content $pidPath
}
Write-Host 'Spinnaker: http://127.0.0.1:14900/#/applications/sarseg/executions'
Write-Host 'SARSEG: http://127.0.0.1:14800 (cuando termine el primer pipeline)'
Write-Host 'Sondeo Git activo cada 20 segundos; las revisiones se confirman solo al terminar el pipeline.'
