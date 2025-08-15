# Contributing to Translate-Stream

Thank you for your interest in contributing to translate-stream! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

- Be respectful
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Respect differing viewpoints and experiences

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

When creating a bug report, include:
- Clear and descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- System information (OS, Python version, etc.)
- Relevant logs or error messages

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:
- Clear and descriptive title
- Detailed description of the proposed feature
- Use cases and examples
- Any potential drawbacks or considerations

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Follow the coding style**:
   - Use consistent indentation (4 spaces for Python)
   - Follow PEP 8 style guidelines
   - Add docstrings to functions and classes
   - Keep line length under 100 characters when possible

3. **Make your changes**:
   - Write clear, self-documenting code
   - Add comments for complex logic
   - Update documentation as needed
   - Add tests if applicable

4. **Test your changes**:
   ```bash
   # Run basic syntax check
   python3 -m py_compile src/transcribe/*.py
   
   # Test transcription
   ./translate-stream.sh -i mic -o json
   
   # Test GUI if modified
   cd translation_gui && python main.py
   ```

5. **Commit your changes**:
   - Use clear and meaningful commit messages
   - Reference issue numbers if applicable
   - Example: "Fix audio stream buffer overflow (#123)"

6. **Push to your fork** and submit a pull request

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/robertelee78/translate-stream.git
   cd translate-stream
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r translation_gui/requirements.txt  # For GUI development
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## Code Style Guidelines

### Python Code
- Follow PEP 8
- Use type hints where appropriate
- Write docstrings for all public functions
- Use meaningful variable names
- Avoid global variables

### Example:
```python
def transcribe_audio(
    audio_stream: AsyncGenerator[bytes, None],
    language: str = "auto"
) -> Dict[str, Any]:
    """
    Transcribe audio stream to text.
    
    Args:
        audio_stream: Async generator yielding audio chunks
        language: Language code or "auto" for detection
        
    Returns:
        Dictionary containing transcription results
    """
    # Implementation here
```

### Documentation
- Update README.md for user-facing changes
- Update docstrings for API changes
- Include examples for new features
- Keep language clear and concise

## Testing

While formal tests are not yet implemented, please ensure:
- Your code runs without errors
- Existing functionality is not broken
- Edge cases are handled gracefully
- Error messages are helpful

## Areas for Contribution

### High Priority
- Add unit tests
- Improve error handling
- Optimize performance
- Add more language examples

### Medium Priority
- Enhance GUI features
- Add export capabilities
- Improve documentation
- Add configuration validation

### Low Priority
- Code refactoring
- Additional output formats
- Alternative UI options

## Questions?

If you have questions, feel free to:
- Open an issue for discussion
- Check existing documentation
- Review closed issues for similar questions

## Recognition

Contributors will be recognized in the project's README.md.

Thank you for contributing to translate-stream!
