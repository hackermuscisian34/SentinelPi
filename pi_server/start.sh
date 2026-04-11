#!/usr/bin/env bash
set -euo pipefail
if [ -f ".env" ]; then
  set -a
  . ./.env
  set +a
fi
export SENTINELPI_HOST=${SENTINELPI_HOST:-0.0.0.0}
export SENTINELPI_PORT=${SENTINELPI_PORT:-8000}

VENV_PY="../.venv/bin/python"
if [ -x "$VENV_PY" ]; then
  "$VENV_PY" -m uvicorn app.main:app --host "$SENTINELPI_HOST" --port "$SENTINELPI_PORT"
else
  python3 -m uvicorn app.main:app --host "$SENTINELPI_HOST" --port "$SENTINELPI_PORT"
fi
