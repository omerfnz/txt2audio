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

# Function to check and install package
install_package() {
    PACKAGE=$1
    if ! command -v $PACKAGE &> /dev/null; then
        echo -e "${YELLOW}$PACKAGE not found. Attempting to install...${NC}"
        if [ -f /etc/debian_version ]; then
            if command -v sudo &> /dev/null; then
                sudo apt-get update && sudo apt-get install -y $PACKAGE
            else
                echo -e "${YELLOW}sudo not found. Trying to install without sudo...${NC}"
                apt-get update && apt-get install -y $PACKAGE
            fi
        else
            echo -e "${RED}Please install $PACKAGE manually for your OS.${NC}"
        fi
    else
        echo -e "${GREEN}✓ $PACKAGE found${NC}"
    fi
}

install_package espeak-ng
install_package ffmpeg
echo ""

# 2. Backend Setup
echo "[2/4] Setting up Backend..."
cd backend

# Venv Handling
USE_VENV=true

if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Virtual environment found. Activating...${NC}"
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    if python3 -m venv venv 2>/dev/null; then
        echo -e "${GREEN}✓ Virtual environment created.${NC}"
        source venv/bin/activate
    else
        echo -e "${YELLOW}⚠ Virtual environment creation failed or restricted.${NC}"
        echo -e "${YELLOW}ℹ Using system Python environment.${NC}"
        USE_VENV=false
    fi
fi

echo "Installing/Updating Python dependencies..."
pip install --upgrade pip setuptools wheel

# PyTorch Installation - FORCE GPU (CUDA 12.1)
# Check if torch is installed to avoid costly re-download
if ! python -c "import torch" &> /dev/null; then
    echo "Installing PyTorch (CUDA 12.1 Enabled)..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
else
    echo -e "${GREEN}✓ PyTorch already installed.${NC}"
fi

# Optional: DeepSpeed
if ! python -c "import deepspeed" &> /dev/null; then
    echo "Checking for DeepSpeed compatibility..."
    if python -c "import torch; import platform; print(torch.cuda.is_available() and platform.system() != 'Windows')" 2>/dev/null | grep -q "True"; then
        echo "Installing DeepSpeed..."
        pip install deepspeed || echo -e "${YELLOW}⚠ DeepSpeed installation failed, continuing without it.${NC}"
    else
        echo -e "${YELLOW}ℹ DeepSpeed skipped (no CUDA GPU or unsupported platform).${NC}"
    fi
fi

# Other requirements
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Model Check
MODEL_DIR="$(pwd)/storage/models"
if [ ! -d "$MODEL_DIR" ] || [ -z "$(ls -A $MODEL_DIR)" ]; then
    echo -e "${YELLOW}ℹ Models will be downloaded on first run.${NC}"
fi

cd ..
echo -e "${GREEN}✓ Backend setup complete${NC}"
echo ""

# 3. Frontend Setup
echo "[3/4] Setting up Frontend..."
cd frontend

# node_modules kontrolü - paketlerin eksik olup olmadığını kontrol et
if [ ! -d "node_modules" ] || [ ! -d "node_modules/@radix-ui" ] || [ ! -d "node_modules/class-variance-authority" ]; then
    echo "Installing/Updating npm packages..."
    if [ -d "node_modules" ]; then
        echo "Cleaning old node_modules..."
        rm -rf node_modules
    fi
    npm install
else
    echo -e "${GREEN}✓ node_modules found. Verifying packages...${NC}"
    # Kritik paketlerin varlığını kontrol et
    if [ ! -d "node_modules/@radix-ui/react-slot" ] || [ ! -d "node_modules/class-variance-authority" ]; then
        echo -e "${YELLOW}⚠ Some packages missing. Reinstalling...${NC}"
        npm install
    else
        echo -e "${GREEN}✓ All packages verified${NC}"
    fi
fi

echo "Cleaning old build files..."
rm -rf dist
echo "Building frontend..."
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
export COQUI_TOS_AGREED=1

echo "Starting Backend..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start Frontend
cd ../frontend
echo "Ensuring frontend dependencies..."
npm install
echo "Cleaning old build files..."
rm -rf dist
echo "Building frontend..."
npm run build
echo "Starting Frontend Server..."
npm run preview -- --host &
FRONTEND_PID=$!

echo "========================================"
echo "🚀 App running!"
echo "Backend API: http://localhost:8000"
echo "Frontend UI: http://localhost:4173"
echo "========================================"

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
EOF

chmod +x start.sh

echo "========================================"
echo -e "${GREEN}✅ Setup Completed Successfully!${NC}"
echo "To start the application, run:"
echo "  ./start.sh"
echo "========================================"
