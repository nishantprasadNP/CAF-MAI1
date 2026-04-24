#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

python3 -m pip install -r "bias-platform/backend/requirements.txt"
PYTHONPATH="bias-platform/backend" uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
