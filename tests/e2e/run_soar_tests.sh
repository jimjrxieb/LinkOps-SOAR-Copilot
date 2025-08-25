#!/bin/bash
# 🎭 WHIS SOAR E2E Test Runner
# ===========================
# Production-ready test suite for all autonomy levels

set -e

echo "🚀 Starting WHIS SOAR E2E Test Suite..."
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WHIS_API_URL=${WHIS_API_URL:-"http://localhost:8001"}
WHIS_UI_URL=${WHIS_UI_URL:-"http://localhost:5000"}
TEST_ENV=${TEST_ENV:-"development"}

echo -e "${BLUE}Configuration:${NC}"
echo -e "  API URL: ${WHIS_API_URL}"
echo -e "  UI URL: ${WHIS_UI_URL}"  
echo -e "  Environment: ${TEST_ENV}"
echo ""

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v npx &> /dev/null; then
    echo -e "${RED}Error: npx not found. Please install Node.js${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    exit 1
fi

# Install Playwright if needed
if ! npx playwright --version &> /dev/null; then
    echo -e "${YELLOW}Installing Playwright...${NC}"
    npm init -y
    npm install --save-dev @playwright/test
    npx playwright install
fi

# Start services if not running
echo -e "${BLUE}Starting WHIS services...${NC}"

# Check if API is running
if ! curl -s "${WHIS_API_URL}/health" > /dev/null; then
    echo -e "${YELLOW}Starting WHIS API on port 8001...${NC}"
    cd ../..
    python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8001 &
    API_PID=$!
    cd tests/e2e
    
    # Wait for API to be ready
    echo "Waiting for API to start..."
    for i in {1..30}; do
        if curl -s "${WHIS_API_URL}/health" > /dev/null; then
            echo -e "${GREEN}API is ready!${NC}"
            break
        fi
        sleep 2
    done
    
    if [ $i -eq 30 ]; then
        echo -e "${RED}API failed to start${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}API is already running${NC}"
fi

# Check if UI is running  
if ! curl -s "${WHIS_UI_URL}" > /dev/null; then
    echo -e "${YELLOW}Starting WHIS UI on port 5000...${NC}"
    cd ../../apps/ui
    python -m http.server 5000 &
    UI_PID=$!
    cd ../../tests/e2e
    
    sleep 3
    if curl -s "${WHIS_UI_URL}" > /dev/null; then
        echo -e "${GREEN}UI is ready!${NC}"
    else
        echo -e "${RED}UI failed to start${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}UI is already running${NC}"
fi

echo ""

# Run tests
echo -e "${BLUE}Running SOAR E2E Tests...${NC}"
echo "========================"

# Test categories
declare -a test_categories=(
    "L0.*Shadow Mode"
    "L1.*Read-Only Mode"
    "L2.*Conditional Mode"
    "L3.*Manual Approval Mode"
    "Integration.*Safety Tests"
    "Performance Tests"
    "Deployment Readiness"
)

# Run tests by category
for category in "${test_categories[@]}"; do
    echo -e "\n${BLUE}Running: ${category}${NC}"
    echo "----------------------------------------"
    
    if npx playwright test --grep "${category}" --config=playwright.config.js; then
        echo -e "${GREEN}✅ ${category} - PASSED${NC}"
    else
        echo -e "${RED}❌ ${category} - FAILED${NC}"
        FAILED_TESTS="${FAILED_TESTS}${category}\n"
    fi
done

# Generate report
echo -e "\n${BLUE}Generating test report...${NC}"
npx playwright show-report test-results/html-report

# Summary
echo ""
echo "============================================="
echo -e "${BLUE}WHIS SOAR E2E Test Results Summary${NC}"
echo "============================================="

if [ -z "$FAILED_TESTS" ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}SOAR system is ready for deployment${NC}"
    exit_code=0
else
    echo -e "${RED}❌ SOME TESTS FAILED:${NC}"
    echo -e "${RED}${FAILED_TESTS}${NC}"
    echo -e "${YELLOW}Review test report before deployment${NC}"
    exit_code=1
fi

echo ""
echo "Test artifacts:"
echo "  - HTML Report: test-results/html-report/index.html"
echo "  - JSON Results: test-results/results.json"
echo "  - JUnit XML: test-results/junit.xml"

# Cleanup
if [ ! -z "$API_PID" ]; then
    echo -e "\n${BLUE}Stopping API server...${NC}"
    kill $API_PID
fi

if [ ! -z "$UI_PID" ]; then
    echo -e "${BLUE}Stopping UI server...${NC}"
    kill $UI_PID
fi

echo -e "\n${GREEN}Test run complete!${NC}"
exit $exit_code