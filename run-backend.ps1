$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

$pythonBin = $null
foreach ($candidate in @("python3", "python")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        try {
            & $candidate -c "import sys" *> $null
            if ($LASTEXITCODE -eq 0) {
                $pythonBin = $candidate
                break
            }
        } catch {
            # Try next candidate
        }
    }
}

if (-not $pythonBin) {
    throw "Python is not installed or not available in PATH."
}

& $pythonBin -m pip install -r "bias-platform/backend/requirements.txt"
$env:PYTHONPATH = "bias-platform/backend"
& $pythonBin -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
