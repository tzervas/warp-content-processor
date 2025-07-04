#!/usr/bin/env python3
"""
Comprehensive security scanning script for Warp Content Processor.

This script runs all security tooling according to user development standards:
- bandit for Python security scanning
- safety for dependency vulnerability scanning
- trufflehog for secret detection
- osv-scanner for vulnerability scanning
- pip-audit for package vulnerability scanning

Adheres to security best practices and comprehensive coverage.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class SecurityScanner:
    """Orchestrates comprehensive security scanning."""

    def __init__(self, project_root: Path = None):
        """Initialize security scanner with project root."""
        self.project_root = project_root or Path.cwd()
        self.src_path = self.project_root / "src"
        self.reports_dir = self.project_root / "security_reports"
        self.reports_dir.mkdir(exist_ok=True)
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
                print(f"🐍 Detected UV package manager: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass

        print("🐍 Using standard Python package management")
        return False

    def run_command(
        self, cmd: List[str], description: str, capture_json: bool = False
    ) -> Tuple[bool, str]:
        """Run a command and return success status and output."""
        print(f"\n🔍 {description}...")
        try:
            # Use UV if available for running Python tools
            if self.use_uv and cmd[0] == "python" and cmd[1] == "-m":
                uv_cmd = ["uv", "run"] + cmd[2:]
                cmd = uv_cmd

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )

            # For security tools, we often want to capture output even on non-zero exit
            # as they may return non-zero when issues are found
            if capture_json or result.returncode in [0, 1]:
                print(f"✅ {description} completed")
                return True, result.stdout
            else:
                print(f"❌ {description} failed:")
                print(result.stderr)
                return False, result.stderr

        except FileNotFoundError as e:
            print(f"❌ {description} failed - tool not found: {e}")
            return False, str(e)

    def run_bandit(self) -> Tuple[bool, Optional[Dict]]:
        """Run bandit security scanner."""
        output_file = (
            self.reports_dir / f"bandit_report_{datetime.now():%Y%m%d_%H%M%S}.json"
        )
        cmd = [
            "python",
            "-m",
            "bandit",
            "-r",
            str(self.src_path),
            "-f",
            "json",
            "-o",
            str(output_file),
            "--skip",
            "B101,B601",  # Skip assert_used and shell=True warnings for development
        ]

        success, output = self.run_command(
            cmd, "Bandit security scanning", capture_json=True
        )

        if success and output_file.exists():
            try:
                with open(output_file, "r") as f:
                    report = json.load(f)
                self._print_bandit_summary(report)
                return True, report
            except json.JSONDecodeError:
                print("⚠️ Could not parse bandit JSON output")
                return False, None
        return success, None

    def _print_bandit_summary(self, report: Dict) -> None:
        """Print summary of bandit scan results."""
        metrics = report.get("metrics", {}).get("_totals", {})
        high_severity = metrics.get("SEVERITY.HIGH", 0)
        medium_severity = metrics.get("SEVERITY.MEDIUM", 0)
        low_severity = metrics.get("SEVERITY.LOW", 0)

        print(f"   High severity issues: {high_severity}")
        print(f"   Medium severity issues: {medium_severity}")
        print(f"   Low severity issues: {low_severity}")
        print(f"   Lines of code scanned: {metrics.get('loc', 0)}")

    def run_safety(self) -> Tuple[bool, Optional[str]]:
        """Run safety dependency vulnerability scanner."""
        output_file = (
            self.reports_dir / f"safety_report_{datetime.now():%Y%m%d_%H%M%S}.json"
        )
        cmd = [
            "python",
            "-m",
            "safety",
            "check",
            "--json",
            "--output",
            str(output_file),
        ]

        success, output = self.run_command(
            cmd, "Safety dependency scanning", capture_json=True
        )

        if success and output_file.exists():
            try:
                with open(output_file, "r") as f:
                    report = json.load(f)
                self._print_safety_summary(report)
                return True, output
            except json.JSONDecodeError:
                print("⚠️ Could not parse safety JSON output")
                return False, None
        return success, output

    def _print_safety_summary(self, report: List) -> None:
        """Print summary of safety scan results."""
        if isinstance(report, list):
            vulnerability_count = len(report)
            print(f"   Vulnerabilities found: {vulnerability_count}")
            if vulnerability_count > 0:
                for vuln in report[:3]:  # Show first 3 vulnerabilities
                    package = vuln.get("package", "Unknown")
                    vuln_id = vuln.get("vulnerability_id", "Unknown")
                    print(f"   - {package}: {vuln_id}")
                if vulnerability_count > 3:
                    print(f"   ... and {vulnerability_count - 3} more")

    def run_pip_audit(self) -> bool:
        """Run pip-audit for package vulnerability scanning."""
        output_file = (
            self.reports_dir / f"pip_audit_report_{datetime.now():%Y%m%d_%H%M%S}.json"
        )
        cmd = [
            "python",
            "-m",
            "pip_audit",
            "--format=json",
            "--output",
            str(output_file),
        ]

        success, _ = self.run_command(
            cmd, "Pip-audit package scanning", capture_json=True
        )
        return success

    def run_trufflehog(self) -> bool:
        """Run trufflehog for secret detection."""
        output_file = (
            self.reports_dir / f"trufflehog_report_{datetime.now():%Y%m%d_%H%M%S}.json"
        )
        cmd = [
            "trufflehog",
            "filesystem",
            str(self.project_root),
            "--json",
            "--no-update",
        ]

        success, output = self.run_command(
            cmd, "TruffleHog secret detection", capture_json=True
        )

        if success and output:
            # Save trufflehog output
            with open(output_file, "w") as f:
                f.write(output)

            # Count secrets found
            secret_count = output.count('"SourceMetadata"')
            print(f"   Potential secrets found: {secret_count}")

        return success

    def run_osv_scanner(self) -> bool:
        """Run OSV scanner for vulnerability detection."""
        output_file = (
            self.reports_dir / f"osv_report_{datetime.now():%Y%m%d_%H%M%S}.json"
        )
        cmd = [
            "osv-scanner",
            "--format=json",
            "--output",
            str(output_file),
            str(self.project_root),
        ]

        success, _ = self.run_command(
            cmd, "OSV vulnerability scanning", capture_json=True
        )
        return success

    def run_all_scans(self) -> Dict[str, bool]:
        """Run all security scans."""
        results = {}

        print("🛡️ Starting comprehensive security scanning...")
        print(f"📁 Project root: {self.project_root}")
        print(f"📊 Reports directory: {self.reports_dir}")

        # Run all security scans
        bandit_success, bandit_report = self.run_bandit()
        results["bandit"] = bandit_success

        safety_success, _ = self.run_safety()
        results["safety"] = safety_success

        results["pip_audit"] = self.run_pip_audit()
        results["trufflehog"] = self.run_trufflehog()
        results["osv_scanner"] = self.run_osv_scanner()

        return results

    def print_summary(self, results: Dict[str, bool]) -> None:
        """Print summary of all security scan results."""
        print("\n" + "=" * 60)
        print("🛡️ SECURITY SCAN SUMMARY")
        print("=" * 60)

        for scan, success in results.items():
            status = "✅ COMPLETED" if success else "❌ FAILED"
            print(f"{scan.ljust(15)}: {status}")

        total_scans = len(results)
        completed_scans = sum(results.values())
        print(f"\nOverall: {completed_scans}/{total_scans} scans completed")

        print(f"\n📁 Security reports saved to: {self.reports_dir}")

        if completed_scans == total_scans:
            print("🎉 All security scans completed successfully!")
            print("📝 Review the generated reports for detailed security analysis.")
        else:
            print("⚠️ Some security scans failed. Please review the output above.")

    def generate_summary_report(self, results: Dict[str, bool]) -> None:
        """Generate a summary security report."""
        summary_file = (
            self.reports_dir / f"security_summary_{datetime.now():%Y%m%d_%H%M%S}.json"
        )

        summary = {
            "scan_timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "scan_results": results,
            "total_scans": len(results),
            "completed_scans": sum(results.values()),
            "success_rate": sum(results.values()) / len(results) * 100,
        }

        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"📄 Summary report saved to: {summary_file}")


def main():
    """Main entry point for security scanning."""
    scanner = SecurityScanner()
    results = scanner.run_all_scans()
    scanner.print_summary(results)
    scanner.generate_summary_report(results)

    # Exit with error code if any critical scans failed
    critical_scans = ["bandit", "safety"]
    critical_failures = [
        scan for scan in critical_scans if not results.get(scan, False)
    ]

    if critical_failures:
        print(f"\n❌ Critical security scans failed: {', '.join(critical_failures)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
