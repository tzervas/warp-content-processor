#!/bin/bash

# Exit on any error
set -e

echo "🚀 Setting up Warp Content Processor development environment..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# Install additional system dependencies
echo "🔧 Installing system dependencies..."
sudo apt-get install -y \
    build-essential \
    curl \
    git \
    jq \
    wget \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Install UV (Python package manager)
echo "🐍 Installing UV (Python package manager)..."
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Create and activate virtual environment using UV
echo "🌍 Setting up Python virtual environment..."
uv venv .venv --python 3.11
source .venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    uv pip install -r requirements.txt
fi

# Install development dependencies
echo "🛠️ Installing development dependencies..."
if [ -f "requirements-dev.txt" ]; then
    uv pip install -r requirements-dev.txt
else
    # Fallback to individual packages if requirements-dev.txt doesn't exist
    uv pip install \
        black \
        isort \
        ruff \
        mypy \
        pylint \
        bandit \
        pytest \
        pytest-cov \
        pytest-xdist \
        pre-commit \
        safety \
        pipdeptree
fi

# Initialize Trunk if not already done
echo "🌳 Initializing Trunk..."
if [ ! -f ".trunk/trunk.yaml" ]; then
    trunk init
fi

# Set up pre-commit hooks
echo "🪝 Setting up pre-commit hooks..."
pre-commit install

# Create development scripts directory
echo "📂 Creating development scripts..."
mkdir -p scripts

# Create code quality check script
cat > scripts/check-quality.sh << 'EOF'
#!/bin/bash

# Exit on any error
set -e

echo "🔍 Running code quality checks..."

echo "📊 Running isort..."
uv run isort --check-only --diff .

echo "🖤 Running Black..."
uv run black --check --diff .

echo "⚡ Running Ruff..."
uv run ruff check .

echo "🔬 Running MyPy..."
uv run mypy src/warp_content_processor --ignore-missing-imports

echo "🌳 Running Trunk..."
trunk check --all

echo "✅ All code quality checks passed!"
EOF

# Create security check script
cat > scripts/check-security.sh << 'EOF'
#!/bin/bash

# Exit on any error
set -e

echo "🔒 Running security checks..."

echo "🛡️ Running Bandit..."
uv run bandit -r src/warp_content_processor --skip B101,B601 -f json -o security_report.json
uv run bandit -r src/warp_content_processor --skip B101,B601

echo "🔐 Running Safety..."
uv run safety check

echo "✅ All security checks passed!"
EOF

# Create test script
cat > scripts/run-tests.sh << 'EOF'
#!/bin/bash

# Exit on any error
set -e

echo "🧪 Running tests..."

echo "🔬 Running pytest with coverage..."
uv run pytest tests/ --cov=src/warp_content_processor --cov-report=html --cov-report=term-missing -v

echo "✅ All tests passed!"
EOF

# Create fix script
cat > scripts/fix-code.sh << 'EOF'
#!/bin/bash

echo "🔧 Fixing code issues..."

echo "📊 Running isort..."
uv run isort .

echo "🖤 Running Black..."
uv run black .

echo "⚡ Running Ruff with auto-fix..."
uv run ruff check --fix .

echo "🌳 Running Trunk format..."
trunk fmt

echo "✅ Code fixed!"
EOF

# Create complete workflow script
cat > scripts/ci-workflow.sh << 'EOF'
#!/bin/bash

# Exit on any error
set -e

echo "🚀 Running complete CI workflow..."

# Fix code first
echo "🔧 Step 1: Fix code formatting..."
bash scripts/fix-code.sh

# Run tests
echo "🧪 Step 2: Run tests..."
bash scripts/run-tests.sh

# Run quality checks
echo "🔍 Step 3: Run quality checks..."
bash scripts/check-quality.sh

# Run security checks
echo "🔒 Step 4: Run security checks..."
bash scripts/check-security.sh

echo "✅ Complete CI workflow passed!"
EOF

# Make scripts executable
chmod +x scripts/*.sh

# Create .env file template
cat > .env.template << 'EOF'
# Environment variables for development
PYTHONPATH=src
PYTEST_CURRENT_TEST=true
COVERAGE_CORE=sysmon
EOF

# Copy template to .env if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.template .env
fi

# Configure git if not already configured
echo "📝 Configuring git..."
if [ -z "$(git config --global user.email)" ]; then
    echo "⚠️  Please configure git with your email: git config --global user.email 'your-email@example.com'"
fi
if [ -z "$(git config --global user.name)" ]; then
    echo "⚠️  Please configure git with your name: git config --global user.name 'Your Name'"
fi

# Set up shell aliases for convenience
echo "📚 Setting up development aliases..."
cat >> ~/.bashrc << 'EOF'

# Warp Content Processor development aliases (legacy)
alias wcp-test='bash scripts/run-tests.sh'
alias wcp-check='bash scripts/check-quality.sh'
alias wcp-fix='bash scripts/fix-code.sh'
alias wcp-security='bash scripts/check-security.sh'
alias wcp-ci='bash scripts/ci-workflow.sh'
alias wcp-activate='source .venv/bin/activate'

# New unified CI script aliases
alias wcp='./scripts/wcp'
alias wcp-quality='./scripts/wcp quality'
alias wcp-quality-check='./scripts/wcp quality --no-fix'
alias wcp-sec='./scripts/wcp security'
alias wcp-tests='./scripts/wcp test'
alias wcp-full='./scripts/wcp ci'
EOF

echo "✅ Development environment setup complete!"
echo ""
echo "🎯 Available commands:"
echo "  wcp-test      - Run tests"
echo "  wcp-check     - Run quality checks"
echo "  wcp-fix       - Fix code formatting"
echo "  wcp-security  - Run security checks"
echo "  wcp-ci        - Run complete CI workflow"
echo "  wcp-activate  - Activate virtual environment"
echo ""
echo "📂 Scripts available in scripts/ directory:"
echo "  check-quality.sh  - Code quality checks"
echo "  check-security.sh - Security analysis"
echo "  run-tests.sh      - Test execution"
echo "  fix-code.sh       - Auto-fix code issues"
echo "  ci-workflow.sh    - Complete CI pipeline"
echo ""
echo "🔄 Reload your shell or run: source ~/.bashrc"
echo "🚀 Happy coding!"
