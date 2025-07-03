# CI Workflow Scripts

This directory contains comprehensive scripts for code quality, security scanning, and CI orchestration for the Warp Content Processor project.

## Overview

The scripts follow the user's development standards and provide automated tooling for:

1. **Code Quality**: Format, lint, and type-check code
2. **Security Scanning**: Comprehensive security analysis
3. **CI Orchestration**: Complete automated workflow

## Scripts

### Core Python Scripts

#### `quality_check.py`
Comprehensive code quality script that runs all formatting, linting, and style checking with safe automated fixes.

**Tools included:**
- `isort` - Import sorting
- `black` - Code formatting  
- `ruff` - Linting with auto-fixes
- `mypy` - Type checking
- `pylint` - Additional linting
- `trunk` - Orchestrated quality checks

**Usage:**
```bash
python scripts/quality_check.py
```

#### `security_scan.py`
Comprehensive security scanning script that runs all security tooling.

**Tools included:**
- `bandit` - Python security scanning
- `safety` - Dependency vulnerability scanning
- `trufflehog` - Secret detection
- `osv-scanner` - Vulnerability scanning
- `pip-audit` - Package vulnerability scanning

**Usage:**
```bash
python scripts/security_scan.py
```

**Output:** Creates timestamped reports in `security_reports/` directory.

#### `ci_workflow.py`
Orchestrates all tooling in a single clean workflow:

1. Project structure validation
2. Code quality checks and automated fixes
3. Security scanning
4. Regression tests
5. Full test suite with coverage

**Usage:**
```bash
python scripts/ci_workflow.py
```

**Output:** Creates comprehensive reports in `ci_reports/` directory.

### Wrapper Scripts

#### `run_ci.sh` (Linux/macOS)
Shell script wrapper for easy execution of CI workflows.

**Usage:**
```bash
# Run full CI workflow
./scripts/run_ci.sh

# Run only quality checks
./scripts/run_ci.sh quality

# Run only security scans
./scripts/run_ci.sh security

# Show help
./scripts/run_ci.sh help
```

#### `run_ci.bat` (Windows)
Windows batch file equivalent of the shell script.

**Usage:**
```cmd
REM Run full CI workflow
scripts\run_ci.bat

REM Run only quality checks
scripts\run_ci.bat quality

REM Run only security scans
scripts\run_ci.bat security

REM Show help
scripts\run_ci.bat help
```

## Development Standards

The scripts adhere to the following development standards:

### Code Quality Workflow
Following user's preferred order:
1. `isort` - Import sorting
2. `black` - Code formatting
3. `ruff` - Linting with fixes
4. `mypy` - Type checking
5. `pylint` - Additional linting
6. `trunk` - Orchestrated checks
7. `pytest` - Test suites

### Security Standards
- Comprehensive scanning with multiple tools
- Automated report generation
- Safe failure modes (warnings vs errors)
- Timestamped output for tracking

### Testing Standards
- Regression tests to ensure functionality preservation
- Parametrized tests avoiding conditionals
- Fixtures for clean test setup
- Coverage reporting

## Project Integration

### Pre-commit Hooks
The scripts integrate with the existing `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: quality-check
      name: Quality Check
      entry: python scripts/quality_check.py
      language: system
      pass_filenames: false
```

### Trunk Integration
Works with existing `.trunk/trunk.yaml` configuration for orchestrated quality checks.

### UV Package Management
Leverages UV for project and package management as per user standards:

```bash
# Install dependencies
uv sync

# Run in UV environment
uv run python scripts/ci_workflow.py
```

## Output Directories

### `security_reports/`
Contains timestamped security scan reports:
- `bandit_report_YYYYMMDD_HHMMSS.json`
- `safety_report_YYYYMMDD_HHMMSS.json`
- `trufflehog_report_YYYYMMDD_HHMMSS.json`
- `osv_report_YYYYMMDD_HHMMSS.json`
- `pip_audit_report_YYYYMMDD_HHMMSS.json`
- `security_summary_YYYYMMDD_HHMMSS.json`

### `ci_reports/`
Contains comprehensive CI workflow reports:
- `ci_report_YYYYMMDD_HHMMSS.json`
- `coverage_html/` - HTML coverage reports
- `coverage.xml` - XML coverage for CI systems
- `coverage.json` - JSON coverage data
- `test_results.xml` - JUnit test results

## Error Handling

### Quality Checks
- Fails fast on quality issues
- Provides detailed error messages
- Shows summary of all checks

### Security Scans
- Non-blocking for most security tools
- Critical scans (bandit, safety) can fail CI
- Comprehensive reporting regardless of status

### CI Workflow
- Validates project structure first
- Stops on critical failures
- Continues on warnings
- Provides comprehensive summary

## Best Practices

### Running Locally
```bash
# Quick quality check before committing
./scripts/run_ci.sh quality

# Full validation before pushing
./scripts/run_ci.sh ci
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Run CI Workflow
  run: python scripts/ci_workflow.py
```

### Docker Integration
```dockerfile
# Install dependencies
RUN uv sync

# Run CI workflow
RUN python scripts/ci_workflow.py
```

## Troubleshooting

### Common Issues

#### Tool Not Found
```bash
# Install missing tools
uv sync
```

#### Permission Denied (Linux/macOS)
```bash
# Make script executable
chmod +x scripts/run_ci.sh
```

#### Python Path Issues
```bash
# Ensure Python is in PATH
which python
python --version
```

### Debug Mode
Add `--verbose` or check individual tool outputs in the reports directories.

## Contributing

When modifying scripts:

1. Maintain the existing workflow order
2. Update documentation
3. Test on multiple platforms
4. Ensure error handling is robust
5. Follow the no-conditionals-in-tests rule for any test additions

## Dependencies

All dependencies are managed through:
- `pyproject.toml` - Core dependencies
- `requirements-dev.txt` - Development dependencies
- `uv.lock` - Locked dependency versions

The scripts automatically handle dependency checking and provide clear error messages for missing tools.
