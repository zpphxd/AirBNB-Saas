#!/usr/bin/env bash
set -euo pipefail

PORT=${1:-8000}
API_PORT=$PORT
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[start] Using port $API_PORT"
cd "$ROOT_DIR"

# Kill existing uvicorn if recorded
if [ -f .uvicorn.pid ]; then
  PID=$(cat .uvicorn.pid || true)
  if [ -n "$PID" ]; then
    kill "$PID" 2>/dev/null || true
  fi
  rm -f .uvicorn.pid
fi

# Python env and deps
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
. .venv/bin/activate
pip install -r requirements.txt >/dev/null 2>&1 || pip install -r requirements.txt

# Build React frontend (optional; skip if offline)
if [ -f frontend/package.json ]; then
  (cd frontend && npm ci || npm i && npm run build) || echo "[start] Skipping frontend build (npm offline?)"
fi

# Start uvicorn
nohup python -m uvicorn app.main:app --host 127.0.0.1 --port "$API_PORT" > uvicorn.$API_PORT.log 2>&1 & echo $! > .uvicorn.pid
sleep 2
if curl -sf "http://127.0.0.1:${API_PORT}/health" >/dev/null; then
  echo "[start] Server healthy at http://127.0.0.1:${API_PORT}"
else
  echo "[start] Server did not respond on port ${API_PORT}. Check uvicorn.${API_PORT}.log"
  exit 1
fi

