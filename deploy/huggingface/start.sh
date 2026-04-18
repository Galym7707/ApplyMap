#!/usr/bin/env bash
set -euo pipefail

export PORT="${PORT:-7860}"
export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-/}"
export INTERNAL_API_URL="${INTERNAL_API_URL:-http://127.0.0.1:8000}"
export BACKEND_CORS_ORIGINS="${BACKEND_CORS_ORIGINS:-[\"http://localhost:${PORT}\",\"http://127.0.0.1:${PORT}\"]}"

cd /home/node/app/apps/api
/home/node/venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 &
api_pid=$!

cleanup() {
  kill "$api_pid" 2>/dev/null || true
}
trap cleanup EXIT

sleep 2
if ! kill -0 "$api_pid" 2>/dev/null; then
  wait "$api_pid"
fi

cd /home/node/app/apps/web
exec pnpm exec next start -p "$PORT" -H 0.0.0.0
