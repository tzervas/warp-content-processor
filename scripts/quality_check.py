#!/usr/bin/env python3
"""
Comprehensive code quality script for Warp Content Processor.

This script runs all formatting, linting, and style checking tools
with safe automated fixes according to user development standards:
- isort for import sorting
- black for code formatting
- ruff for linting with auto-fixes
- mypy for type checking
- pylint for additional linting
- trunk for orchestrated quality checks

Adheres to PEP8, DRY, SRP, and KISS principles.

Usage:
    python scripts/quality_check.py [options]

Options:
    --no-fix   - Run checks without applying fixes
    --verbose  - Show detailed output
    --help     - Show this help message
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class QualityChecker:
    """Orchestrates code quality checks and fixes."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize quality checker with project root."""
        self.project_root = project_root or Path.cwd()
        self.src_path = self.project_root / "src"
        self.tests_path = self.project_root / "tests"
        self.python_paths = [str(self.src_path), str(self.tests_path)]
        self.use_uv = self._detect_uv()

    def _detect_uv(self) -> bool:
        """Detect if UV package manager is available."""
        try:
            result = subprocess.run(
                ["uv", "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                print(f"Detected UV package manager: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass

        print("Using standard Python package management")
        return False

    def run_command(self, cmd: List[str], description: str) -> Tuple[bool, str]:
        """Run a command and return success status and output."""
        try:
            print(f"\n🔧 {description}...")
        except UnicodeEncodeError:
            print(f"\n{description}...")
        try:
            # Use UV if available for running Python tools
            if self.use_uv and cmd[0] == sys.executable and cmd[1] == "-m":
                uv_cmd = ["uv", "run"] + cmd[2:]
                cmd = uv_cmd

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                try:
                    print(f"✅ {description} completed successfully")
                except UnicodeEncodeError:
                    print(f"{description} completed successfully")
                return True, result.stdout

            try:
                print(f"❌ {description} failed:")
            except UnicodeEncodeError:
                print(f"{description} failed:")
            print(result.stderr)
            return False, result.stderr
        except FileNotFoundError as e:
            try:
                print(f"❌ {description} failed - tool not found: {e}")
            except UnicodeEncodeError:
                print(f"{description} failed - tool not found: {e}")
            return False, str(e)

    def run_isort(self) -> bool:
        """Run isort to sort imports."""
        cmd = [sys.executable, "-m", "isort", "--profile", "black"] + self.python_paths
        success, _ = self.run_command(cmd, "Import sorting with isort")
        return success

    def run_black(self) -> bool:
        """Run black to format code."""
        cmd = [sys.executable, "-m", "black", "--line-length", "88"] + self.python_paths
        success, _ = self.run_command(cmd, "Code formatting with black")
        return success

    def run_ruff_fix(self) -> bool:
        """Run ruff with auto-fixes."""
        cmd = [sys.executable, "-m", "ruff", "check", "--fix"] + self.python_paths
        success, _ = self.run_command(cmd, "Linting with ruff (auto-fix)")
        return success

    def run_ruff_check(self) -> bool:
        """Run ruff for final linting check."""
        cmd = [sys.executable, "-m", "ruff", "check"] + self.python_paths
        success, _ = self.run_command(cmd, "Final ruff linting check")
        return success

    def run_mypy(self) -> bool:
        """Run mypy for type checking."""
        cmd = [sys.executable, "-m", "mypy"] + self.python_paths
        success, _ = self.run_command(cmd, "Type checking with mypy")
        return success

    def run_pylint(self) -> bool:
        """Run pylint for additional linting."""
        cmd = [sys.executable, "-m", "pylint"] + self.python_paths
        success, _ = self.run_command(cmd, "Additional linting with pylint")
        return success

    def run_trunk_check(self) -> bool:
        """Run trunk for orchestrated quality checks."""
        cmd = ["trunk", "check", "--fix", "--all"]
        success, _ = self.run_command(cmd, "Trunk orchestrated quality checks")
        return success

    def run_isort_check(self) -> bool:
        """Run isort to check import sorting without fixing."""
        cmd = [
            sys.executable,
            "-m",
            "isort",
            "--profile",
            "black",
            "--check-only",
            "--diff",
        ] + self.python_paths
        success, _ = self.run_command(cmd, "Import sorting check with isort")
        return success

    def run_black_check(self) -> bool:
        """Run black to check code formatting without fixing."""
        cmd = [
            sys.executable,
            "-m",
            "black",
            "--line-length",
            "88",
            "--check",
            "--diff",
        ] + self.python_paths
        success, _ = self.run_command(cmd, "Code formatting check with black")
        return success

    def run_trunk_check_only(self) -> bool:
        """Run trunk checks without applying fixes."""
        cmd = ["trunk", "check", "--all"]
        success, _ = self.run_command(cmd, "Trunk orchestrated checks (no fixes)")
        return success

    def run_all_checks(self, apply_fixes: bool = True) -> Dict[str, bool]:
        """Run all quality checks in the correct order."""
        results = {}

        print(
            "🚀 Starting comprehensive code quality checks..."
            if sys.platform != "win32"
            else "Starting comprehensive code quality checks..."
        )
        print(f"Project root: {self.project_root}")
        print(f"Python paths: {', '.join(self.python_paths)}")
        print(f"Apply fixes: {'Yes' if apply_fixes else 'No'}")

        if apply_fixes:
            # Step 1: Import sorting (must come first)
            results["isort"] = self.run_isort()

            # Step 2: Code formatting (must come after isort)
            results["black"] = self.run_black()

            # Step 3: Linting with auto-fixes
            results["ruff_fix"] = self.run_ruff_fix()
        else:
            # Check-only versions without applying fixes
            results["isort_check"] = self.run_isort_check()
            results["black_check"] = self.run_black_check()

        # Step 4: Type checking
        results["mypy"] = self.run_mypy()

        # Step 5: Additional linting
        results["pylint"] = self.run_pylint()

        # Step 6: Final ruff check (no fixes)
        results["ruff_check"] = self.run_ruff_check()

        # Step 7: Trunk orchestrated checks
        if apply_fixes:
            results["trunk"] = self.run_trunk_check()
        else:
            results["trunk_check"] = self.run_trunk_check_only()

        return results

    def print_summary(self, results: Dict[str, bool]) -> None:
        """Print summary of all quality check results."""
        print("\n" + "=" * 60)
        print("QUALITY CHECK SUMMARY")
        print("=" * 60)

        for check, success in results.items():
            status = "PASS" if success else "FAIL"
            print(f"{check.ljust(15)}: {status}")

        total_checks = len(results)
        passed_checks = sum(results.values())
        print(f"\nOverall: {passed_checks}/{total_checks} checks passed")

        if passed_checks == total_checks:
            print("All quality checks passed!")
        else:
            print("Some quality checks failed. Please review the output above.")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Code Quality Checker")
    parser.add_argument(
        "--no-fix", action="store_true", help="Run checks without applying fixes"
    )
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")

    return parser.parse_args()


def main() -> None:
    """Main entry point for quality checking."""
    args = parse_arguments()
    checker = QualityChecker()

    # Run checks with or without fixes based on arguments
    apply_fixes = not args.no_fix
    results = checker.run_all_checks(apply_fixes=apply_fixes)
    checker.print_summary(results)

    # Exit with error code if any checks failed
    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
