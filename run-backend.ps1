$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

$backendDir = Join-Path $PSScriptRoot "bias-platform/backend"
$venvPython = Join-Path $backendDir ".venv/Scripts/python.exe"
$portFile = Join-Path $backendDir ".port"

# ---- Python virtualenv (created once, reused afterwards) ----
if (-not (Test-Path $venvPython)) {
    $pythonBin = $null
    foreach ($candidate in @("python3", "python", "py")) {
        if (Get-Command $candidate -ErrorAction SilentlyContinue) {
            & $candidate -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" *> $null
            if ($LASTEXITCODE -eq 0) {
                $pythonBin = $candidate
                break
            }
        }
    }
    if (-not $pythonBin) {
        throw "Python 3.11+ is required but was not found in PATH."
    }
    & $pythonBin -m venv (Join-Path $backendDir ".venv")
}

& $venvPython -m pip install --quiet --disable-pip-version-check -r (Join-Path $backendDir "requirements.txt")

# ---- Pick a free port (BACKEND_PORT to force one) ----
$port = $env:BACKEND_PORT
if (-not $port) {
    foreach ($candidate in 8000..8010) {
        if (-not (Get-NetTCPConnection -LocalPort $candidate -State Listen -ErrorAction SilentlyContinue)) {
            $port = $candidate
            break
        }
    }
}
if (-not $port) {
    throw "Ports 8000-8010 are all busy. Set BACKEND_PORT to a free port."
}

Set-Content -Path $portFile -Value $port
Write-Host "Backend API: http://127.0.0.1:$port  (run .\run-frontend.ps1 in another terminal)"

try {
    Set-Location $backendDir
    & $venvPython -m uvicorn app.main:app --host 127.0.0.1 --port $port --reload
}
finally {
    Remove-Item -Path $portFile -ErrorAction SilentlyContinue
}
