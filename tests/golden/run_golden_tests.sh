#!/bin/bash
# 🏆 WHIS SOAR Golden Tests Runner
# ===============================
# Ensures deterministic decision mapping for deployment readiness

set -e

echo "🏆 Starting WHIS SOAR Golden Decision Tests..."
echo "=============================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m' 
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$TEST_DIR")")"
RESULTS_DIR="${TEST_DIR}/results"

echo -e "${BLUE}Configuration:${NC}"
echo "  Test Directory: ${TEST_DIR}"
echo "  Root Directory: ${ROOT_DIR}"
echo "  Results Directory: ${RESULTS_DIR}"
echo ""

# Create results directory
mkdir -p "${RESULTS_DIR}"

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    exit 1
fi

# Install required packages if needed
if ! python3 -c "import pytest" &> /dev/null; then
    echo -e "${YELLOW}Installing pytest...${NC}"
    pip3 install pytest
fi

# Verify decision graph exists
DECISION_GRAPH="${ROOT_DIR}/apps/api/engines/decision_graph.yaml"
if [ ! -f "$DECISION_GRAPH" ]; then
    echo -e "${RED}Error: Decision graph not found at ${DECISION_GRAPH}${NC}"
    exit 1
fi

echo -e "${GREEN}Prerequisites satisfied${NC}"
echo ""

# Run golden tests
echo -e "${BLUE}Running Golden Decision Tests...${NC}"
echo "================================"

cd "$ROOT_DIR"

# Run the golden test suite
if python3 -m tests.golden.decision_mapping_tests; then
    echo -e "\n${GREEN}✅ All Golden Tests PASSED${NC}"
    echo -e "${GREEN}Decision mapping is deterministic and ready for deployment${NC}"
    EXIT_CODE=0
else
    echo -e "\n${RED}❌ Some Golden Tests FAILED${NC}"
    echo -e "${RED}Decision logic needs review before deployment${NC}"
    EXIT_CODE=1
fi

# Generate additional reports
echo -e "\n${BLUE}Generating additional reports...${NC}"

# Coverage report for decision paths
echo "📊 Decision Path Coverage Report" > "${RESULTS_DIR}/coverage_report.txt"
echo "=================================" >> "${RESULTS_DIR}/coverage_report.txt"
echo "Test Date: $(date)" >> "${RESULTS_DIR}/coverage_report.txt"
echo "" >> "${RESULTS_DIR}/coverage_report.txt"

# Count tests by runbook
echo "Tests by Runbook:" >> "${RESULTS_DIR}/coverage_report.txt"
grep -o "expected_runbook=\"RB-[0-9]*\"" "${TEST_DIR}/decision_mapping_tests.py" | sort | uniq -c | while read count runbook; do
    runbook_id=$(echo "$runbook" | grep -o "RB-[0-9]*")
    echo "  $runbook_id: $count tests" >> "${RESULTS_DIR}/coverage_report.txt"
done

echo "" >> "${RESULTS_DIR}/coverage_report.txt"

# Count tests by MITRE technique
echo "Tests by MITRE ATT&CK Technique:" >> "${RESULTS_DIR}/coverage_report.txt"
grep -o "T[0-9]\{4\}\(\.[0-9]\{3\}\)\?" "${TEST_DIR}/decision_mapping_tests.py" | sort | uniq -c | while read count technique; do
    echo "  $technique: $count tests" >> "${RESULTS_DIR}/coverage_report.txt"
done

# Determinism validation
echo -e "\n${BLUE}Running determinism validation...${NC}"

DETERMINISM_RESULTS="${RESULTS_DIR}/determinism_validation.txt"
echo "🔒 Determinism Validation Report" > "$DETERMINISM_RESULTS"
echo "================================" >> "$DETERMINISM_RESULTS" 
echo "Test Date: $(date)" >> "$DETERMINISM_RESULTS"
echo "" >> "$DETERMINISM_RESULTS"

# Run same test multiple times to ensure identical results
echo "Running identical test 5 times to verify determinism..." >> "$DETERMINISM_RESULTS"
echo "" >> "$DETERMINISM_RESULTS"

