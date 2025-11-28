#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================"
echo "AI Audiobook Studio - Unified Setup (Linux/Lightning AI)"
echo "========================================"
echo ""

# 1. System Dependencies (espeak-ng)
echo "[1/4] Checking system dependencies..."
if ! command -v espeak-ng &> /dev/null; then
    echo -e "${YELLOW}espeak-ng not found. Attempting to install...${NC}"
    if [ -f /etc/debian_version ]; then
        sudo apt-get update && sudo apt-get install -y espeak-ng
    else
        echo -e "${RED}Please install espeak-ng manually for your OS.${NC}"
        # Lightning AI'da sudo gerekebilir, hata verirse devam etmeyelim
    fi
else
    echo -e "${GREEN}✓ espeak-ng found${NC}"
fi
echo ""

# 2. Backend Setup
echo "[2/4] Setting up Backend..."
cd backend
if [ -d "venv" ]; then
    echo "Removing old venv..."
    rm -rf venv
fi
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel

# PyTorch Installation - FORCE GPU (CUDA 12.1)
# Lightning AI ve modern sunucular için varsayılan olarak GPU versiyonunu kuruyoruz.
# CPU olsa bile bu çalışır (sadece boyutu büyüktür), ama GPU varsa direkt görür.
echo "Installing PyTorch (CUDA 12.1 Enabled)..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Diğer gereksinimler
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Model Kontrolü
MODEL_DIR="$(pwd)/storage/models"
if [ -d "$MODEL_DIR" ] && [ "$(ls -A $MODEL_DIR)" ]; then
    echo -e "${GREEN}✓ Models directory exists and is not empty. Skipping download check.${NC}"
else
    echo -e "${YELLOW}ℹ Models will be downloaded on first run automatically.${NC}"
fi

cd ..
echo -e "${GREEN}✓ Backend setup complete${NC}"
echo ""

# 3. Frontend Setup
echo "[3/4] Setting up Frontend..."
cd frontend
npm install
npm run build
cd ..
echo -e "${GREEN}✓ Frontend setup complete${NC}"
echo ""

# 4. Create Start Script
echo "[4/4] Creating start script..."
cat > start.sh << 'EOF'
#!/bin/bash
# Start Backend
cd backend
source venv/bin/activate
# Modelleri tekrar indirmeyi engellemek için environment variable
export TTS_HOME="$(pwd)/storage/models"
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start Frontend (Preview)
cd ../frontend
npm run preview -- --host &
FRONTEND_PID=$!

echo "App running..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:4173"

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
EOF
chmod +x start.sh

echo "========================================"
echo -e "${GREEN}✅ Setup Completed Successfully!${NC}"
echo "To start the application, run:"
echo "  ./start.sh"
echo "========================================"
