#!/bin/bash
set -e

echo "Running black..."
black src/warp_content_processor tests

echo "Running isort..."
isort src/warp_content_processor tests

echo "Running pylint..."
pylint src/warp_content_processor tests || true

echo "Running pytest with coverage..."
python -m pytest tests/ -v --cov=src/warp_content_processor
