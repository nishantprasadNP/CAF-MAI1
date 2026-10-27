#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/bias-platform/frontend"
PORT_FILE="$ROOT_DIR/bias-platform/backend/.port"

# Proxy /api to the port run-backend.sh chose (BACKEND_PORT to override).
BACKEND_PORT="${BACKEND_PORT:-$(cat "$PORT_FILE" 2>/dev/null || echo 8000)}"
export API_PROXY_TARGET="http://127.0.0.1:$BACKEND_PORT"

if ! curl -sf "$API_PROXY_TARGET/health" >/dev/null 2>&1; then
  echo "Warning: no backend answering at $API_PROXY_TARGET — start ./run-backend.sh first."
fi

npm --prefix "$FRONTEND_DIR" install
echo "API requests are proxied to $API_PROXY_TARGET"
npm --prefix "$FRONTEND_DIR" run dev
