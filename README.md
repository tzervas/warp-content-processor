# Warp Content Processor

> ⚠️ **Active Development**: This project is currently in active development. APIs and functionality may change without notice.

A Python-based content processor for Warp Terminal that handles multiple content types including workflows, prompts, notebooks, environment variables, and rules. It validates, normalizes, and organizes content for import into Warp Terminal.

## Features

- Multi-format content processing:
  - Workflows
  - Prompts
  - Notebooks
  - Environment Variables
  - Rules

- Smart content handling:
  - Automatic content type detection
  - Schema validation
  - Content normalization
  - Intelligent file organization
  - Split combined documents
  - Handle mixed content types

- Robust validation:
  - YAML syntax checking
  - Required fields validation
  - Type checking
  - Format validation
  - Smart warnings for potential issues

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/warp-content-processor.git
cd warp-content-processor

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

1. Place your input files in the `input` directory
2. Run the processor:
   ```bash
   python src/main.py
   ```
3. Find processed files in the `output` directory, organized by type:
   ```
   output/
   ├── workflow/
   ├── prompt/
   ├── notebook/
   ├── env_var/
   └── rule/
   ```

## Project Structure

```
warp-content-processor/
├── src/                    # Source code
│   ├── processors/         # Content type processors
│   ├── schema_processor.py # Base processing logic
│   └── main.py            # Main entry point
├── tests/                  # Test suite
│   ├── fixtures/          # Test data
│   └── unit/             # Unit tests
├── examples/              # Example content files
├── docs/                 # Documentation
├── input/               # Directory for files to process
└── output/             # Processed file output
```

## Development

This project uses:

- Python 3.8+
- PyYAML for YAML processing
- pytest for testing

### Running Tests

```bash
pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

### Issue Templates

When creating issues, please use our issue templates:

- **Bug Reports**: Use the Bug Report template for reporting bugs. Include steps to reproduce, expected behavior, and your environment details.
- **Enhancements**: Use the Enhancement Request template for suggesting improvements. This covers feature requests, performance improvements, documentation updates, and more.

The templates will help ensure all necessary information is provided, making it easier for maintainers to understand and address your issue.

## License

[MIT License](LICENSE)

## TODO

- [ ] Add CLI interface with more options
- [ ] Implement batch processing
- [ ] Add support for custom schemas
- [ ] Create detailed documentation
- [ ] Add more example content
- [ ] Implement content validation plugins
