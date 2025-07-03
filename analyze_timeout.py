#!/usr/bin/env python3
"""
Pytest Timeout Analysis Tool

This script helps analyze pytest timeout failures by:
1. Running tests with timeout and capturing detailed output
2. Parsing stack traces to identify hanging operations
3. Providing recommendations for fixes
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class TimeoutAnalyzer:
    def __init__(self):
        self.timeout_patterns = {
            "simple_sleep": r"time\.sleep\(",
            "infinite_loop": r"while\s+True:|for\s+.*\s+in\s+.*:",
            "socket_io": r"socket\.(connect|recv|send|accept)",
            "requests": r"requests\.(get|post|put|delete)",
            "database": r"\.(execute|fetchall|fetchone|commit)",
            "file_io": r"(open|read|write|close)\(",
            "threading": r"(\.join\(|\.acquire\(|with\s+\w+:)",
        }

        self.recommendations = {
            "simple_sleep": [
                "Consider if sleep is necessary",
                "Use shorter sleep duration",
                "Replace with proper synchronization",
            ],
            "infinite_loop": [
                "Add proper exit condition",
                "Implement maximum iteration limit",
                "Add timeout mechanism",
            ],
            "socket_io": [
                "Add socket timeout with settimeout()",
                "Use connection timeout parameter",
                "Implement retry logic with backoff",
            ],
            "requests": [
                "Add timeout parameter to requests",
                "Use session with connection pooling",
                "Implement circuit breaker pattern",
            ],
            "database": [
                "Add query timeout",
                "Use connection pooling",
                "Check for long-running transactions",
            ],
            "file_io": [
                "Add file operation timeout",
                "Check if file is on network share",
                "Use async file operations",
            ],
            "threading": [
                "Check for deadlock patterns",
                "Use lock ordering",
                "Add timeout to join() calls",
            ],
        }

    def run_test_with_timeout(
        self, test_path: str, timeout: int = 10, log_level: str = "DEBUG"
    ) -> Tuple[str, str, int]:
        """Run pytest with timeout and capture output."""
        log_file = Path(f"timeout_analysis_{Path(test_path).stem}.log")

        cmd = [
            "python",
            "-m",
            "pytest",
            test_path,
            f"--timeout={timeout}",
            "--timeout-method=thread",
            "-v",
            "-s",
            f"--log-file={log_file}",
            f"--log-level={log_level}",
            "--tb=long",
        ]

        print(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 10,  # Add buffer to pytest timeout
            )

            # Read log file if it exists
            log_content = ""
            if log_file.exists():
                log_content = log_file.read_text()

            return result.stdout, log_content, result.returncode

        except subprocess.TimeoutExpired:
            return "", "", -1

    def parse_stack_trace(self, output: str) -> List[Dict]:
        """Parse stack traces from pytest timeout output."""
        traces = []

        # Find timeout sections
        timeout_sections = re.findall(
            r"\+{10,}\s*Timeout\s*\+{10,}(.*?)\+{10,}\s*Timeout\s*\+{10,}",
            output,
            re.DOTALL,
        )

        for section in timeout_sections:
            # Extract thread stacks
            thread_stacks = re.findall(
                r"Stack of (\w+.*?) \((\d+)\).*?\n(.*?)(?=Stack of|\+{10,}|$)",
                section,
                re.DOTALL,
            )

            for thread_name, thread_id, stack_content in thread_stacks:
                # Extract file/line information
                file_lines = re.findall(
                    r'File "([^"]+)", line (\d+), in (\w+)\n\s*(.+)', stack_content
                )

                if file_lines:
                    traces.append(
                        {
                            "thread_name": thread_name.strip(),
                            "thread_id": thread_id,
                            "stack_frames": [
                                {
                                    "file": file_path,
                                    "line": int(line_num),
                                    "function": func_name,
                                    "code": code_line.strip(),
                                }
                                for file_path, line_num, func_name, code_line in file_lines
                            ],
                        }
                    )

        return traces

    def analyze_hanging_operation(self, traces: List[Dict]) -> Dict:
        """Analyze stack traces to identify type of hanging operation."""
        analysis = {
            "timeout_type": "unknown",
            "likely_cause": [],
            "hanging_location": None,
            "recommendations": [],
        }

        for trace in traces:
            if not trace["stack_frames"]:
                continue

            # Analyze the last frame (where execution was when timeout occurred)
            last_frame = trace["stack_frames"][-1]
            code_line = last_frame["code"]

            # Check against patterns
            for pattern_name, pattern in self.timeout_patterns.items():
                if re.search(pattern, code_line):
                    analysis["timeout_type"] = pattern_name
                    analysis["likely_cause"].append(
                        {
                            "type": pattern_name,
                            "location": f"{last_frame['file']}:{last_frame['line']}",
                            "code": code_line,
                            "thread": trace["thread_name"],
                        }
                    )

                    if pattern_name in self.recommendations:
                        analysis["recommendations"].extend(
                            self.recommendations[pattern_name]
                        )

        # Special analysis for deadlocks
        if len(traces) > 1:
            thread_locks = []
            for trace in traces:
                for frame in trace["stack_frames"]:
                    if "with " in frame["code"] and ":" in frame["code"]:
                        thread_locks.append(
                            {
                                "thread": trace["thread_name"],
                                "location": f"{frame['file']}:{frame['line']}",
                                "code": frame["code"],
                            }
                        )

            if len(thread_locks) >= 2:
                analysis["timeout_type"] = "deadlock"
                analysis["likely_cause"] = thread_locks
                analysis["recommendations"] = self.recommendations["threading"]

        return analysis

    def generate_report(
        self, test_path: str, traces: List[Dict], analysis: Dict, log_content: str
    ) -> str:
        """Generate comprehensive analysis report."""
        report = f"""
