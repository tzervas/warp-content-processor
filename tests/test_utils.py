import os
import sys
from contextlib import contextmanager
from io import StringIO


@contextmanager
def capture_console_output():
    """Capture stdout and stderr output."""
    stdout, stderr = StringIO(), StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = stdout, stderr
        yield stdout, stderr
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr


def read_log_file(log_dir, log_file):
    """Read contents of a log file from the logs directory."""
    log_path = os.path.join(log_dir, log_file)
    if not os.path.exists(log_path):
        return ""
    with open(log_path, "r") as f:
        return f.read()


@contextmanager
def capture_logs(log_dir="logs"):
    """Capture both console output and log files."""
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Get initial state of log files
    initial_logs = {}
    if os.path.exists(log_dir):
        for log_file in os.listdir(log_dir):
            initial_logs[log_file] = read_log_file(log_dir, log_file)

    # Capture console output
    with capture_console_output() as (stdout, stderr):
        yield {
            "stdout": stdout,
            "stderr": stderr,
            "get_logs": lambda: {
                "console": {"stdout": stdout.getvalue(), "stderr": stderr.getvalue()},
                "files": {
                    log_file: read_log_file(log_dir, log_file)
                    for log_file in os.listdir(log_dir)
                    if read_log_file(log_dir, log_file)
                    != initial_logs.get(log_file, "")
                },
            },
        }
