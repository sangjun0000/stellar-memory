# Contributing to Stellar Memory

Thank you for your interest in contributing to Stellar Memory!

## Development Setup

```bash
# Clone the repository
git clone https://github.com/stellar-memory/stellar-memory.git
cd stellar-memory

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install in development mode
pip install -e .[dev]

# Run tests
pytest
```

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=stellar_memory --cov-report=term-missing

# Specific test file
pytest tests/test_stellar.py -v
```

## Code Style

- Python 3.10+ with type hints
- Use `from __future__ import annotations` for forward references
- Clear, descriptive names; comments only when logic isn't self-evident
- Follow existing patterns in the codebase

## Project Structure

```
stellar_memory/          # Source code
  stellar.py            # Core StellarMemory class
  config.py             # Configuration dataclasses
  models.py             # Data models
  orbit_manager.py      # Zone management
  memory_function.py    # Importance scoring
  ...
tests/                   # Test files
  test_stellar.py       # Core tests
  ...
examples/               # Example projects
docs/                   # Documentation
```

## Pull Request Process

1. Fork the repository and create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass: `pytest`
4. Update documentation if needed
5. Submit a pull request with a clear description

## Reporting Issues

Please include:
- Python version
- Stellar Memory version (`stellar-memory --version` or `python -c "import stellar_memory; print(stellar_memory.__version__)"`)
- Steps to reproduce
- Expected vs actual behavior

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
