#!/bin/bash
#
# Comprehensive CI Workflow Runner for Warp Content Processor
#
# This script provides easy access to all our quality and security tooling.
# Usage: ./scripts/run_ci.sh [command]
#
# Commands:
#   quality  - Run code quality checks and fixes
#   security - Run security scanning
#   ci       - Run full CI workflow
#   help     - Show this help message
#

set -e # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
	echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
	echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
	echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
	echo -e "${RED}❌ $1${NC}"
}

# Function to check if Python is available
check_python() {
	if ! command -v python &>/dev/null; then
		print_error "Python is not installed or not in PATH"
		exit 1
	fi
}

# Function to show help
show_help() {
	echo "Warp Content Processor CI Workflow Runner"
	echo ""
	echo "Usage: ./scripts/run_ci.sh [command]"
	echo ""
	echo "Commands:"
	echo "  quality   - Run code quality checks and automated fixes"
	echo "            - Includes: isort, black, ruff, mypy, pylint, trunk"
	echo ""
	echo "  security  - Run comprehensive security scanning"
	echo "            - Includes: bandit, safety, trufflehog, osv-scanner, pip-audit"
	echo ""
	echo "  ci        - Run complete CI workflow"
	echo "            - Includes: quality checks + security scans + tests"
	echo ""
	echo "  help      - Show this help message"
	echo ""
	echo "Examples:"
	echo "  ./scripts/run_ci.sh quality    # Run only quality checks"
	echo "  ./scripts/run_ci.sh security   # Run only security scans"
	echo "  ./scripts/run_ci.sh ci         # Run full CI pipeline"
}

# Function to run quality checks
run_quality() {
	print_info "Starting code quality checks and automated fixes..."
	cd "$PROJECT_ROOT"
	python scripts/quality_check.py

	if [ $? -eq 0 ]; then
		print_success "Code quality checks completed successfully!"
	else
		print_error "Code quality checks failed. Please review the output above."
		exit 1
	fi
}

# Function to run security scans
run_security() {
	print_info "Starting comprehensive security scanning..."
	cd "$PROJECT_ROOT"
	python scripts/security_scan.py

	if [ $? -eq 0 ]; then
		print_success "Security scanning completed successfully!"
	else
		print_warning "Some security scans failed. Please review the output above."
		# Don't exit on security scan failures - they might be warnings
	fi
}

# Function to run full CI workflow
run_ci() {
	print_info "Starting comprehensive CI workflow..."
	cd "$PROJECT_ROOT"
	python scripts/ci_workflow.py

	if [ $? -eq 0 ]; then
		print_success "Full CI workflow completed successfully!"
		print_success "🎉 Your code is ready for deployment!"
	else
		print_error "CI workflow failed. Please review the output above."
		exit 1
	fi
}

# Main script logic
main() {
	check_python

	case "${1:-ci}" in
	"quality")
		run_quality
		;;
	"security")
		run_security
		;;
	"ci")
		run_ci
		;;
	"help" | "-h" | "--help")
		show_help
		;;
	*)
		print_error "Unknown command: $1"
		echo ""
		show_help
		exit 1
		;;
	esac
}

# Run main function with all arguments
main "$@"
