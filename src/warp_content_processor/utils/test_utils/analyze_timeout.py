#!/usr/bin/env python3
"""
Pytest Timeout Analysis Tool

This script helps analyze pytest timeout failures by:
1. Running tests with timeout and capturing detailed output
2. Parsing stack traces to identify hanging operations
3. Providing recommendations for fixes
"""

import argparse
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple


class TimeoutAnalyzer:
    def __init__(self):
        self.timeout_patterns = {
            "simple_sleep": r"time\.sleep\(",
            "infinite_loop": r"while\s+True:",
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
        import shlex

        # Validate and sanitize inputs
        if not isinstance(test_path, str) or not test_path.strip():
            raise ValueError("Invalid test_path provided")
        if timeout <= 0 or timeout > 3600:  # Max 1 hour timeout
            raise ValueError("Invalid timeout value")
        if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("Invalid log_level provided")

        # Sanitize test_path to prevent injection
        safe_test_path = shlex.quote(test_path)
        log_file_name = f"timeout_analysis_{Path(test_path).stem}.log"
        log_file = Path(log_file_name)
        safe_log_file = shlex.quote(str(log_file))

        # Use static command array with sanitized inputs
        cmd = [
            "python",
            "-m",
            "pytest",
            safe_test_path,
            f"--timeout={timeout}",
            "--timeout-method=thread",
            "-v",
            "-s",
            f"--log-file={safe_log_file}",
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

            log_content = log_file.read_text() if log_file.exists() else ""
            return result.stdout, log_content, result.returncode

        except subprocess.TimeoutExpired:
            print("Subprocess timed out while running the command: {}".format(" ".join(cmd)))
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
                # Extract file/line information using named expression
                if file_lines := re.findall(
                    r'File "([^"]+)", line (\d+), in (\w+)\n\s*(.+)', stack_content
                ):
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

    def _analyze_single_trace(self, trace: Dict) -> Tuple[str, Dict]:
        """Analyze a single trace for timeout patterns."""
        if not trace.get("stack_frames"):
            return None, None

        last_frame = trace["stack_frames"][-1]
        code_line = last_frame.get("code", "")

        for pattern_name, pattern in self.timeout_patterns.items():
            if re.search(pattern, code_line):
                cause = {
                    "type": pattern_name,
                    "location": f"{last_frame.get('file', 'unknown')}:{last_frame.get('line', 'unknown')}",
                    "code": code_line,
                    "thread": trace.get("thread_name", "unknown"),
                }
                return pattern_name, cause

        return None, None

    def _detect_deadlock(self, traces: List[Dict]) -> Tuple[bool, List[Dict]]:
        """Detect potential deadlocks from multiple traces."""
        if len(traces) <= 1:
            return False, []

        thread_locks = [
            {
                "thread": trace.get("thread_name", "unknown"),
                "location": f"{frame.get('file', 'unknown')}:{frame.get('line', 'unknown')}",
                "code": frame.get("code", ""),
            }
            for trace in traces
            for frame in trace.get("stack_frames", [])
            if "with " in frame.get("code", "") and ":" in frame.get("code", "")
        ]

        return len(thread_locks) >= 2, thread_locks

    def analyze_hanging_operation(self, traces: List[Dict]) -> Dict:
        """Analyze stack traces to identify type of hanging operation."""
        analysis = {
            "timeout_type": "unknown",
            "likely_cause": [],
            "hanging_location": None,
            "recommendations": [],
        }

        # Analyze individual traces
        for trace in traces:
            pattern_name, cause = self._analyze_single_trace(trace)
            if pattern_name and cause:
                analysis["timeout_type"] = pattern_name
                analysis["likely_cause"].append(cause)

        # Check for deadlocks
        is_deadlock, thread_locks = self._detect_deadlock(traces)
        if is_deadlock:
            analysis["timeout_type"] = "deadlock"
            analysis["likely_cause"] = thread_locks

        # Set recommendations based on final timeout_type
        if analysis["timeout_type"] in self.recommendations:
            analysis["recommendations"] = self.recommendations[analysis["timeout_type"]]

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
            report += """
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
            report += """
## Recommendations
"""
            for rec in analysis["recommendations"]:
                report += f"- {rec}\n"

        def format_log_excerpt(log: str, max_length: int = 1000) -> str:
            if len(log) <= max_length:
                return log
            head_len = max_length // 2
            tail_len = max_length - head_len
            head = log[:head_len]
            tail = log[-tail_len:]
            return f"{head}\n...\n{tail}"

        LOG_EXCERPT_LENGTH = 1000  # Can be made configurable

        if log_content.strip():
            report += f"""
## Log Analysis

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

        return self.generate_report(test_path, traces, analysis, log_content)


def main():
    parser = argparse.ArgumentParser(description="Analyze pytest timeout failures")
    parser.add_argument("test_path", help="Path to test file or specific test")
    parser.add_argument(
        "--timeout", "-t", type=int, default=10, help="Timeout duration in seconds"
    )
    parser.add_argument("--output", "-o", help="Output file for report")
    parser.add_argument(
        "--log-level",
        default="DEBUG",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: DEBUG)",
    )

    args = parser.parse_args()

    import logging
    logging.basicConfig(level=getattr(logging, args.log_level))

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
