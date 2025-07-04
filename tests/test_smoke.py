"""
Smoke tests for warp-content-processor test infrastructure.

These tests verify that the basic test infrastructure is working correctly
and can be used as a foundation for more comprehensive testing.
"""

import pytest
import sys
from pathlib import Path

# Test the test infrastructure itself
def test_pytest_running():
    """Verify that pytest is running correctly."""
    assert True, "Pytest basic assertion failed"


@pytest.mark.smoke
def test_imports():
    """Test that core modules can be imported."""
    try:
        import warp_content_processor
        assert hasattr(warp_content_processor, '__version__')
    except ImportError as e:
        pytest.fail(f"Failed to import warp_content_processor: {e}")


@pytest.mark.smoke  
def test_fixtures_loading(test_data_dir):
    """Test that test fixtures can be loaded."""
    assert test_data_dir.exists(), f"Test data directory does not exist: {test_data_dir}"
    
    # Check for some expected fixture files
    expected_files = ["example_workflow.yaml", "mixed_content.yaml"]
    for filename in expected_files:
        file_path = test_data_dir / filename
        assert file_path.exists(), f"Expected fixture file not found: {file_path}"


@pytest.mark.smoke
def test_temp_directory_fixture(temp_dir):
    """Test that temporary directory fixture works."""
    assert temp_dir.exists(), "Temporary directory was not created"
    assert temp_dir.is_dir(), "Temporary directory is not a directory"
    
    # Test writing to temp directory
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")
    assert test_file.exists(), "Could not create file in temporary directory"
    assert test_file.read_text() == "test content", "File content mismatch"


@pytest.mark.smoke
def test_yaml_fixtures(yaml_test_data):
    """Test that YAML test data fixtures work."""
    assert "valid_yaml" in yaml_test_data
    assert "invalid_yaml" in yaml_test_data
    assert "complex_yaml" in yaml_test_data
    
    # Test valid YAML structure
    valid_data = yaml_test_data["valid_yaml"]
    assert isinstance(valid_data, dict)
    assert "key" in valid_data
    assert valid_data["key"] == "value"


@pytest.mark.smoke
def test_sample_content_fixtures(sample_yaml_content, sample_notebook_content):
    """Test that sample content fixtures work."""
    # Test YAML content
    assert isinstance(sample_yaml_content, str)
    assert "workflows:" in sample_yaml_content
    assert len(sample_yaml_content.strip()) > 0
    
    # Test notebook content
    assert isinstance(sample_notebook_content, dict)
    assert "cells" in sample_notebook_content
    assert "metadata" in sample_notebook_content
    assert isinstance(sample_notebook_content["cells"], list)


@pytest.mark.smoke
def test_mock_file_system(mock_file_system):
    """Test that mock file system fixture works."""
    assert mock_file_system.exists()
    assert mock_file_system.is_dir()
    
    # Check that sample files were created
    expected_files = ["sample.yaml", "sample.yml", "sample.ipynb", "sample.txt"]
    for filename in expected_files:
        file_path = mock_file_system / filename
        assert file_path.exists(), f"Expected mock file not found: {filename}"


@pytest.mark.smoke
def test_validation_test_cases(validation_test_cases):
    """Test that validation test cases fixture works."""
    assert isinstance(validation_test_cases, list)
    assert len(validation_test_cases) > 0
    
    # Check structure of test cases
    for test_case in validation_test_cases:
        assert "name" in test_case
        assert "data" in test_case
        assert "expected" in test_case
        assert "description" in test_case


@pytest.mark.smoke
def test_security_test_payloads(security_test_payloads):
    """Test that security test payloads fixture works."""
    assert isinstance(security_test_payloads, list)
    assert len(security_test_payloads) > 0
    
    # Check for expected dangerous patterns
    payloads_str = " ".join(security_test_payloads)
    assert "DROP TABLE" in payloads_str
    assert "<script>" in payloads_str
    assert "../../" in payloads_str


@pytest.mark.smoke
def test_environment_variables(environment_variables):
    """Test that environment variables fixture works."""
    assert isinstance(environment_variables, dict)
    assert "TEST_MODE" in environment_variables
    assert environment_variables["TEST_MODE"] == "true"
    assert "PYTEST_RUNNING" in environment_variables
    assert environment_variables["PYTEST_RUNNING"] == "true"


