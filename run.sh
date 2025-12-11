#!/bin/bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"

# Ortam seçimi: conda > venv > sistem
if [ -n "${CONDA_PREFIX-}" ]; then
  echo "Using conda env: $CONDA_PREFIX"
elif [ -d "$VENV_DIR" ]; then
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  echo "Using venv: $VENV_DIR"
else
  echo "No conda/venv detected; using system Python."
fi

export TTS_HOME="${TTS_HOME:-$BACKEND_DIR/storage/models}"
export COQUI_TOS_AGREED=1
export TTS_USE_DEEPSPEED=False

echo "Backend starting on 0.0.0.0:8000 ..."
cd "$BACKEND_DIR"
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACK_PID=$!

echo "Frontend starting on 0.0.0.0:5173 ..."
cd "$FRONTEND_DIR"
npm run dev -- --host --port 5173 &
FRONT_PID=$!

echo "Backend PID: $BACK_PID"
echo "Frontend PID: $FRONT_PID"
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"

trap "kill $BACK_PID $FRONT_PID" EXIT
wait
