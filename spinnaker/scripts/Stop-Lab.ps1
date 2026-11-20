$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$pidPath = Join-Path $repoRoot '.local/spinnaker/watch.pid'
if (Test-Path $pidPath) {
    $watchPid = [int](Get-Content $pidPath)
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$watchPid"
    if ($process -and $process.CommandLine -like '*git_watch.py*') { Stop-Process -Id $watchPid }
}
docker stop sarseg-spinnaker-control-plane
Write-Host 'Sondeo detenido y cluster pausado. Se conservaron datos, imagenes y volumenes.'
