# Contributing to api-mocker

Thank you for your interest in contributing to api-mocker! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- pip (Python package installer)

### Development Setup

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/your-username/api-mocker.git
   cd api-mocker
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Development Dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify Installation**
   ```bash
   api-mocker --version
   pytest tests/
   ```

## 📋 Development Guidelines

### Code Style

We follow PEP 8 style guidelines with some modifications:

- **Line Length**: 88 characters (using Black formatter)
- **Import Order**: Standard library, third-party, local imports
- **Type Hints**: Required for all function parameters and return values
- **Docstrings**: Use Google-style docstrings

### Code Formatting

We use several tools to maintain code quality:

```bash
# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Check code style with flake8
flake8 src/ tests/

# Run all formatting tools
make format
```

### Type Checking

We use mypy for static type checking:

```bash
# Run type checking
mypy src/

# Run with strict mode
mypy --strict src/
```

### Testing

#### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api_mocker

# Run specific test file
pytest tests/test_core.py

# Run with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

#### Writing Tests

- Use pytest as the testing framework
- Write descriptive test names
- Use fixtures for common setup
- Mock external dependencies
- Test both success and failure cases

Example test:
```python
import pytest
from api_mocker import MockServer, Route, Response

def test_mock_server_creation():
    """Test creating a mock server with basic configuration."""
    routes = [
        Route(
            method="GET",
            path="/api/health",
            response=Response(status_code=200, body={"status": "healthy"})
        )
    ]
    
    server = MockServer(routes=routes)
    assert len(server.routes) == 1
    assert server.routes[0].method == "GET"
    assert server.routes[0].path == "/api/health"

@pytest.fixture
def sample_config():
    """Provide a sample configuration for testing."""
    return {
        "server": {"host": "127.0.0.1", "port": 8000},
        "routes": [
            {
                "method": "GET",
                "path": "/api/health",
                "response": {"status_code": 200, "body": {"status": "healthy"}}
            }
        ]
    }

def test_config_loading(sample_config, tmp_path):
    """Test loading configuration from file."""
    config_file = tmp_path / "test_config.yaml"
    # Write config to file and test loading
    # ... test implementation
```

## 🎯 Contribution Areas

### High Priority
- **Bug Fixes**: Fix reported issues and edge cases
- **Documentation**: Improve README, docstrings, and examples
- **Testing**: Add test coverage for existing features
- **Performance**: Optimize slow operations

### Medium Priority
- **New Features**: Add requested functionality
- **CLI Improvements**: Enhance command-line interface
- **Plugin System**: Develop new plugins
- **Integration**: Add support for more frameworks

### Low Priority
- **UI/UX**: Improve user experience
- **Monitoring**: Add advanced analytics
- **Deployment**: Add Docker and cloud support

## 🐛 Bug Reports

### Before Reporting
1. Check existing issues for duplicates
2. Try the latest version
3. Reproduce the issue in isolation

### Bug Report Template
```markdown
**Description**
Brief description of the issue

**Steps to Reproduce**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**
What you expected to happen

**Actual Behavior**
What actually happened

**Environment**
- OS: [e.g., Ubuntu 20.04]
- Python Version: [e.g., 3.11.0]
- api-mocker Version: [e.g., 0.1.0]

**Additional Information**
- Error messages
- Screenshots
- Configuration files
```

## 💡 Feature Requests

### Before Requesting
1. Check if the feature already exists
2. Consider if it fits the project scope
3. Think about implementation complexity

### Feature Request Template
```markdown
**Feature Description**
Brief description of the requested feature

**Use Case**
Why this feature is needed and how it would be used

**Proposed Implementation**
Optional: How you think it could be implemented

**Alternatives Considered**
Other approaches you've considered

**Additional Context**
Any other relevant information
```

## 🔧 Pull Request Process

### Before Submitting
1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Add tests** for new functionality
5. **Update documentation** if needed
6. **Run the test suite**
   ```bash
   pytest
   make format
   mypy src/
   ```

