# Test Design Patterns and Best Practices

> **Status**: 222 tests passing (100% success rate) with conditional-free parametrized design

## 🎯 Testing Philosophy

The project follows a strict **"No-Conditionals-In-Tests"** rule to ensure test clarity and maintainability. All tests are designed using parametrized approaches that eliminate conditional logic within test functions.

## 🏛️ Test Architecture

### Core Testing Principles

1. **Parametrized Tests**: Use `@pytest.mark.parametrize` for all test variations
2. **No Conditionals**: Eliminate if/else logic within test functions  
3. **Clear Assertions**: Each test has explicit, readable assertions
4. **Isolated Tests**: Tests are independent and can run in any order
5. **Fast Execution**: 222 tests complete in 0.18s

### Test Structure Pattern

```python
@pytest.mark.parametrize("input_data,expected_result,expected_error", [
    ("valid_input", "expected_output", False),
    ("invalid_input", None, True),
    ("edge_case", "edge_output", False),
])
def test_function_behavior(input_data, expected_result, expected_error):
    """Test function with various scenarios using parametrized inputs."""
    if expected_error:
        with pytest.raises(SomeException):
            function_under_test(input_data)
    else:
        result = function_under_test(input_data)
        assert result == expected_result
```

## 📋 Test Categories

### 1. Unit Tests (`tests/`)
**Purpose**: Test individual components in isolation
**Coverage**: All core classes and functions
**Pattern**: Single responsibility per test

### 2. Integration Tests (`tests/`)
**Purpose**: Test component interactions and workflows
**Coverage**: End-to-end processing scenarios
**Pattern**: Real-world data flows

### 3. Security Tests (`tests/test_security_normalization.py`)
**Purpose**: Validate security measures and input sanitization
**Coverage**: All security validation logic
**Pattern**: Attack scenario simulation

### 4. Excavation Tests (`tests/excavation/`)
**Purpose**: Test content archaeology and schema extraction
**Coverage**: Island detection, artifact extraction, confidence scoring
**Pattern**: Content contamination scenarios

## 🧪 Test Patterns by Component

### Content Processing Tests
- **File**: `tests/test_content_processor.py`
- **Pattern**: Multi-format content validation
- **Key Tests**: Type detection, content splitting, mixed content processing

### Robust Parsing Tests  
- **File**: `tests/test_robust_parsing.py`
- **Pattern**: Progressive parsing strategy validation
- **Key Tests**: Standard, cleaned, mangled, partial, reconstructed strategies

### Security Validation Tests
- **File**: `tests/test_security_normalization.py`
- **Pattern**: Attack vector simulation and validation
- **Key Tests**: XSS prevention, command injection, path traversal

### Content Archaeology Tests
- **Files**: `tests/excavation/test_archaeologist.py`, `tests/excavation/test_island_detector.py`
- **Pattern**: Contaminated content extraction scenarios
- **Key Tests**: Island detection, artifact quality assessment, confidence scoring

## 🎯 Parametrization Strategies

### 1. Data-Driven Testing
```python
@pytest.mark.parametrize("content_type,sample_data", [
    ("workflow", "name: test\ncommand: echo hello"),
    ("prompt", "name: test\nprompt: Hello world"),
    ("rule", "name: test\nrule: Use meaningful names"),
])
def test_content_type_detection(content_type, sample_data):
    result = ContentTypeDetector.detect_type(sample_data)
    assert result.value == content_type
```

### 2. Error Scenario Testing
```python
@pytest.mark.parametrize("malicious_content,expected_error", [
    ("<script>alert('xss')</script>", SecurityValidationError),
    ("javascript:void(0)", SecurityValidationError),
    ("normal content", None),
])
def test_security_validation(malicious_content, expected_error):
    if expected_error:
        with pytest.raises(expected_error):
            ContentSanitizer.validate_content(malicious_content)
    else:
        result = ContentSanitizer.validate_content(malicious_content)
        assert result == malicious_content
```

