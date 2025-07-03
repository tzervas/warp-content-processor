# Warp Content Processor Development Container

This development container provides a complete, reproducible development environment for the Warp Content Processor with all necessary tools for code quality and security scanning.

## 🚀 Quick Start

### Prerequisites

- Docker Desktop installed and running
- VS Code with the "Dev Containers" extension

### Launch Development Environment

1. **Open in VS Code**: Open this project in VS Code
2. **Reopen in Container**: When prompted, click "Reopen in Container" or use:
   - Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
   - Search for "Dev Containers: Reopen in Container"
3. **Wait for Setup**: The container will build and run the setup script automatically

## 🛠️ What's Included

### Development Tools

- **Python 3.11** with UV package manager
- **Code Formatters**: Black, isort
- **Linters**: Ruff, Pylint, MyPy
- **Security Tools**: Bandit, Safety, TruffleHog
- **Testing**: pytest with coverage
- **Quality Control**: Trunk, pre-commit hooks

### VS Code Extensions

- Python development suite (Pylance, formatters, linters)
- Trunk.io for comprehensive code quality
- GitLens for enhanced Git integration
- YAML and TOML support
- Spell checker

### Scripts Available

After setup, you'll have these convenient commands:

```bash
# Quick aliases (reload shell first: source ~/.bashrc)
wcp-test      # Run all tests with coverage
wcp-check     # Run all code quality checks
wcp-fix       # Auto-fix code formatting issues
wcp-security  # Run security scans
wcp-ci        # Complete CI workflow
wcp-activate  # Activate Python virtual environment

# Direct scripts
./scripts/run-tests.sh      # Test execution with coverage
./scripts/check-quality.sh  # Code quality analysis
./scripts/check-security.sh # Security vulnerability scanning
./scripts/fix-code.sh       # Auto-fix formatting and lint issues
./scripts/ci-workflow.sh    # Complete CI pipeline simulation
```

## 📋 Development Workflow

Following your preferred workflow order:

### 1. Code Quality Fixes

```bash
# Auto-fix issues
wcp-fix
# or
./scripts/fix-code.sh
```

This runs:
- `isort` - Import sorting
- `black` - Code formatting
- `ruff --fix` - Linting with auto-fixes
- `trunk fmt` - Additional formatting

### 2. Code Quality Checks

```bash
# Check code quality
wcp-check
# or
./scripts/check-quality.sh
```

This runs:
- `isort --check-only --diff`
- `black --check --diff` 
- `ruff check`
- `mypy` type checking
- `trunk check --all`

### 3. Security Analysis

```bash
# Security scanning
wcp-security
# or
./scripts/check-security.sh
```

This runs:
- `bandit` - Python security linter
- `safety` - Dependency vulnerability scanner

### 4. Testing

```bash
# Run tests with coverage
wcp-test
# or
./scripts/run-tests.sh
```

This runs:
- `pytest` with coverage reporting
- HTML coverage report in `htmlcov/`

### 5. Complete CI Simulation

```bash
# Run the complete workflow
wcp-ci
# or
./scripts/ci-workflow.sh
```

This runs all steps in sequence: fix → test → quality → security

## 🔧 Configuration

### Python Environment

- **Virtual Environment**: `.venv` (automatically activated)
- **Package Manager**: UV (faster pip replacement)
- **Python Version**: 3.11
- **Dependencies**: Installed from `requirements.txt`

### Code Quality Standards

- **Line Length**: 88 characters (Black standard)
- **Import Style**: Black-compatible (isort profile)
- **Type Checking**: Strict mode with MyPy
- **Security**: Bandit with common test exclusions

### Pre-commit Hooks

Pre-commit hooks are automatically installed and will run:
- Code formatting (isort, black)
- Linting (ruff)
- Type checking (mypy)
- Security scanning (bandit)
- General quality checks

## 🐛 Troubleshooting

### Container Build Issues

If the container fails to build:

1. **Check Docker**: Ensure Docker Desktop is running
2. **Rebuild Container**: 
   - Command Palette → "Dev Containers: Rebuild Container"
3. **Clean Build**: 
   - Command Palette → "Dev Containers: Rebuild Container Without Cache"

### Permission Issues

If you encounter permission issues:

```bash
# Fix ownership in container
sudo chown -R vscode:vscode /workspaces/warp-content-processor
```

### Missing Tools

If tools seem missing after setup:

```bash
# Re-run setup script
bash .devcontainer/setup.sh

# Reload shell
source ~/.bashrc
```

### Python Environment Issues

```bash
# Recreate virtual environment
rm -rf .venv
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt
```

## 📁 Directory Structure

```
.devcontainer/
├── devcontainer.json    # Container configuration
├── setup.sh            # Environment setup script
└── README.md           # This file

scripts/
├── check-quality.sh    # Code quality checks
├── check-security.sh   # Security analysis
├── run-tests.sh        # Test execution
├── fix-code.sh         # Auto-fix issues
└── ci-workflow.sh      # Complete CI pipeline

.trunk/
└── trunk.yaml          # Trunk configuration

.pre-commit-config.yaml # Pre-commit hooks configuration
```

## 🔗 Useful Links

- [Trunk.io Documentation](https://docs.trunk.io/)
- [UV Package Manager](https://github.com/astral-sh/uv)
- [Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)
- [Pre-commit](https://pre-commit.com/)

## 💡 Tips

1. **First Time Setup**: The initial container build may take 5-10 minutes
2. **Aliases**: Reload your shell (`source ~/.bashrc`) to use the `wcp-*` aliases
3. **VS Code**: Extensions will auto-configure with optimal settings
4. **Git**: Remember to configure your git user info after first setup
5. **Testing**: Use `wcp-test` frequently during development
6. **CI Simulation**: Run `wcp-ci` before pushing to ensure everything passes

Happy coding! 🚀
