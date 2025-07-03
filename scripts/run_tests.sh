#!/bin/bash
set -e

# Parse command line arguments
FAIL_FAST=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --fail-fast)
            FAIL_FAST="-x"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--fail-fast]"
            exit 1
            ;;
    esac
done

# Function to run a command and check its exit status
run_step() {
    local step_name=$1
    shift
    echo "Running ${step_name}..."
    if ! "$@"; then
        echo "${step_name} failed!"
        if [[ -n "$FAIL_FAST" ]]; then
            exit 1
        fi
        return 1
    fi
}

# Run each step
run_step "black" black src/warp_content_processor tests
run_step "isort" isort src/warp_content_processor tests

# Pylint is allowed to fail, but should still respect fail-fast
if ! run_step "pylint" pylint src/warp_content_processor tests; then
    [[ -n "$FAIL_FAST" ]] && exit 1
fi

# Run pytest with coverage and optional fail-fast
echo "Running pytest with coverage..."
python -m pytest tests/ -v --cov=src/warp_content_processor $FAIL_FAST