@pytest.mark.smoke
def test_processor_config(processor_test_config):
    """Test that processor test configuration fixture works."""
    assert isinstance(processor_test_config, dict)
    assert "timeout" in processor_test_config
    assert "max_file_size" in processor_test_config
    assert "allowed_extensions" in processor_test_config
    assert "security_scan" in processor_test_config
    assert "validation_rules" in processor_test_config


@pytest.mark.smoke
def test_test_helpers_import():
    """Test that test helper modules can be imported."""
    try:
        from tests.utils import test_helpers
        from tests.utils import assertions
        from tests.utils.fixtures import load_fixture_data, FixtureManager, fixture_manager
        
        # Test some basic functions exist
        assert hasattr(test_helpers, 'create_temp_file')
        assert hasattr(assertions, 'assert_yaml_structure')
        
        # Test that we can use the functions
        assert callable(load_fixture_data)
        assert isinstance(FixtureManager(), FixtureManager)
        assert isinstance(fixture_manager, FixtureManager)
        
    except ImportError as e:
        pytest.fail(f"Failed to import test helper modules: {e}")


@pytest.mark.smoke  
def test_custom_assertions():
    """Test that custom assertions work correctly."""
    from tests.utils.assertions import (
        assert_yaml_structure, 
        assert_yaml_valid,
        assert_security_safe
    )
    
    # Test YAML structure assertion
    test_data = {"name": "test", "command": "echo test"}
    assert_yaml_structure(test_data, ["name", "command"])
    
    # Test YAML validation
    valid_yaml = "key: value\nlist:\n  - item1\n  - item2"
    result = assert_yaml_valid(valid_yaml)
    assert result["key"] == "value"
    assert result["list"] == ["item1", "item2"]
    
    # Test security assertion  
    safe_content = "echo 'Hello, World!'"
    assert_security_safe(safe_content)  # Should not raise


@pytest.mark.smoke
def test_fixture_manager():
    """Test that the fixture manager works correctly."""
    from tests.utils.fixtures import FixtureManager, fixture_manager
    
    # Test creating new manager
    manager = FixtureManager()
    
    # Test getting sample data
    workflows = manager.get_workflows()
    assert isinstance(workflows, list)
    assert len(workflows) > 0
    
    prompts = manager.get_prompts()
    assert isinstance(prompts, list)
    
    notebooks = manager.get_notebooks()
    assert isinstance(notebooks, list)
    
    # Test generating content
    workflow_content = manager.generate_content("workflow")
    assert isinstance(workflow_content, str)
    assert "name:" in workflow_content
    
    # Test global fixture manager instance
    global_workflows = fixture_manager.get_workflows()
    assert isinstance(global_workflows, list)
    assert len(global_workflows) > 0


@pytest.mark.smoke
def test_python_path_setup():
    """Test that Python path is correctly set up for testing."""
    # Check that the src directory is in the path
    src_path = str(Path(__file__).parent.parent / "src")
    assert any(src_path in path for path in sys.path), "src directory not in Python path"


@pytest.mark.smoke
def test_markers_configuration():
    """Test that pytest markers are properly configured."""
    # This test verifies that our custom markers are working
    # The markers themselves are applied to this test function
    pass


# Performance smoke test
@pytest.mark.smoke
@pytest.mark.performance
def test_basic_performance():
    """Basic performance smoke test."""
    import time
    
    start_time = time.time()
    
    # Simulate some work
    for i in range(1000):
        _ = str(i)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # This should complete very quickly
    assert execution_time < 1.0, f"Basic operations too slow: {execution_time:.3f}s"


# Integration smoke test
@pytest.mark.smoke
@pytest.mark.integration 
def test_basic_integration():
    """Basic integration smoke test."""
    try:
        # Test that we can create and use test utilities together
        from tests.utils.test_helpers import TemporaryTestFile
        from tests.utils.assertions import assert_yaml_valid
        import yaml
        
        test_data = {"name": "integration test", "command": "echo test"}
        yaml_content = yaml.dump(test_data, default_flow_style=False)
        
        with TemporaryTestFile(yaml_content, ".yaml") as temp_file:
            content = temp_file.read_text()
            parsed_data = assert_yaml_valid(content)
            assert parsed_data["name"] == "integration test"
            
    except Exception as e:
        pytest.fail(f"Integration test failed: {e}")


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v"])
