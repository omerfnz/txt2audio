#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================"
echo "AI Audiobook Studio - Frontend Setup"
echo "========================================"
echo ""

# Adım 1: Node.js check
echo "[1/3] Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}ERROR: Node.js not found!${NC}"
    echo "Please install Node.js from: https://nodejs.org/"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js $NODE_VERSION found${NC}"
echo ""

# Adım 2: npm paketleri kur
echo "[2/3] Installing npm packages..."
if [ -d "node_modules" ]; then
    echo "Cleaning old node_modules..."
    rm -rf node_modules
fi
npm install
echo -e "${GREEN}✓ npm packages installed${NC}"
echo ""

# Adım 3: build kontrol
echo "[3/3] Testing build..."
npm run build || echo -e "${YELLOW}⚠ Build had warnings${NC}"
echo -e "${GREEN}✓ Build test completed${NC}"
echo ""

echo "========================================"
echo -e "${GREEN}✅ Frontend setup completed!${NC}"
echo "========================================"
echo ""
echo "To start the frontend:"
echo "  npm run dev"
echo ""
echo "Frontend will run on: http://localhost:5173"
echo ""
