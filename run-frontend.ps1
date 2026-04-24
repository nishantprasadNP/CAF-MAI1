$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

$frontendPath = "bias-platform/frontend"

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm is not installed or not available in PATH."
}

npm --prefix $frontendPath install
npm --prefix $frontendPath run dev