for i in {1..5}; do
    echo "Run $i:" >> "$DETERMINISM_RESULTS"
    # This would run a single test multiple times and compare hashes
    python3 -c "
import hashlib
import json
from tests.golden.decision_mapping_tests import GOLDEN_TESTS, DecisionTester

# Run first test 
tester = DecisionTester('apps/api/engines/decision_graph.yaml')
result = tester._run_single_test(GOLDEN_TESTS[0])

# Create hash of result (excluding timestamp)
result_copy = result.copy()
if 'execution_time_ms' in result_copy:
    del result_copy['execution_time_ms']

result_hash = hashlib.md5(json.dumps(result_copy, sort_keys=True).encode()).hexdigest()
print(f'  Hash: {result_hash}')
" >> "$DETERMINISM_RESULTS"
done

# Check if all hashes are identical
UNIQUE_HASHES=$(tail -5 "$DETERMINISM_RESULTS" | grep "Hash:" | cut -d' ' -f4 | sort | uniq | wc -l)

if [ "$UNIQUE_HASHES" -eq 1 ]; then
    echo -e "\n${GREEN}✅ DETERMINISM VERIFIED: All runs produced identical results${NC}"
    echo "" >> "$DETERMINISM_RESULTS"
    echo "✅ DETERMINISM VERIFIED: All 5 runs produced identical results" >> "$DETERMINISM_RESULTS"
else
    echo -e "\n${RED}❌ NON-DETERMINISTIC BEHAVIOR DETECTED${NC}"
    echo "" >> "$DETERMINISM_RESULTS"
    echo "❌ NON-DETERMINISTIC: Found $UNIQUE_HASHES different results" >> "$DETERMINISM_RESULTS"
    EXIT_CODE=1
fi

# Performance validation
echo -e "\n${BLUE}Running performance validation...${NC}"

PERF_RESULTS="${RESULTS_DIR}/performance_results.txt"
echo "⚡ Performance Validation Report" > "$PERF_RESULTS"
echo "===============================" >> "$PERF_RESULTS"
echo "Test Date: $(date)" >> "$PERF_RESULTS"
echo "" >> "$PERF_RESULTS"

# Measure decision time
python3 -c "
import time
import statistics
from tests.golden.decision_mapping_tests import GOLDEN_TESTS, DecisionTester

tester = DecisionTester('apps/api/engines/decision_graph.yaml')
times = []

print('Running performance tests...')
for test in GOLDEN_TESTS[:10]:  # Test first 10 for speed
    start = time.time()
    result = tester._run_single_test(test)
    end = time.time()
    times.append((end - start) * 1000)  # Convert to ms

avg_time = statistics.mean(times)
max_time = max(times)
min_time = min(times)

print(f'Average Decision Time: {avg_time:.2f}ms')
print(f'Maximum Decision Time: {max_time:.2f}ms')
print(f'Minimum Decision Time: {min_time:.2f}ms')

if avg_time < 100:  # Less than 100ms
    print('✅ PERFORMANCE: Decision times are within acceptable limits')
else:
    print('⚠️ PERFORMANCE: Decision times may be too slow for production')
    exit(1)
" >> "$PERF_RESULTS"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Performance validation passed${NC}"
else
    echo -e "${YELLOW}⚠️ Performance validation had warnings${NC}"
fi

# Summary
echo ""
echo "============================================="
echo -e "${BLUE}Golden Test Suite Complete${NC}"
echo "============================================="

echo ""
echo "📋 Generated Reports:"
echo "  - Golden Test Results: tests/golden/golden_test_results.json"
echo "  - Coverage Report: ${RESULTS_DIR}/coverage_report.txt"
echo "  - Determinism Validation: ${RESULTS_DIR}/determinism_validation.txt"  
echo "  - Performance Results: ${PERF_RESULTS}"

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL GOLDEN TESTS PASSED${NC}"
    echo -e "${GREEN}SOAR decision logic is deterministic and ready for deployment${NC}"
else
    echo ""
    echo -e "${RED}❌ GOLDEN TESTS FAILED${NC}"
    echo -e "${RED}Review decision logic before proceeding with deployment${NC}"
fi

echo ""
exit $EXIT_CODE