# Parametrized Test Cases Design

## Overview

This document outlines the design and implementation of parametrized test cases that replace content-type switching logic in the test suite. The goal is to eliminate conditionals in tests and centralize assertion logic, following the "No-Conditionals-In-Tests" principle.

## Key Design Principles

1. **No Conditionals in Tests**: Avoid `if/elif` statements and loops in test functions
2. **Single Responsibility**: Each test function should have one clear purpose
3. **Centralized Assertions**: Use a single test function driven by parameters
4. **Minimal Valid Input**: Define the smallest valid input for each content type

## Implementation Details

### 1. Content Type Parameter Sets

Each content type is defined with its minimal valid input:

```python
CONTENT_TYPE_PARAMETERS = [
    pytest.param(
        ContentType.WORKFLOW,
        {"name": "test", "command": "echo test"},
        id="workflow"
    ),
    pytest.param(
        ContentType.PROMPT,
        {"name": "test", "prompt": "do {{action}}"},
        id="prompt"
    ),
    pytest.param(
        ContentType.NOTEBOOK,
        "---\\ntitle: test\\n---\\n# Test\\n```bash\\necho test\\n```",
        id="notebook"
    ),
    pytest.param(
        ContentType.ENV_VAR,
        {"variables": {"TEST": "value"}},
        id="env_var"
    ),
    pytest.param(
        ContentType.RULE,
        {
            "title": "Test Rule",
            "description": "A test rule",
            "guidelines": ["Test guideline"],
        },
        id="rule"
    ),
]
```

### 2. Parametrized Test Function

Replaced multiple individual test methods with a single parametrized test:

```python
@pytest.mark.parametrize("content_type,test_content", CONTENT_TYPE_PARAMETERS)
@pytest.mark.timeout(90)
def test_content_type_validation(self, content_type, test_content):
    """Test validation of content for each supported content type.
    
    This parametrized test replaces individual validation test methods
    to avoid conditionals in tests and centralize assertion logic.
    """
    # Skip if no processor is available for this content type
    if content_type not in self.processor.processors:
        pytest.skip(f"No processor available for {content_type}")
    
    processor = self.processor.processors[content_type]
    
    # Convert dict content to YAML if needed
    if isinstance(test_content, dict):
        content = yaml.dump(test_content)
    else:
        content = test_content

    result = processor.process(content)

    # Centralized assertion logic
    assert result.is_valid, f"Validation failed for {content_type}: {result.errors}"
    assert not result.errors, f"Unexpected errors for {content_type}: {result.errors}"
```

## Benefits

### 1. Eliminated Conditionals

**Before:**
```python
def _test_content_type_validation(self, content_type):
    if content_type not in self.processor.processors:
        pytest.skip(f"No processor available for {content_type}")
    
    processor = self.processor.processors[content_type]
    content_type_test_data = self.get_content_type_test_data()
    content = content_type_test_data[content_type]

    if isinstance(content, dict):
        content = yaml.dump(content)
    # ...

def test_workflow_validation(self):
    self._test_content_type_validation(ContentType.WORKFLOW)

def test_prompt_validation(self):
    self._test_content_type_validation(ContentType.PROMPT)
# ... more individual test methods
```

**After:**
```python
@pytest.mark.parametrize("content_type,test_content", CONTENT_TYPE_PARAMETERS)
def test_content_type_validation(self, content_type, test_content):
    # Single test function with parameters
```

### 2. Centralized Test Data

All test data is now defined in one place (`CONTENT_TYPE_PARAMETERS`) rather than scattered across multiple methods.

### 3. Better Test Organization

- Each parameter set has a clear `id` for easy identification
- Test failures are more descriptive with parameter information
- Easier to add new content types by simply adding to the parameter list

### 4. Improved Maintainability

- Single point of change for assertion logic
- Consistent test structure across all content types
- Reduced code duplication

## Test Data Design

### Minimal Valid Input Principle

Each content type parameter includes the absolute minimum required fields for validation:

- **WORKFLOW**: `name` and `command` (core requirements)
- **PROMPT**: `name` and `prompt` with template variable
- **NOTEBOOK**: Markdown with frontmatter and code block
- **ENV_VAR**: Simple variable definition
- **RULE**: Basic rule structure with title, description, and guidelines

### Parameter IDs

Each parameter has a descriptive `id` that appears in test output:
- `workflow`, `prompt`, `notebook`, `env_var`, `rule`

This makes it easy to identify which content type failed during test runs.

## Future Enhancements

### 1. Additional Test Scenarios

The parametrized approach can be extended for other test scenarios:

```python
INVALID_CONTENT_PARAMETERS = [
    pytest.param(ContentType.WORKFLOW, {}, "missing_required_fields", id="workflow-empty"),
    pytest.param(ContentType.PROMPT, {"name": "test"}, "missing_prompt", id="prompt-no-prompt"),
    # ... more invalid cases
]

@pytest.mark.parametrize("content_type,invalid_content,expected_error", INVALID_CONTENT_PARAMETERS)
def test_content_type_validation_failures(self, content_type, invalid_content, expected_error):
    # Test invalid content scenarios
```

### 2. Performance Testing

```python
PERFORMANCE_TEST_PARAMETERS = [
    pytest.param(ContentType.WORKFLOW, large_workflow_content, id="workflow-large"),
    pytest.param(ContentType.NOTEBOOK, large_notebook_content, id="notebook-large"),
    # ... performance test cases
]
```

### 3. Edge Cases

```python
EDGE_CASE_PARAMETERS = [
    pytest.param(ContentType.WORKFLOW, unicode_workflow, id="workflow-unicode"),
    pytest.param(ContentType.PROMPT, nested_template_prompt, id="prompt-nested"),
    # ... edge cases
]
```

## Migration Guide

### For Existing Tests

1. **Identify content-type switching logic**: Look for `if content_type` patterns
2. **Extract test data**: Move content definitions to parameter sets
3. **Consolidate assertions**: Combine assertion logic into single test function
4. **Add parameter decorators**: Use `@pytest.mark.parametrize`
5. **Remove individual test methods**: Delete the old conditional test methods

### For New Tests

1. **Define parameter sets first**: Start with parameter definitions
2. **Use descriptive IDs**: Make test output clear and readable
3. **Keep data minimal**: Use the smallest valid input for each type
4. **Centralize assertions**: Write assertion logic once

## Testing the Implementation

The parametrized tests can be run individually:

```bash
# Run all content type validation tests
pytest tests/test_content_processor.py::TestContentProcessor::test_content_type_validation

# Run specific content type
pytest tests/test_content_processor.py::TestContentProcessor::test_content_type_validation[workflow]

# Run with verbose output to see parameter IDs
pytest -v tests/test_content_processor.py::TestContentProcessor::test_content_type_validation
```

## Conclusion

The parametrized test design successfully:

1. ✅ Replaces content-type switching logic with `@pytest.mark.parametrize`
2. ✅ Defines parameter sets for each content type with minimal valid input
3. ✅ Isolates assertion logic into a single test function driven by parameters
4. ✅ Follows the "No-Conditionals-In-Tests" principle
5. ✅ Improves test maintainability and readability

This approach provides a solid foundation for testing multiple content types consistently while avoiding conditional logic in tests.
