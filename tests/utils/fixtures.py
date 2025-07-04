"""
Test fixture helpers for loading and managing test data.

This module provides utilities for loading fixtures and creating
dynamic test data for different test scenarios.
"""

import json
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import yaml

# Fixture file paths
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def load_fixture_data(filename: str) -> Any:
    """Load fixture data from a file in the fixtures directory."""
    file_path = FIXTURES_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Fixture file not found: {file_path}")

    if file_path.suffix in [".yaml", ".yml"]:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    elif file_path.suffix == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()


def get_sample_workflows() -> List[Dict[str, Any]]:
    """Get a collection of sample workflows for testing."""
    return [
        {
            "name": "Simple Echo",
            "description": "A simple echo command",
            "command": "echo 'Hello, World!'",
            "tags": ["test", "simple"],
            "shells": ["bash", "zsh"],
        },
        {
            "name": "Python Script",
            "description": "Run a Python script",
            "command": "python script.py",
            "tags": ["python", "development"],
            "shells": ["bash", "zsh", "fish"],
            "arguments": [
                {
                    "name": "script_path",
                    "description": "Path to the Python script",
                    "default_value": "script.py",
                }
            ],
        },
        {
            "name": "Git Status",
            "description": "Check git repository status",
            "command": "git status && git diff --stat",
            "tags": ["git", "version-control"],
            "shells": ["bash", "zsh"],
            "requirements": ["git"],
        },
        {
            "name": "Complex Workflow",
            "description": "A complex multi-step workflow",
            "command": """
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
python -m pytest tests/ --cov=src
black --check src/
""",
            "tags": ["python", "testing", "development"],
            "shells": ["bash"],
            "arguments": [
                {
                    "name": "test_path",
                    "description": "Path to test files",
                    "default_value": "tests/",
                },
                {
                    "name": "coverage",
                    "description": "Enable coverage reporting",
                    "default_value": "true",
                },
            ],
            "requirements": ["python", "pytest", "black"],
        },
    ]


def get_sample_prompts() -> List[Dict[str, Any]]:
    """Get a collection of sample prompts for testing."""
    return [
        {
            "name": "Code Review",
            "prompt": "Please review the following code and provide feedback on {{aspect}}",
            "description": "AI-assisted code review",
            "arguments": [
                {
                    "name": "aspect",
                    "description": "Aspect to focus on (security, performance, etc.)",
                    "default_value": "general",
                }
            ],
            "tags": ["code-review", "ai"],
        },
        {
            "name": "Documentation Generator",
            "prompt": "Generate documentation for the following {{language}} code:\n\n{{code}}\n\nInclude explanations for all functions and classes.",
            "description": "Generate code documentation",
            "arguments": [
                {
                    "name": "language",
                    "description": "Programming language",
                    "default_value": "Python",
                },
                {
                    "name": "code",
                    "description": "Code to document",
                    "default_value": "",
                },
            ],
            "tags": ["documentation", "ai"],
        },
    ]


def get_sample_notebooks() -> List[Dict[str, Any]]:
    """Get a collection of sample notebooks for testing."""
    return [
        {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["# Simple Test Notebook\n", "This is a test notebook."],
                },
                {
                    "cell_type": "code",
                    "execution_count": 1,
                    "metadata": {},
                    "outputs": [],
                    "source": ["print('Hello, World!')"],
                },
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3",
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4,
        },
        {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["# Data Analysis Example"],
                },
                {
                    "cell_type": "code",
                    "execution_count": 1,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "import pandas as pd\n",
                        "import numpy as np\n",
                        "\n",
                        "# Create sample data\n",
                        "data = pd.DataFrame({\n",
                        "    'x': np.random.randn(100),\n",
                        "    'y': np.random.randn(100)\n",
                        "})\n",
                        "\n",
                        "print(data.head())",
                    ],
                },
                {
                    "cell_type": "code",
                    "execution_count": 2,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "# Statistical analysis\n",
                        "correlation = data['x'].corr(data['y'])\n",
                        "print(f'Correlation: {correlation:.3f}')",
                    ],
                },
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3",
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4,
        },
    ]


def get_invalid_test_data() -> Dict[str, Any]:
    """Get invalid test data for testing error handling."""
    return {
        "invalid_yaml": "invalid: yaml: content: [",
        "invalid_json": '{"invalid": json content}',
        "missing_required_fields": {
            "description": "Missing name field",
            "command": "echo test",
        },
        "empty_command": {
            "name": "Empty Command",
            "command": "",
            "description": "Test with empty command",
        },
        "invalid_types": {
            "name": 123,  # Should be string
            "command": ["echo", "test"],  # Should be string
            "tags": "not a list",  # Should be list
        },
        "security_threats": [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "$(rm -rf /)",
        ],
    }


