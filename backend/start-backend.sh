#!/bin/bash
set -euo pipefail

echo "=== AI Audiobook Studio | Backend Start ==="

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ortam seçimi: conda > venv > sistem
if [ -n "${CONDA_PREFIX-}" ]; then
  echo "Using active conda env: $CONDA_PREFIX"
elif [ -d "$ROOT_DIR/venv" ]; then
  echo "Activating venv at $ROOT_DIR/venv"
  # shellcheck disable=SC1091
  source "$ROOT_DIR/venv/bin/activate"
else
  echo "No conda or venv detected. Using system Python."
fi

# Model yolu ve lisans
export TTS_HOME="${TTS_HOME:-$ROOT_DIR/storage/models}"
export COQUI_TOS_AGREED=1
export TTS_USE_DEEPSPEED=False

echo "TTS_HOME=$TTS_HOME"
echo "Starting Uvicorn on 0.0.0.0:8000 (reload)..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
