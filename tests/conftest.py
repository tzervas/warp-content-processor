import os
import shutil
import tempfile
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def temp_dir():
    """Fixture that creates a temporary directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def source_dir(temp_dir):
    """Fixture that creates a temporary source directory."""
    source_path = os.path.join(temp_dir, "source")
    os.makedirs(source_path)
    yield source_path
    shutil.rmtree(source_path)


@pytest.fixture
def output_dir(temp_dir):
    """Fixture that creates a temporary output directory."""
    output_path = os.path.join(temp_dir, "output")
    os.makedirs(output_path)
    yield output_path


@pytest.fixture
def fixtures_dir():
    """Fixture for accessing the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def messy_content_file(fixtures_dir):
    """Fixture providing the messy_mixed_content.yaml file."""
    return fixtures_dir / "messy_mixed_content.yaml"


@pytest.fixture
def content_processor(output_dir):
    """Fixture providing a ContentProcessor with output directory."""
    from warp_content_processor import ContentProcessor

    return ContentProcessor(output_dir)


@pytest.fixture
def sample_yaml_file(source_dir):
    """Fixture that creates a sample YAML file."""
    yaml_content = {
        "title": "Sample Document",
        "sections": [
            {"name": "Introduction", "content": "This is the introduction."},
            {"name": "Details", "content": "These are the details."},
        ],
    }
    yaml_file = os.path.join(source_dir, "sample.yaml")
    with open(yaml_file, "w") as f:
        yaml.dump(yaml_content, f)
    yield yaml_file


@pytest.fixture
def sample_markdown_file(source_dir):
    """Fixture that creates a sample Markdown file."""
    markdown_content = """# Sample Document

## Introduction
This is the introduction.

## Details
These are the details.
"""
    md_file = os.path.join(source_dir, "sample.md")
    with open(md_file, "w") as f:
        f.write(markdown_content)
    yield md_file
