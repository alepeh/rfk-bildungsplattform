#!/bin/bash

# E2E Test Runner for RFK Bildungsplattform
# Usage: ./scripts/run_e2e_tests.sh [local|staging|production]

set -e

# Default to local if no argument provided
TARGET=${1:-local}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "=== RFK Bildungsplattform E2E Test Runner ==="
echo "Target environment: $TARGET"

# Set up virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt
pip install -r requirements-test.txt

# Set environment variables based on target
case $TARGET in
    "local")
        echo "Running E2E tests against local development server..."
        export DJANGO_SETTINGS_MODULE=bildungsplattform.settings
        export ENVIRONMENT=development
        export DEBUG=True
        export SECRET_KEY=test-secret-key-for-local-e2e
        export E2E_BASE_URL="http://127.0.0.1:8000"
        
        # Use SQLite for local testing to avoid PostgreSQL dependency
        export USE_SQLITE=true
        
        # Check if local server is running
        if ! curl -s http://127.0.0.1:8000 >/dev/null 2>&1; then
            echo "ERROR: Local development server is not running on port 8000"
            echo "Please start the server with:"
            echo "  export ENVIRONMENT=development DEBUG=True SECRET_KEY=test-key USE_SQLITE=true"
            echo "  python manage.py migrate"
            echo "  python manage.py runserver"
            exit 1
        fi
        ;;
        
    "staging")
        echo "Running E2E tests against staging environment..."
        export DJANGO_SETTINGS_MODULE=bildungsplattform.settings
        export ENVIRONMENT=staging
        export DEBUG=False
        export SECRET_KEY=staging-e2e-test-key
        export E2E_BASE_URL="https://bildungsplattform-test.rauchfangkehrer.or.at"
        
        # Check if staging is accessible
        if ! curl -s "$E2E_BASE_URL" >/dev/null 2>&1; then
            echo "WARNING: Staging environment may not be accessible at $E2E_BASE_URL"
            echo "Continuing with tests..."
        fi
        ;;
        
    "production")
        echo "Running E2E tests against production environment..."
        echo "WARNING: Running E2E tests against production should be done with caution!"
        read -p "Are you sure you want to run E2E tests against production? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Cancelled."
            exit 0
        fi
        
        export DJANGO_SETTINGS_MODULE=bildungsplattform.settings
        export ENVIRONMENT=production
        export DEBUG=False
        export SECRET_KEY=production-e2e-test-key
        export E2E_BASE_URL="https://bildungsplattform.rauchfangkehrer.or.at"
        ;;
        
    *)
        echo "Invalid target: $TARGET"
        echo "Usage: $0 [local|staging|production]"
        exit 1
        ;;
esac

echo "Creating logs directory..."
mkdir -p logs

echo "Running E2E tests..."
echo "Target URL: $E2E_BASE_URL"

# Run the E2E tests
pytest core/tests/test_e2e.py -v --tb=short -m e2e --junitxml=junit/test-results-e2e.xml

echo "E2E tests completed successfully!"