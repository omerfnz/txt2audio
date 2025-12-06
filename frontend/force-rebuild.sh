#!/bin/bash
# Force rebuild script - Sunucuda çalıştırın

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "========================================"
echo "Frontend Force Rebuild"
echo "========================================"
echo ""

# 1. Eski build dosyalarını temizle
echo "[1/4] Cleaning old build files..."
rm -rf dist
rm -rf .vite
rm -rf node_modules/.vite
echo -e "${GREEN}✓ Cleaned${NC}"
echo ""

# 2. npm cache temizle (opsiyonel ama önerilir)
echo "[2/4] Clearing npm cache..."
npm cache clean --force || echo -e "${YELLOW}⚠ npm cache clean failed (continuing...)${NC}"
echo ""

# 3. Dependencies kontrolü
echo "[3/4] Checking dependencies..."
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
else
    echo -e "${GREEN}✓ Dependencies found${NC}"
fi
echo ""

# 4. Yeni build
echo "[4/4] Building frontend..."
npm run build
echo ""

# Build sonrası kontrol
if [ -d "dist" ] && [ -f "dist/index.html" ]; then
    echo -e "${GREEN}✅ Build successful!${NC}"
    echo ""
    echo "Build files:"
    ls -lh dist/
    echo ""
    echo "index.html hash check:"
    grep -o 'index-[^"]*\.js' dist/index.html || echo "Hash not found in index.html"
    echo ""
    echo "To start preview server:"
    echo "  npm run preview -- --host"
else
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

