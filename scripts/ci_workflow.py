#!/usr/bin/env python3
"""
Comprehensive CI workflow script for Warp Content Processor.

This script orchestrates all tooling in a single clean workflow:
1. Apply all safe fixes and reformatting (quality_check.py)
2. Run all security scans (security_scan.py)
3. Run all tests with coverage
4. Generate comprehensive reports

Follows user development standards: isort, black, ruff, mypy, trunk, then pytest
test suites.
Leverages UV for project and package management and venv management.

Usage:
    python scripts/ci_workflow.py [command] [options]

Commands:
    quality   - Run code quality checks and fixes
    security  - Run security scanning
    test      - Run test suite with coverage
    ci        - Run full CI workflow (default)

Options:
    --no-fix  - Skip automated fixes (quality checks only)
    --verbose - Show detailed output
    --help    - Show this help message
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class CIWorkflow:
    """Orchestrates the complete CI workflow."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize CI workflow with project root."""
        self.project_root = project_root or Path.cwd()
        self.scripts_dir = self.project_root / "scripts"
        self.reports_dir = self.project_root / "ci_reports"
        self.reports_dir.mkdir(exist_ok=True)
        self._no_fix_mode = False

    def run_command(self, cmd: List[str], description: str) -> Tuple[bool, str]:
        """Run a command and return success status and output."""
        print(f"\n🚀 {description}...")
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                print(f"✅ {description} completed successfully")
                return True, result.stdout

            print(f"❌ {description} failed:")
            print(result.stderr)
            print(result.stdout)  # Sometimes useful info is in stdout
            return False, result.stderr
        except FileNotFoundError as e:
            print(f"❌ {description} failed - command not found: {e}")
            return False, str(e)

    def run_quality_checks(self) -> bool:
        """Run comprehensive code quality checks and fixes."""
        quality_script = self.scripts_dir / "quality_check.py"
        cmd = [sys.executable, str(quality_script)]

        # Add --no-fix flag if in no-fix mode
        if self._no_fix_mode:
            cmd.append("--no-fix")

        success, _ = self.run_command(cmd, "Code quality checks and fixes")
        return success

    def run_security_scans(self) -> bool:
        """Run comprehensive security scanning."""
        security_script = self.scripts_dir / "security_scan.py"
        cmd = [sys.executable, str(security_script)]
        success, _ = self.run_command(cmd, "Security scanning")
        return success

    def run_tests_with_coverage(self) -> bool:
        """Run all tests with coverage reporting."""
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html:ci_reports/coverage_html",
            "--cov-report=xml:ci_reports/coverage.xml",
            "--cov-report=json:ci_reports/coverage.json",
            "--junit-xml=ci_reports/test_results.xml",
            "--tb=short",
            "-v",
        ]
        success, _ = self.run_command(cmd, "Test suite with coverage")
        return success

    def run_regression_tests(self) -> bool:
        """Run specific regression tests to ensure functionality is preserved."""
        # Run tests that cover core functionality
        critical_test_paths = [
            "tests/test_notebook_processor.py",
            "tests/test_content_processor.py",
            "tests/test_workflow_processor.py",
            "tests/processors/",
            "tests/excavation/",
        ]

        existing_paths = [
            path for path in critical_test_paths if (self.project_root / path).exists()
        ]

        if not existing_paths:
            print("⚠️ No critical test paths found, running all tests")
            return self.run_tests_with_coverage()

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--tb=short",
            "-v",
            "--timeout=300",  # 5 minute timeout per test
        ] + existing_paths

        success, _ = self.run_command(cmd, "Regression tests for core functionality")
        return success

    def validate_project_structure(self) -> bool:
        """Validate that essential project files and structure exist."""
        essential_files = [
            "pyproject.toml",
            "src/warp_content_processor/__init__.py",
            "tests/",
            ".trunk/trunk.yaml",
            ".pre-commit-config.yaml",
        ]

        missing_files = []
        for file_path in essential_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)

        if missing_files:
            print(f"❌ Missing essential project files: {', '.join(missing_files)}")
            return False

        print("✅ Project structure validation passed")
        return True

    def generate_ci_report(self, results: Dict[str, bool]) -> None:
        """Generate comprehensive CI report."""
        import json  # pylint: disable=import-outside-toplevel
        from datetime import datetime  # pylint: disable=import-outside-toplevel

        report = {
            "ci_run_timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "workflow_results": results,
            "total_steps": len(results),
            "successful_steps": sum(results.values()),
            "success_rate": sum(results.values()) / len(results) * 100,
            "overall_success": all(results.values()),
        }

        report_file = (
            self.reports_dir / f"ci_report_{datetime.now():%Y%m%d_%H%M%S}.json"
        )
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print(f"📄 CI report saved to: {report_file}")

    def run_full_workflow(self) -> Dict[str, bool]:
        """Run the complete CI workflow."""
        results = {}

        print("🔄 Starting Comprehensive CI Workflow")
        print("=" * 60)
        print(f"📁 Project root: {self.project_root}")
        print(f"📊 Reports directory: {self.reports_dir}")

        # Step 1: Validate project structure
        results["project_validation"] = self.validate_project_structure()

        # Step 2: Code quality checks and automated fixes
        # This includes: isort, black, ruff, mypy, pylint, trunk
        results["quality_checks"] = self.run_quality_checks()

        # Step 3: Security scanning
        # This includes: bandit, safety, trufflehog, osv-scanner, pip-audit
        results["security_scans"] = self.run_security_scans()

        # Step 4: Regression tests (ensure functionality is preserved)
        results["regression_tests"] = self.run_regression_tests()

        # Step 5: Full test suite with coverage
        results["full_test_suite"] = self.run_tests_with_coverage()

        return results

    def print_workflow_summary(self, results: Dict[str, bool]) -> None:
        """Print comprehensive workflow summary."""
        print("\n" + "=" * 60)
        print("🎯 CI WORKFLOW SUMMARY")
        print("=" * 60)

        step_descriptions = {
            "project_validation": "Project Structure Validation",
            "quality_checks": "Code Quality Checks & Fixes",
            "security_scans": "Security Scanning",
            "regression_tests": "Regression Tests",
            "full_test_suite": "Full Test Suite with Coverage",
        }

        for step, success in results.items():
            description = step_descriptions.get(step, step.replace("_", " ").title())
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{description.ljust(35)}: {status}")

        total_steps = len(results)
        passed_steps = sum(results.values())
        print(f"\nOverall Result: {passed_steps}/{total_steps} steps passed")

        if all(results.values()):
            print("🎉 All CI workflow steps completed successfully!")
            print("📦 Your code is ready for deployment!")
        else:
            failed_steps = [step for step, success in results.items() if not success]
            print(f"⚠️ Failed steps: {', '.join(failed_steps)}")
            print("🔧 Please review the output above and fix any issues.")

        print(f"\n📁 Detailed reports available in: {self.reports_dir}")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="CI Workflow Management")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["quality", "security", "test", "ci"],
        default="ci",
        help="Command to execute: quality, security, test, ci (default: ci)",
    )
    parser.add_argument(
        "--no-fix",
        action="store_true",
        help="Skip automated fixes (only for quality checks)",
    )
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")

    return parser.parse_args()


def main() -> None:
    """Main entry point for CI workflow."""
    args = parse_arguments()
    workflow = CIWorkflow()

    if args.verbose:
        print("Verbose mode enabled")

    command_mapping = {
        "quality": workflow.run_quality_checks,
        "security": workflow.run_security_scans,
        "test": workflow.run_tests_with_coverage,
        "ci": workflow.run_full_workflow,
    }

    if args.no_fix and args.command == "quality":
        print("Skipping fixes in quality checks")
        workflow._no_fix_mode = True

    # Execute selected command
    results = command_mapping[args.command]()

    if args.command == "ci":
        # Type guard to ensure results is Dict[str, bool]
        if isinstance(results, dict):
            workflow.print_workflow_summary(results)
            workflow.generate_ci_report(results)

            # Exit with error code if any steps failed
            if not all(results.values()):
                sys.exit(1)
        else:
            print("CI workflow completed with unknown result type")
            sys.exit(1)


if __name__ == "__main__":
    main()
