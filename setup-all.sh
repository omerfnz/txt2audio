#!/bin/bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"

echo "========================================"
echo "AI Audiobook Studio - Otomatik Kurulum (Linux/Lightning AI, sudo yok)"
echo "========================================"
echo ""

echo "[1/5] Sistem bağımlılıkları kontrol (yalnızca uyarı)"
for bin in espeak-ng ffmpeg; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ $bin bulunamadı. Lütfen sistem paket yöneticisi ile kurun.${NC}"
  else
    echo -e "${GREEN}✓ $bin bulundu${NC}"
  fi
done
echo ""

echo "[2/5] Python ortamı (conda varsa kullanır, yoksa venv oluşturur)"
ACTIVATION_DONE=false
if [ -n "${CONDA_PREFIX-}" ]; then
  echo -e "${GREEN}✓ Conda ortamı aktif: ${CONDA_PREFIX}${NC}"
  ACTIVATION_DONE=true
else
  if [ -d "$VENV_DIR" ]; then
    echo -e "${GREEN}✓ Venv bulundu. Aktivasyon...${NC}"
  else
    echo -e "${YELLOW}Venv yok, oluşturuluyor...${NC}"
    python3 -m venv "$VENV_DIR"
  fi
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  ACTIVATION_DONE=true
  echo -e "${GREEN}✓ Python ortamı aktif${NC}"
fi
echo ""

echo "[3/5] Backend bağımlılıkları kuruluyor"
cd "$BACKEND_DIR"
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python -m spacy download en_core_web_sm || echo -e "${YELLOW}⚠ Spacy modeli indirilemedi, tekrar deneyin.${NC}"
pip uninstall -y torchcodec || true
pip install ffmpeg-python
echo -e "${GREEN}✓ Backend bağımlılıkları yüklendi${NC}"
echo ""

echo "[4/5] Frontend bağımlılıkları kuruluyor"
cd "$FRONTEND_DIR"
npm install
npm run build
echo -e "${GREEN}✓ Frontend hazır (build alındı)${NC}"
echo ""

echo "[5/5] Çalıştırma scriptleri oluşturuluyor"
cd "$ROOT_DIR"

cat > run.sh <<'EOF'
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
EOF
chmod +x run.sh

cat > run.cmd <<'EOF'
@echo off
setlocal enabledelayedexpansion
set ROOT=%~dp0
set BACKEND=%ROOT%backend
set FRONTEND=%ROOT%frontend
set VENV=%BACKEND%\venv

rem Kullanılacak Python ortamı
if defined CONDA_PREFIX (
  echo Using conda: %CONDA_PREFIX%
) else (
  if exist "%VENV%\Scripts\activate.bat" (
    call "%VENV%\Scripts\activate.bat"
    echo Using venv: %VENV%
  ) else (
    echo No conda/venv detected; using system Python.
  )
)

set TTS_HOME=%BACKEND%\storage\models
set COQUI_TOS_AGREED=1
set TTS_USE_DEEPSPEED=False

echo Starting backend on 0.0.0.0:8000 ...
start "backend" cmd /k "cd /d %BACKEND% && set TTS_HOME=%TTS_HOME% && set COQUI_TOS_AGREED=1 && set TTS_USE_DEEPSPEED=False && uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo Starting frontend on 0.0.0.0:5173 ...
start "frontend" cmd /k "cd /d %FRONTEND% && npm run dev -- --host --port 5173"

echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
EOF

echo -e "${GREEN}✓ run.sh ve run.cmd oluşturuldu${NC}"
echo ""

echo "========================================"
echo -e "${GREEN}Kurulum tamamlandı. Çalıştırmak için: ${NC}"
echo "Linux/macOS: ./run.sh"
echo "Windows:     run.cmd"
echo "========================================"
