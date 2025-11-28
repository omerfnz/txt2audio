#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================"
echo "AI Audiobook Studio - Backend Setup"
echo "========================================"
echo ""

# Adım 1: venv oluştur
echo "[1/7] Creating Python virtual environment..."
if [ -d "venv" ]; then
    echo "Removing old venv..."
    rm -rf venv
fi
python3 -m venv venv
echo -e "${GREEN}✓ venv created${NC}"
echo ""

# Adım 2: venv aktifleştir
echo "[2/7] Activating venv..."
source venv/bin/activate
echo -e "${GREEN}✓ venv activated${NC}"
echo ""

# Adım 3: pip güncelle
echo "[3/7] Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Adım 4: PyTorch kur
echo "[4/7] Installing PyTorch..."
if python install_pytorch.py; then
    echo -e "${GREEN}✓ PyTorch installed${NC}"
else
    echo -e "${YELLOW}Trying manual CPU installation...${NC}"
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi
echo ""

# Adım 5: requirements.txt paketleri kur
echo "[5/7] Installing requirements..."
pip install -r requirements.txt
echo -e "${GREEN}✓ requirements installed${NC}"
echo ""

# Adım 6: Spacy model indir
echo "[6/7] Downloading Spacy model..."
python -m spacy download en_core_web_sm || echo -e "${YELLOW}⚠ Spacy model download had issues${NC}"
echo -e "${GREEN}✓ Spacy model setup complete${NC}"
echo ""

# Adım 7: espeak-ng check
echo "[7/8] Checking espeak-ng..."
if ! command -v espeak-ng &> /dev/null; then
    echo -e "${YELLOW}⚠ espeak-ng not found!${NC}"
    echo "Please install:"
    echo "  Ubuntu/Debian: sudo apt-get install espeak-ng"
    echo "  macOS: brew install espeak-ng"
else
    echo -e "${GREEN}✓ espeak-ng found${NC}"
fi
echo ""

# Adım 8: ffmpeg check
echo "[8/8] Checking ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}⚠ ffmpeg not found!${NC}"
    echo "ffmpeg is required for audio merging. Please install:"
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  CentOS/RHEL: sudo yum install ffmpeg"
    echo ""
    echo -e "${RED}⚠ Audio merging will fail without ffmpeg!${NC}"
else
    echo -e "${GREEN}✓ ffmpeg found${NC}"
fi
echo ""

echo "========================================"
echo -e "${GREEN}✅ Backend setup completed!${NC}"
echo "========================================"
echo ""
echo "To start the backend:"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
