#!/bin/bash
# Linting script for DMOJ using Ruff
# Usage: ./scripts/lint.sh [fix]

set -e

echo "Running Ruff linter..."

if [[ "$1" == "fix" ]]; then
    echo "Applying automatic fixes..."
    uv run ruff check --config pyproject.toml . --fix
    echo "Formatting code..."
    uv run ruff format --config pyproject.toml .
    echo "Done! Applied fixes and formatted code."
else
    echo "Checking code style and quality..."
    uv run ruff check --config pyproject.toml .
    echo ""
    echo "Checking code formatting..."
    uv run ruff format --check --config pyproject.toml .
    echo ""
    echo "To apply automatic fixes, run: ./scripts/lint.sh fix"
fi