# Timeout Analysis Report for {test_path}

## Summary
- **Timeout Type**: {analysis['timeout_type']}
- **Threads Involved**: {len(traces)}

## Stack Trace Analysis
"""

        for i, trace in enumerate(traces, 1):
            report += f"""
### Thread {i}: {trace['thread_name']} (ID: {trace['thread_id']})

**Stack Frames:**
"""
            for frame in trace["stack_frames"]:
                report += f"""
- `{frame['file']}:{frame['line']}` in `{frame['function']}()`
  ```python
  {frame['code']}
  ```
"""

        if analysis["likely_cause"]:
            report += f"""
## Likely Cause
"""
            for cause in analysis["likely_cause"]:
                if isinstance(cause, dict) and "type" in cause:
                    report += f"""
- **Type**: {cause['type']}
- **Location**: {cause['location']}
- **Thread**: {cause['thread']}
- **Code**: `{cause['code']}`
"""
                elif isinstance(cause, dict):
                    # Handle deadlock case
                    report += f"""
- **Thread**: {cause.get('thread', 'Unknown')}
- **Location**: {cause.get('location', 'Unknown')}
- **Code**: `{cause.get('code', 'Unknown')}`
"""

        if analysis["recommendations"]:
            report += f"""
## Recommendations
"""
            for rec in analysis["recommendations"]:
                report += f"- {rec}\n"

        if log_content.strip():
            report += f"""
## Log Analysis
```
{log_content[-1000:]}  # Last 1000 characters
```
"""

        return report

    def analyze_test(self, test_path: str, timeout: int = 10) -> str:
        """Complete analysis workflow for a test."""
        print(f"Analyzing timeout behavior for: {test_path}")

        # Run test with timeout
        stdout, log_content, returncode = self.run_test_with_timeout(test_path, timeout)

        if returncode == 0:
            return f"Test {test_path} completed successfully within {timeout}s"

        # Parse stack traces
        traces = self.parse_stack_trace(stdout)

        if not traces:
            return (
                f"No timeout detected or unable to parse stack traces for {test_path}"
            )

        # Analyze hanging operations
        analysis = self.analyze_hanging_operation(traces)

        # Generate report
        report = self.generate_report(test_path, traces, analysis, log_content)

        return report


def main():
    parser = argparse.ArgumentParser(description="Analyze pytest timeout failures")
    parser.add_argument("test_path", help="Path to test file or specific test")
    parser.add_argument(
        "--timeout", "-t", type=int, default=10, help="Timeout duration in seconds"
    )
    parser.add_argument("--output", "-o", help="Output file for report")

    args = parser.parse_args()

    analyzer = TimeoutAnalyzer()
    report = analyzer.analyze_test(args.test_path, args.timeout)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
