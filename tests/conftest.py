import os
import shutil
import tempfile

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


@pytest.fixture
def output_dir(temp_dir):
    """Fixture that creates a temporary output directory."""
    output_path = os.path.join(temp_dir, "output")
    os.makedirs(output_path)
    yield output_path


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
