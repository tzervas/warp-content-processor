#!/usr/bin/env python3
"""Debug test to understand the validation logic."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def debug_key_validation():
    """Debug the key validation logic."""
    test_keys = [
        '"../../../etc/passwd"',
        '"/etc/passwd"',
        '"<script>alert(1)</script>"',
        '"command | rm -rf /"',
        '"Full Name"',
        '"API Key"',
    ]

    for test_key in test_keys:
        print(f"\nTesting key: {test_key}")

        # Basic validation
        if not test_key or test_key.startswith("#") or len(test_key) > 50:
            print("  Failed basic validation")
            continue

        # Handle quoted keys
        if (test_key.startswith('"') and test_key.endswith('"')) or (
            test_key.startswith("'") and test_key.endswith("'")
        ):
            # Remove quotes and validate the inner content
            inner_key = test_key[1:-1]
            print(f"  Inner key: {inner_key}")

            # Check individual conditions
            print(f"  Empty check: {not inner_key}")
            print(f"  Starts with #: {inner_key.startswith('#')}")
            print(f"  Contains ..: {'..' in inner_key}")
            print(f"  Starts with /: {inner_key.startswith('/')}")
            backslash_check = inner_key.startswith("\\")
            print(f"  Starts with \\: {backslash_check}")

            dangerous_chars = ["<", ">", "|", "&", ";", "`", "$"]
            char_checks = [f"{c} in key: {c in inner_key}" for c in dangerous_chars]
            print(f"  Dangerous chars: {char_checks}")

            # Combined check
            if (
                not inner_key
                or inner_key.startswith("#")
                or ".." in inner_key  # Path traversal
                or inner_key.startswith("/")  # Absolute paths
                or inner_key.startswith("\\\\")  # Windows paths
                or any(
                    c in inner_key for c in ["<", ">", "|", "&", ";", "`", "$"]
                )  # Command injection chars
            ):
                print("  REJECTED: Contains unsafe patterns")
                continue
            else:
                print("  ACCEPTED: Safe quoted key")
        else:
            print("  Unquoted key")


if __name__ == "__main__":
    debug_key_validation()