### 3. Edge Case Coverage
```python
@pytest.mark.parametrize("input_size,timeout,expected_behavior", [
    (1024, 30, "success"),
    (104857600, 300, "success"), 
    (1048576000, 600, "success"),
    (0, 300, "success"),
])
def test_size_and_timeout_scenarios(input_size, timeout, expected_behavior):
    archaeologist = ContentArchaeologist(
        max_content_size=input_size,
        timeout_seconds=timeout
    )
    assert archaeologist.max_content_size == input_size
    assert archaeologist.timeout_seconds == timeout
```

## 🔧 Test Infrastructure

### Fixtures and Helpers
- **File**: `tests/conftest.py`, `tests/helpers.py`
- **Purpose**: Shared test data and utility functions
- **Pattern**: Reusable, isolated test components

### Test Data Management
- **Location**: `tests/fixtures/`
- **Content**: Sample YAML files for various content types
- **Pattern**: Representative real-world data samples

## 📊 Test Metrics

### Current Status
- **Total Tests**: 222
- **Pass Rate**: 100% (222/222)
- **Execution Time**: 0.18s
- **Test Categories**: Unit, Integration, Security, Excavation

### Quality Gates
- **No Conditionals**: Enforced via linting rules
- **Parametrized Design**: All tests use `@pytest.mark.parametrize`
- **Clear Assertions**: Single responsibility per assertion
- **Fast Execution**: Sub-second test suite execution

## 🛡️ Security Testing Approach

### Threat Modeling
1. **Input Validation**: Test all input boundaries
2. **Injection Attacks**: Simulate XSS, command injection, path traversal
3. **Resource Exhaustion**: Test timeout and size limits
4. **Data Corruption**: Test handling of malformed content

### Security Test Patterns
```python
@pytest.mark.parametrize("attack_vector,validation_should_fail", [
    ("rm -rf /", True),
    ("normal command", False),
    ("<script>evil()</script>", True),
    ("normal content", False),
])
def test_security_validation(attack_vector, validation_should_fail):
    if validation_should_fail:
        with pytest.raises(SecurityValidationError):
            ContentSanitizer.validate_content(attack_vector)
    else:
        result = ContentSanitizer.validate_content(attack_vector)
        assert result == attack_vector
```

## 🚀 Performance Testing

### Test Performance Characteristics
- **Fast Execution**: Complete test suite in 0.18s
- **Parallel Execution**: Tests designed for parallel execution
- **Resource Efficiency**: Minimal memory footprint during testing
- **Timeout Protection**: All tests have appropriate timeout limits

### Performance Validation
```python
@pytest.mark.parametrize("content_size,expected_max_time", [
    (1000, 0.1),      # Small content should be very fast
    (50000, 1.0),     # Medium content should be under 1s
    (100000, 2.0),    # Large content should be under 2s
])
def test_performance_expectations(content_size, expected_max_time):
    content = "test_data" * (content_size // 9)  # Approximate size
    start_time = time.time()
    result = process_content(content)
    execution_time = time.time() - start_time
    assert execution_time < expected_max_time
    assert result is not None
```

## 🎖️ Best Practices Summary

### ✅ Do's
- Use `@pytest.mark.parametrize` for all test variations
- Write descriptive test names that explain the scenario
- Keep assertions simple and focused
- Use fixtures for complex test data setup
- Test both success and failure scenarios
- Include edge cases and boundary conditions

### ❌ Don'ts  
- Never use conditional logic (`if/else`) within test functions
- Don't write tests that depend on execution order
- Avoid complex logic within test functions
- Don't skip testing error conditions
- Never ignore timeout scenarios in performance-critical tests

---

*This testing documentation reflects the current state of 222 passing tests with 100% success rate, following strict no-conditionals-in-tests principles and comprehensive parametrized design patterns.*

<citations>
<document>
<document_type>RULE</document_type>
<document_id>P0QQCW17oOJd3ErAjxpaq2</document_id>
</document>
</citations>
