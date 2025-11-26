#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "========================================"
echo "AI Audiobook Studio - Complete Setup"
echo "========================================"
echo ""

# Backend setup
echo ""
echo -e "${BLUE}░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░${NC}"
echo -e "${BLUE}░ BACKEND SETUP${NC}"
echo -e "${BLUE}░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░${NC}"
cd backend
chmod +x setup.sh
bash setup.sh
cd ..
echo ""

# Frontend setup
echo ""
echo -e "${BLUE}░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░${NC}"
echo -e "${BLUE}░ FRONTEND SETUP${NC}"
echo -e "${BLUE}░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░${NC}"
cd frontend
chmod +x setup.sh
bash setup.sh
cd ..
echo ""

echo "========================================"
echo -e "${GREEN}✅ COMPLETE SETUP FINISHED!${NC}"
echo "========================================"
echo ""
echo "NEXT STEPS:"
echo ""
echo "1. Backend (Terminal 1):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "2. Frontend (Terminal 2):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Open browser:"
echo "   http://localhost:5173"
echo ""
