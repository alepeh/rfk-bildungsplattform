#!/bin/bash
# Test runner script for RFK Bildungsplattform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== RFK Bildungsplattform Test Suite ===${NC}"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}Warning: No virtual environment detected${NC}"
    echo "Consider activating a virtual environment first:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
    echo ""
fi

# Set environment variables for testing
export ENVIRONMENT=test
export DEBUG=False
export SECRET_KEY=test-secret-key-for-testing-only

# Install test dependencies if requirements-test.txt exists
if [ -f "requirements-test.txt" ]; then
    echo -e "${BLUE}Installing test dependencies...${NC}"
    pip install -r requirements-test.txt
fi

# Function to run specific test suites
run_tests() {
    case $1 in
        "unit")
            echo -e "${GREEN}Running unit tests...${NC}"
            pytest core/tests/test_models.py core/tests/test_views.py -v --tb=short
            ;;
        "integration")
            echo -e "${GREEN}Running integration tests...${NC}"
            pytest core/tests/test_integration.py -v --tb=short
            ;;
        "e2e")
            echo -e "${GREEN}Running end-to-end tests...${NC}"
            echo -e "${YELLOW}Note: E2E tests require Chrome/Chromium browser${NC}"
            pytest core/tests/test_e2e.py -v --tb=short -m e2e
            ;;
        "coverage")
            echo -e "${GREEN}Running tests with coverage...${NC}"
            pytest --cov=core --cov=erweiterungen --cov-report=html --cov-report=term-missing --cov-report=xml
            echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
            ;;
        "fast")
            echo -e "${GREEN}Running fast tests (unit + integration)...${NC}"
            pytest core/tests/test_models.py core/tests/test_views.py core/tests/test_integration.py -v --tb=short
            ;;
        "all")
            echo -e "${GREEN}Running all tests...${NC}"
            pytest -v --tb=short
            ;;
        *)
            echo -e "${GREEN}Running default test suite...${NC}"
            pytest core/tests/test_models.py core/tests/test_views.py core/tests/test_integration.py -v --tb=short
            ;;
    esac
}

# Check for command line arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 [unit|integration|e2e|coverage|fast|all]"
    echo ""
    echo "Test suites:"
    echo "  unit        - Run unit tests only"
    echo "  integration - Run integration tests only"
    echo "  e2e         - Run end-to-end tests only (requires browser)"
    echo "  coverage    - Run tests with coverage reporting"
    echo "  fast        - Run unit and integration tests"
    echo "  all         - Run all tests"
    echo ""
    echo "Running default test suite (unit + integration)..."
    run_tests "fast"
else
    run_tests $1
fi

# Check if tests passed
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi