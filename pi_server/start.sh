#!/usr/bin/env bash
set -euo pipefail
if [ -f ".env" ]; then
  set -a
  . ./.env
  set +a
fi
export SENTINELPI_HOST=${SENTINELPI_HOST:-0.0.0.0}
export SENTINELPI_PORT=${SENTINELPI_PORT:-8000}
uvicorn app.main:app --host "$SENTINELPI_HOST" --port "$SENTINELPI_PORT"
