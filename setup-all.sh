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

# 1. System Dependencies (espeak-ng & ffmpeg)
echo "[1/4] Checking system dependencies..."

# Check espeak-ng
if ! command -v espeak-ng &> /dev/null; then
    echo -e "${YELLOW}espeak-ng not found. Attempting to install...${NC}"
    if [ -f /etc/debian_version ]; then
        # Check if we have sudo
        if command -v sudo &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y espeak-ng
        else
            echo -e "${YELLOW}sudo not found. Trying to install without sudo (might fail)...${NC}"
            apt-get update && apt-get install -y espeak-ng
        fi
    else
        echo -e "${RED}Please install espeak-ng manually for your OS.${NC}"
    fi
else
    echo -e "${GREEN}✓ espeak-ng found${NC}"
fi

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}ffmpeg not found. Attempting to install...${NC}"
    if [ -f /etc/debian_version ]; then
        if command -v sudo &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y ffmpeg
        else
            echo -e "${YELLOW}sudo not found. Trying to install without sudo (might fail)...${NC}"
            apt-get update && apt-get install -y ffmpeg
        fi
    else
        echo -e "${RED}Please install ffmpeg manually for your OS.${NC}"
        echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
        echo "  macOS: brew install ffmpeg"
        echo "  CentOS/RHEL: sudo yum install ffmpeg"
    fi
else
    echo -e "${GREEN}✓ ffmpeg found${NC}"
fi
echo ""

# 2. Backend Setup
echo "[2/4] Setting up Backend..."
cd backend

# Venv Handling
USE_VENV=true
echo "Attempting to create virtual environment..."

# Remove old venv if exists
if [ -d "venv" ]; then
    rm -rf venv
fi

# Try to create venv, if fails, use system python
if python3 -m venv venv 2>/dev/null; then
    echo -e "${GREEN}✓ Virtual environment created.${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠ Virtual environment creation failed or restricted.${NC}"
    echo -e "${YELLOW}ℹ Using system Python environment (Conda/System Default).${NC}"
    USE_VENV=false
fi

pip install --upgrade pip setuptools wheel

# PyTorch Installation - FORCE GPU (CUDA 12.1)
echo "Installing PyTorch (CUDA 12.1 Enabled)..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Other requirements
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Model Check
MODEL_DIR="$(pwd)/storage/models"
if [ -d "$MODEL_DIR" ] && [ "$(ls -A $MODEL_DIR)" ]; then
    echo -e "${GREEN}✓ Models directory exists and is not empty.${NC}"
else
    echo -e "${YELLOW}ℹ Models will be downloaded on first run.${NC}"
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

# Start building start.sh
echo "#!/bin/bash" > start.sh
echo "# Start Backend" >> start.sh
echo "cd backend" >> start.sh

# Only activate venv if we created one
if [ "$USE_VENV" = true ]; then
    echo "source venv/bin/activate" >> start.sh
fi

# Continue building start.sh
cat >> start.sh << 'EOF'
# Prevent re-downloading models
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
