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
    try:
        with open(log_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def _get_initial_logs(log_dir):
    """Helper to get initial state of log files."""
    initial_logs = {}
    try:
        log_files = os.listdir(log_dir)
        initial_logs = {
            log_file: read_log_file(log_dir, log_file) for log_file in log_files
        }
    except FileNotFoundError:
        pass
    return initial_logs


def _get_changed_logs(log_dir, initial_logs):
    """Helper to get logs that have changed since initial state."""
    try:
        log_files = os.listdir(log_dir)
        return {
            log_file: read_log_file(log_dir, log_file)
            for log_file in log_files
            if read_log_file(log_dir, log_file) != initial_logs.get(log_file, "")
        }
    except FileNotFoundError:
        return {}


@contextmanager
def capture_logs(log_dir="logs"):
    """Capture both console output and log files."""
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Get initial state of log files
    initial_logs = _get_initial_logs(log_dir)

    # Capture console output
    with capture_console_output() as (stdout, stderr):
        yield {
            "stdout": stdout,
            "stderr": stderr,
            "get_logs": lambda: {
                "console": {"stdout": stdout.getvalue(), "stderr": stderr.getvalue()},
                "files": _get_changed_logs(log_dir, initial_logs),
            },
        }
