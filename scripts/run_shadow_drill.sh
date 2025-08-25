#!/bin/bash
# 🎭 WHIS SOAR Shadow Mode Drill Runner
# ====================================
# Production readiness validation for SOAR deployment

set -e

echo "🎭 WHIS SOAR Shadow Mode Validation Drill"
echo "========================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m' 
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
API_URL=${WHIS_API_URL:-"http://localhost:8001"}
UI_URL=${WHIS_UI_URL:-"http://localhost:5000"}

echo -e "${BLUE}Configuration:${NC}"
echo "  API URL: ${API_URL}"
echo "  UI URL: ${UI_URL}"
echo "  Mode: L0 Shadow (Zero Risk)"
echo ""

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    exit 1
fi

# Install required packages
pip3 install requests structlog >/dev/null 2>&1

# Check if API is running
echo -n "  API Health Check: "
if curl -s "${API_URL}/health" >/dev/null; then
    echo -e "${GREEN}✅ API Running${NC}"
else
    echo -e "${RED}❌ API Not Available${NC}"
    echo "  Start the API server first: python -m uvicorn apps.api.main:app --port 8001"
    exit 1
fi

# Check if UI is running
echo -n "  UI Availability: "
if curl -s "${UI_URL}" >/dev/null; then
    echo -e "${GREEN}✅ UI Running${NC}"
else
    echo -e "${YELLOW}⚠️  UI Not Available${NC}"
    echo "  Note: UI check is optional for API-only drill"
fi

echo ""

# Run the drill
echo -e "${BLUE}Starting Shadow Mode Validation Drill...${NC}"
echo ""

cd "$(dirname "$0")/.."

if python3 scripts/shadow_mode_drill.py --api-url "$API_URL" --ui-url "$UI_URL"; then
    echo ""
    echo -e "${GREEN}🎉 DRILL PASSED - SOAR system is ready for Shadow Mode deployment!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Review the detailed results file"
    echo "2. Deploy to production in L0 Shadow Mode"  
    echo "3. Monitor for 48 hours"
    echo "4. Review all recommendations with security team"
    echo ""
    exit 0
else
    echo ""
    echo -e "${RED}❌ DRILL FAILED - Issues detected that require resolution${NC}"
    echo ""
    echo "Required actions:"
    echo "1. Review the detailed results file"
    echo "2. Address all identified issues"
    echo "3. Re-run the drill until it passes"
    echo "4. Do not deploy until drill passes completely"
    echo ""
    exit 1
fi