#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/bias-platform/backend"
VENV_DIR="$BACKEND_DIR/.venv"
PORT_FILE="$BACKEND_DIR/.port"

# ---- Python virtualenv (created once, reused afterwards) ----
if [ ! -x "$VENV_DIR/bin/python" ]; then
  PYTHON_BIN=""
  for candidate in python3.13 python3.12 python3.11 python3.14 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 &&
      "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
      PYTHON_BIN="$candidate"
      break
    fi
  done
  if [ -z "$PYTHON_BIN" ]; then
    echo "Error: Python 3.11+ is required but was not found in PATH."
    exit 1
  fi
  echo "Creating virtualenv with $("$PYTHON_BIN" --version)..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --quiet --disable-pip-version-check -r "$BACKEND_DIR/requirements.txt"

# ---- Pick a free port (BACKEND_PORT to force one) ----
port_in_use() {
  "$VENV_DIR/bin/python" -c 'import socket,sys; s=socket.socket(); sys.exit(0 if s.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0 else 1)' "$1"
}

PORT="${BACKEND_PORT:-}"
if [ -z "$PORT" ]; then
  for candidate in $(seq 8000 8010); do
    if ! port_in_use "$candidate"; then
      PORT="$candidate"
      break
    fi
  done
fi
if [ -z "$PORT" ]; then
  echo "Error: ports 8000-8010 are all busy. Set BACKEND_PORT to a free port."
  exit 1
fi

echo "$PORT" > "$PORT_FILE"
trap 'rm -f "$PORT_FILE"' EXIT

echo "Backend API: http://127.0.0.1:$PORT  (run ./run-frontend.sh in another terminal)"
cd "$BACKEND_DIR"
"$VENV_DIR/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" --reload
