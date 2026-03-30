#!/bin/bash
# Frontend code quality check script
# Runs Prettier format checks on all frontend files

set -e

FRONTEND_DIR="$(dirname "$0")/../frontend"

echo "=== Frontend Quality Checks ==="
echo ""

# Check if node_modules exists
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "Installing frontend dependencies..."
    (cd "$FRONTEND_DIR" && npm install)
    echo ""
fi

echo "Checking formatting with Prettier..."
if (cd "$FRONTEND_DIR" && npm run format:check); then
    echo ""
    echo "All frontend files are correctly formatted."
else
    echo ""
    echo "Formatting issues found. Run the following to fix them:"
    echo "  cd frontend && npm run format"
    exit 1
fi
