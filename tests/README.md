# Test Infrastructure

This directory contains the comprehensive test infrastructure for the warp-content-processor project.

## Structure

```
tests/
├── conftest.py                 # Core pytest configuration and shared fixtures
├── test_smoke.py              # Smoke tests to verify test infrastructure
├── fixtures/                  # Test data fixtures
│   ├── example_workflow.yaml  # Sample workflow data
│   ├── mixed_content.yaml     # Mixed content types
│   ├── sample_notebook.json   # Sample Jupyter notebook
│   └── test_data.yaml         # Additional test data
├── utils/                     # Test utilities and helpers
│   ├── __init__.py           # Test utilities exports
│   ├── test_helpers.py       # Helper functions for testing
│   ├── assertions.py         # Custom assertion functions
│   └── fixtures.py           # Fixture management utilities
└── [test modules]            # Actual test files
```

## Key Features

### 1. Comprehensive Pytest Configuration
- Coverage reporting with multiple formats (terminal, HTML, XML)
- Custom test markers for categorization
- Strict configuration for better test reliability
- Timeout protection for long-running tests
- Detailed test duration reporting

### 2. Rich Fixture System
- Pre-configured test data and environments
- Mock file systems for testing file operations
- Sample content for different content types
- Security test payloads for validation testing
- Temporary file management

### 3. Custom Assertions
- YAML/JSON structure validation
- Security content validation
- File existence and content assertions
- Performance and memory usage assertions
- Workflow and notebook structure validation

### 4. Test Utilities
- Temporary file creation helpers
- Mock file system operations
- Log capture utilities
- Test data loading functions
- Environment variable management

## Usage

### Running Tests

```bash
# Run all tests
pytest

# Run with no coverage (faster for development)
pytest --no-cov

# Run specific test categories
pytest -m smoke          # Smoke tests only
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m security       # Security-related tests

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_smoke.py

# Run specific test function
pytest tests/test_smoke.py::test_pytest_running
```

### Using Test Markers

The test infrastructure provides several markers for categorizing tests:

- `@pytest.mark.smoke` - Basic functionality tests
- `@pytest.mark.unit` - Unit tests (default for most tests)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.security` - Security-related tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.slow` - Tests that take longer to run

### Using Fixtures

Import and use fixtures in your tests:

```python
def test_example(test_data_dir, sample_yaml_content):
    # test_data_dir points to tests/fixtures/
    # sample_yaml_content provides sample YAML data
    pass

def test_with_temp_files(mock_file_system):
    # mock_file_system provides a temporary file structure
    sample_file = mock_file_system / "sample.yaml" 
    assert sample_file.exists()
```

### Using Test Utilities

```python
from tests.utils.test_helpers import create_temp_file, TemporaryTestFile
from tests.utils.assertions import assert_yaml_structure, assert_security_safe
from tests.utils.fixtures import fixture_manager

def test_example():
    # Create temporary files
    with TemporaryTestFile("test content", ".txt") as temp_file:
        content = temp_file.read_text()
        assert content == "test content"
    
    # Use custom assertions
    data = {"name": "test", "command": "echo test"}
    assert_yaml_structure(data, ["name", "command"])
    
    # Use fixture manager
    workflows = fixture_manager.get_workflows()
    assert len(workflows) > 0
```

### Custom Assertions

The test infrastructure provides many custom assertions for better error messages:

```python
from tests.utils.assertions import (
    assert_yaml_structure,
    assert_file_exists,
    assert_security_safe,
    assert_workflow_structure,
    assert_notebook_structure
)

def test_validation():
    # Validate YAML structure
    data = {"name": "test", "command": "echo test"}
    assert_yaml_structure(data, ["name", "command"])
    
    # Validate security
    safe_content = "echo 'Hello World'"
    assert_security_safe(safe_content)
    
    # Validate workflow structure
    workflow = {"name": "Test", "command": "echo test"}
    assert_workflow_structure(workflow)
```

## Test Data

### Fixtures Directory

The `fixtures/` directory contains various test data files:

- `example_workflow.yaml` - Sample workflow configuration
- `mixed_content.yaml` - File with multiple content types
- `sample_notebook.json` - Sample Jupyter notebook
- `test_data.yaml` - Additional test data for validation

### Dynamic Test Data

Use the fixture manager to generate test data programmatically:

```python
from tests.utils.fixtures import fixture_manager

# Get sample data
workflows = fixture_manager.get_workflows()
notebooks = fixture_manager.get_notebooks()
prompts = fixture_manager.get_prompts()

# Generate content
yaml_content = fixture_manager.generate_content("workflow")
notebook_content = fixture_manager.generate_content("notebook")
```

## Configuration

The test configuration is in `pyproject.toml` under `[tool.pytest.ini_options]`. Key settings:

- **Coverage**: 80% minimum coverage requirement
- **Timeouts**: 60-second timeout for individual tests
- **Markers**: Strict marker validation
- **Output**: Multiple coverage report formats
- **Warnings**: Error on most warnings for stricter testing

## Best Practices

1. **Use appropriate markers** - Mark tests with their category
2. **Use fixtures for test data** - Don't hardcode test data in tests
3. **Use custom assertions** - They provide better error messages
4. **Keep tests focused** - One assertion per test when possible
5. **Use temporary files** - Don't leave test artifacts
6. **Test edge cases** - Use the provided edge case data
7. **Test security** - Use security test payloads for validation

## Smoke Tests

The `test_smoke.py` file contains smoke tests that verify the test infrastructure itself. Run these first when setting up or debugging test issues:

```bash
pytest tests/test_smoke.py -v
```

These tests verify:
- Pytest is running correctly
- All fixtures are working
- Test utilities can be imported
- Custom assertions work
- File operations work
- Environment is properly configured