def get_edge_case_data() -> Dict[str, Any]:
    """Get edge case test data."""
    return {
        "very_long_string": "A" * 10000,
        "unicode_content": "Hello 世界 🌍",
        "special_characters": "!@#$%^&*()_+-=[]{}|;':\",./<>?",
        "empty_values": {
            "empty_string": "",
            "empty_list": [],
            "empty_dict": {},
            "null_value": None,
        },
        "nested_structure": {
            "level1": {
                "level2": {"level3": {"level4": {"level5": "deeply nested value"}}}
            }
        },
        "large_list": list(range(1000)),
        "binary_data": b"\x00\x01\x02\x03\x04\x05",
    }


def create_mixed_content_fixture() -> str:
    """Create a mixed content fixture with multiple document types."""
    return """---
# Workflow
name: Test Workflow
description: A test workflow
command: echo "test"
tags:
  - test
shells:
  - bash
---

---
# Prompt
name: Test Prompt
prompt: "Please help with {{task}}"
description: A test prompt
arguments:
  - name: task
    description: The task to help with
    default_value: "general assistance"
tags:
  - ai
---

# Rule
title: Test Rule
description: A test development rule
guidelines:
  - Follow the rule
  - Document everything
category: testing
tags:
  - development
  - testing

---
# Notebook
title: Test Notebook
description: A test notebook guide
tags:
  - notebook
  - guide
---

# Test Notebook

This is a test notebook content.

## Code Example

```python
def hello():
    print("Hello, World!")
```

## More Content

This notebook demonstrates various features.
"""


def get_performance_test_data() -> Dict[str, Any]:
    """Get data for performance testing."""
    return {
        "small_dataset": {"workflows": [get_sample_workflows()[0]], "size": "small"},
        "medium_dataset": {"workflows": get_sample_workflows() * 10, "size": "medium"},
        "large_dataset": {"workflows": get_sample_workflows() * 100, "size": "large"},
        "very_large_dataset": {
            "workflows": get_sample_workflows() * 1000,
            "size": "very_large",
        },
    }


def generate_test_file_content(content_type: str, **kwargs) -> str:
    """Generate test file content based on type."""
    if content_type == "workflow":
        workflow = kwargs.get("workflow", get_sample_workflows()[0])
        return yaml.dump(workflow, default_flow_style=False)

    elif content_type == "notebook":
        notebook = kwargs.get("notebook", get_sample_notebooks()[0])
        return json.dumps(notebook, indent=2)

    elif content_type == "mixed":
        return create_mixed_content_fixture()

    elif content_type == "invalid_yaml":
        return "invalid: yaml: content: ["

    elif content_type == "invalid_json":
        return '{"invalid": json content}'

    elif content_type == "empty":
        return ""

    else:
        raise ValueError(f"Unknown content type: {content_type}")


class FixtureManager:
    """Manager for handling test fixtures."""

    def __init__(self, fixtures_dir: Optional[Path] = None):
        self.fixtures_dir = fixtures_dir or FIXTURES_DIR

    def load(self, filename: str) -> Any:
        """Load a fixture file."""
        return load_fixture_data(filename)

    def get_workflows(self) -> List[Dict[str, Any]]:
        """Get sample workflows."""
        return get_sample_workflows()

    def get_prompts(self) -> List[Dict[str, Any]]:
        """Get sample prompts."""
        return get_sample_prompts()

    def get_notebooks(self) -> List[Dict[str, Any]]:
        """Get sample notebooks."""
        return get_sample_notebooks()

    def get_invalid_data(self) -> Dict[str, Any]:
        """Get invalid test data."""
        return get_invalid_test_data()

    def get_edge_cases(self) -> Dict[str, Any]:
        """Get edge case data."""
        return get_edge_case_data()

    def generate_content(self, content_type: str, **kwargs) -> str:
        """Generate test content."""
        return generate_test_file_content(content_type, **kwargs)

    def create_temp_fixture(
        self, content: str, suffix: str = ".yaml"
    ) -> Generator[Path, None, None]:
        """Create a temporary fixture file."""
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False, dir=self.fixtures_dir
        ) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            yield temp_path
        finally:
            if temp_path.exists():
                temp_path.unlink()


# Global fixture manager instance
fixture_manager = FixtureManager()
