#!/usr/bin/env bash
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -f .uvicorn.pid ]; then
  PID=$(cat .uvicorn.pid || true)
  if [ -n "$PID" ]; then
    kill "$PID" 2>/dev/null || true
  fi
  rm -f .uvicorn.pid
  echo "[stop] Stopped server PID ${PID}"
else
  echo "[stop] No PID file found"
fi