### Pull Request Guidelines
- **Title**: Clear, descriptive title
- **Description**: Explain what and why, not how
- **Tests**: Include tests for new features
- **Documentation**: Update docs if needed
- **Breaking Changes**: Clearly mark and explain

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Added tests for new functionality
- [ ] All tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly marked)

## Related Issues
Closes #123
```

## 🏗️ Architecture Overview

### Project Structure
```
api-mocker/
├── src/api_mocker/          # Main package
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── core.py             # Core mocking engine
│   ├── server.py           # FastAPI server
│   ├── config.py           # Configuration management
│   ├── openapi.py          # OpenAPI import/export
│   ├── recorder.py         # Request recording
│   └── plugins.py          # Plugin system
├── tests/                  # Test suite
├── examples/               # Example configurations
├── docs/                   # Documentation
└── pyproject.toml         # Project configuration
```

### Key Components

#### Core Engine (`core.py`)
- Route matching and handling
- Response generation
- Template processing
- Middleware execution

#### Server (`server.py`)
- FastAPI application setup
- Request/response handling
- CORS and middleware integration

#### CLI (`cli.py`)
- Command-line interface
- Subcommand handling
- Configuration management

#### Configuration (`config.py`)
- YAML/JSON/TOML parsing
- Configuration validation
- Default value handling

## 🔌 Plugin Development

### Creating a Plugin

1. **Create Plugin Structure**
   ```python
   # plugins/my_plugin.py
   from api_mocker.plugins import Plugin
   
   class MyPlugin(Plugin):
       name = "my_plugin"
       version = "1.0.0"
       
       def setup(self, config):
           """Initialize plugin with configuration."""
           pass
       
       def process_request(self, request):
           """Process incoming request."""
           return request
       
       def process_response(self, response):
           """Process outgoing response."""
           return response
   ```

2. **Register Plugin**
   ```python
   # In your plugin file
   from api_mocker.plugins import register_plugin
   
   register_plugin(MyPlugin)
   ```

3. **Add Tests**
   ```python
   def test_my_plugin():
       plugin = MyPlugin()
       plugin.setup({})
       # Test plugin functionality
   ```

### Plugin Guidelines
- Follow the Plugin base class interface
- Include comprehensive tests
- Document configuration options
- Handle errors gracefully
- Use type hints

## 📚 Documentation

### Documentation Standards
- Use clear, concise language
- Include code examples
- Keep examples up-to-date
- Use consistent formatting

### Documentation Structure
- **README.md**: Project overview and quick start
- **docs/QUICKSTART.md**: Detailed getting started guide
- **docs/API.md**: API reference
- **docs/CONFIGURATION.md**: Configuration options
- **docs/PLUGINS.md**: Plugin development guide

### Updating Documentation
1. Update relevant documentation files
2. Ensure examples work with current code
3. Test documentation examples
4. Update version numbers and dates

## 🚀 Release Process

### Version Management
We use semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version bumped in pyproject.toml
- [ ] CHANGELOG.md updated
- [ ] Release notes prepared
- [ ] PyPI package built and uploaded

## 🤝 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Help others learn and grow
- Provide constructive feedback
- Follow project guidelines

### Communication
- Use GitHub Issues for bug reports
- Use GitHub Discussions for questions
- Be clear and specific in communications
- Respond to feedback promptly

### Recognition
- Contributors will be listed in CONTRIBUTORS.md
- Significant contributions will be acknowledged in release notes
- Contributors may be invited to join the maintainer team

## 🆘 Getting Help

### Resources
- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-username/api-mocker/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/api-mocker/discussions)
- **Email**: support@api-mocker.com

### Common Issues
- **Installation Problems**: Check Python version and dependencies
- **Configuration Issues**: Validate YAML syntax and schema
- **Performance Issues**: Check server configuration and resources
- **Plugin Problems**: Verify plugin compatibility and configuration

## 📄 License

By contributing to api-mocker, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to api-mocker! Your contributions help make this tool better for everyone. 🎉 