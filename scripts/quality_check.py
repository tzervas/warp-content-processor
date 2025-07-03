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
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class QualityChecker:
    """Orchestrates code quality checks and fixes."""

    def __init__(self, project_root: Path = None):
        """Initialize quality checker with project root."""
        self.project_root = project_root or Path.cwd()
        self.src_path = self.project_root / "src"
        self.tests_path = self.project_root / "tests"
        self.python_paths = [str(self.src_path), str(self.tests_path)]

    def run_command(self, cmd: List[str], description: str) -> Tuple[bool, str]:
        """Run a command and return success status and output."""
        print(f"\n🔧 {description}...")
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
            else:
                print(f"❌ {description} failed:")
                print(result.stderr)
                return False, result.stderr
        except FileNotFoundError as e:
            print(f"❌ {description} failed - tool not found: {e}")
            return False, str(e)

    def run_isort(self) -> bool:
        """Run isort to sort imports."""
        cmd = ["python", "-m", "isort", "--profile", "black"] + self.python_paths
        success, _ = self.run_command(cmd, "Import sorting with isort")
        return success

    def run_black(self) -> bool:
        """Run black to format code."""
        cmd = ["python", "-m", "black", "--line-length", "88"] + self.python_paths
        success, _ = self.run_command(cmd, "Code formatting with black")
        return success

    def run_ruff_fix(self) -> bool:
        """Run ruff with auto-fixes."""
        cmd = ["python", "-m", "ruff", "check", "--fix"] + self.python_paths
        success, _ = self.run_command(cmd, "Linting with ruff (auto-fix)")
        return success

    def run_ruff_check(self) -> bool:
        """Run ruff for final linting check."""
        cmd = ["python", "-m", "ruff", "check"] + self.python_paths
        success, _ = self.run_command(cmd, "Final ruff linting check")
        return success

    def run_mypy(self) -> bool:
        """Run mypy for type checking."""
        cmd = ["python", "-m", "mypy"] + self.python_paths
        success, _ = self.run_command(cmd, "Type checking with mypy")
        return success

    def run_pylint(self) -> bool:
        """Run pylint for additional linting."""
        cmd = ["python", "-m", "pylint"] + self.python_paths
        success, _ = self.run_command(cmd, "Additional linting with pylint")
        return success

    def run_trunk_check(self) -> bool:
        """Run trunk for orchestrated quality checks."""
        cmd = ["trunk", "check", "--fix", "--all"]
        success, _ = self.run_command(cmd, "Trunk orchestrated quality checks")
        return success

    def run_all_checks(self) -> Dict[str, bool]:
        """Run all quality checks in the correct order."""
        results = {}

        print("🚀 Starting comprehensive code quality checks...")
        print(f"📁 Project root: {self.project_root}")
        print(f"🐍 Python paths: {', '.join(self.python_paths)}")

        # Step 1: Import sorting (must come first)
        results["isort"] = self.run_isort()

        # Step 2: Code formatting (must come after isort)
        results["black"] = self.run_black()

        # Step 3: Linting with auto-fixes
        results["ruff_fix"] = self.run_ruff_fix()

        # Step 4: Type checking
        results["mypy"] = self.run_mypy()

        # Step 5: Additional linting
        results["pylint"] = self.run_pylint()

        # Step 6: Final ruff check (no fixes)
        results["ruff_check"] = self.run_ruff_check()

        # Step 7: Trunk orchestrated checks
        results["trunk"] = self.run_trunk_check()

        return results

    def print_summary(self, results: Dict[str, bool]) -> None:
        """Print summary of all quality check results."""
        print("\n" + "=" * 60)
        print("📊 QUALITY CHECK SUMMARY")
        print("=" * 60)

        for check, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{check.ljust(15)}: {status}")

        total_checks = len(results)
        passed_checks = sum(results.values())
        print(f"\nOverall: {passed_checks}/{total_checks} checks passed")

        if passed_checks == total_checks:
            print("🎉 All quality checks passed!")
        else:
            print("⚠️  Some quality checks failed. Please review the output above.")


def main():
    """Main entry point for quality checking."""
    checker = QualityChecker()
    results = checker.run_all_checks()
    checker.print_summary(results)

    # Exit with error code if any checks failed
    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
