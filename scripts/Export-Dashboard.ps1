param(
    [string]$OutputFile = 'docs/evidencias/capturas/grafana-exportacion.png'
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $repoRoot
$tokenFile = Join-Path $repoRoot '.local\renderer-token.txt'
New-Item -ItemType Directory -Path (Split-Path $tokenFile) -Force | Out-Null
if (-not (Test-Path $tokenFile)) {
    $tokenBytes = New-Object byte[] 32
    [Security.Cryptography.RandomNumberGenerator]::Fill($tokenBytes)
    [IO.File]::WriteAllText($tokenFile, [Convert]::ToBase64String($tokenBytes))
}
$renderer = docker ps -a --filter 'name=^sarseg-p2-renderer$' --format '{{.Names}}'
if (-not $renderer) {
    $env:AUTH_TOKEN = [IO.File]::ReadAllText($tokenFile).Trim()
    docker run -d --name sarseg-p2-renderer --network kind `
        -p 127.0.0.1:18081:8081 --env AUTH_TOKEN --env GOMEMLIMIT=512MiB `
        --memory 3g --cpus 2 grafana/grafana-image-renderer:v5.12.10
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo iniciar el renderer.' }
} else {
    docker start sarseg-p2-renderer | Out-Null
}
$deadline = (Get-Date).AddSeconds(90)
do {
    try {
        $rendererReady = (Invoke-WebRequest 'http://127.0.0.1:18081/healthz' -TimeoutSec 3).StatusCode -eq 200
    } catch { $rendererReady = $false }
    if (-not $rendererReady) { Start-Sleep -Seconds 2 }
} until ($rendererReady -or (Get-Date) -gt $deadline)
if (-not $rendererReady) { throw 'El renderer no esta listo.' }
$target = 'http://sarseg-p2-control-plane:30300/d/sarseg-operacion/sarseg?orgId=1&from=now-15m&to=now&kiosk=tv'
$uri = 'http://127.0.0.1:18081/render?url=' + [uri]::EscapeDataString($target) +
    '&width=1500&height=950&deviceScaleFactor=1&timeout=90&encoding=png'
$parent = Split-Path $OutputFile -Parent
if ($parent) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
Invoke-WebRequest $uri -Headers @{'X-Auth-Token'=[IO.File]::ReadAllText($tokenFile).Trim()} `
    -OutFile $OutputFile -TimeoutSec 120
$signature = [IO.File]::ReadAllBytes((Join-Path $repoRoot $OutputFile))[0..7]
if ([Convert]::ToHexString($signature) -ne '89504E470D0A1A0A') { throw 'La respuesta no es PNG.' }
Write-Host "Tablero exportado: $OutputFile"
