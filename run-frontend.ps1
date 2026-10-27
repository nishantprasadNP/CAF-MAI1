$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

$frontendPath = "bias-platform/frontend"
$portFile = "bias-platform/backend/.port"

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm is not installed or not available in PATH."
}

# Proxy /api to the port run-backend.ps1 chose (BACKEND_PORT to override).
$backendPort = $env:BACKEND_PORT
if (-not $backendPort -and (Test-Path $portFile)) {
    $backendPort = (Get-Content $portFile).Trim()
}
if (-not $backendPort) {
    $backendPort = 8000
}
$env:API_PROXY_TARGET = "http://127.0.0.1:$backendPort"
Write-Host "API requests are proxied to $env:API_PROXY_TARGET"

npm --prefix $frontendPath install
npm --prefix $frontendPath run dev
