## Contributing to PolicyGraph

We welcome contributions from security researchers, machine learning engineers, and open-source enthusiasts! This guide explains how to contribute effectively.

### Code of Conduct

- Be respectful and inclusive
- Focus on the code, not the person
- Help others learn and grow
- Report issues in private, not public shaming

### Ways to Contribute

#### 1. Bug Reports & Feature Requests

**Reporting Bugs:**
1. Check if the bug has already been reported (search Issues)
2. Create a new Issue with:
   - Clear title describing the bug
   - Step-by-step reproduction instructions
   - Expected vs. actual behavior
   - Environment: Python version, OS, dependencies
   - Error traceback (if applicable)

**Requesting Features:**
1. Describe the feature and use case
2. Explain why it's valuable
3. Provide examples if possible
4. Link to related issues/PRs

#### 2. Code Contributions

**Getting Started:**
```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/PolicyGraph.git
cd PolicyGraph

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Create a feature branch
git checkout -b feature/your-feature-name
```

**Code Standards:**

1. **Style & Formatting**
   - Follow PEP 8
   - Use Black for code formatting
   - Use ruff for linting
   - 100-character line limit

2. **Type Hints**
   - Add type hints to all functions
   - Use `from __future__ import annotations` for forward references
   - Run mypy for type checking

3. **Documentation**
   - Write docstrings for all public functions/classes
   - Use Google-style docstrings
   - Update README if adding new features
   - Add examples for new functionality

4. **Testing**
   - Write unit tests for new code
   - Maintain >80% test coverage
   - Run: `pytest tests/ -v --cov=policygraph`

5. **Logging**
   - Add logging statements for important events
   - Use appropriate levels: DEBUG, INFO, WARNING, ERROR
   - Logger: `logger = logging.getLogger(__name__)`

**Example Function with Documentation:**
```python
def analyze_policy(
    self, 
    policy_input: Union[str, Path, Dict[str, Any]]
) -> Dict[str, Any]:
    """Analyze a single IAM policy and return risk assessment.
    
    Analyzes an IAM policy using the trained GNN model combined with
    heuristic pattern matching. Returns a comprehensive risk report.
    
    Args:
        policy_input: Policy JSON file path, pathlib.Path, or dictionary.
        
    Returns:
        Dictionary containing:
            - risk_score (float): 0.0-1.0 risk score
            - prediction (int): 0 (secure) or 1 (vulnerable)
            - vulnerabilities_detected (list): Identified patterns
            - attack_paths (list): Potential escalation chains
            - explanation (dict): Model reasoning
            
    Raises:
        PolicyParsingError: If policy JSON is invalid or file not found
        
    Example:
        >>> analyzer = PolicyAnalyzer(model_path="model.pt")
        >>> result = analyzer.analyze_policy("policy.json")
        >>> print(f"Risk: {result['risk_score']:.2%}")
    """
    ...
```

**Pull Request Process:**

1. **Before Submitting:**
   ```bash
   # Format code
   black policygraph tests
   ruff check --fix policygraph tests
   
   # Type check
   mypy policygraph --ignore-missing-imports
   
   # Run tests
   pytest tests/ -v --cov=policygraph
   
   # Run pre-commit hooks
   pre-commit run --all-files
   ```

2. **Submit PR:**
   - Clear title: `feat: add GCN model option` or `fix: resolve graph building edge case`
   - Detailed description of changes
   - Reference related issues: `Fixes #123`
   - Add screenshots/GIFs if UI-related
   - Check "Allow edits from maintainers"

3. **PR Review Process:**
   - Address feedback constructively
   - Push new commits (don't force push)
   - Re-request review when ready
   - Squash commits before merge if requested

#### 3. Dataset Contributions

We welcome labeled IAM policies to expand the training dataset!

**Submitting Policies:**
1. Ensure policies are anonymized (no real ARNs/account IDs)
2. Create a JSON file following this format:
   ```json
   {
       "Statement": [
           {
               "Effect": "Allow",
               "Action": ["iam:PassRole", "lambda:CreateFunction"],
               "Resource": "*"
           }
       ]
   }
   ```
3. Provide labels in `LABELS.json` format:
   ```json
   {
       "policy_file.json": {
           "vulnerable": true,
           "severity": "high",
           "vulnerability_type": "privilege_escalation",
           "attack_chain": "PassRole + Lambda"
       }
   }
   ```
4. Submit via Pull Request with detailed documentation

#### 4. Documentation Contributions

- Fix typos and clarify explanations
- Add examples and tutorials
- Improve API documentation
- Translate documentation (future)
- Create architecture diagrams

#### 5. Research & Publication

Help advance IAM security research:
- Share novel vulnerability patterns
- Propose new detection techniques
- Benchmark against other tools
- Publish findings (cite PolicyGraph)

### Development Workflow

**Local Testing:**
```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_analyzer.py::test_policy_analysis -v

# Run with coverage
pytest tests/ --cov=policygraph --cov-report=html

# Run linting
ruff check policygraph/
black --check policygraph/

# Type checking
mypy policygraph/

# All checks at once
make test  # (if Makefile exists)
```

**Debugging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Then run your code, detailed logs will show
```

### Architecture & Design Principles

Before contributing, familiarize yourself with:
- See `docs/ARCHITECTURE.md` for system design
- Review `setup.py` for dependencies and constraints
- Check `config.yaml` for configuration options
- Read recent PRs to understand ongoing work

**Design Philosophy:**
- **Simplicity over cleverness** — Code should be readable
- **Explicit over implicit** — Clear intent and behavior
- **Small datasets work best** — Account for limited training data
- **Hybrid models are better** — Combine neural + heuristic approaches
- **Fail gracefully** — Meaningful error messages

### Release Process

Only maintainers handle releases, but here's how it works:
1. Update version in `__init__.py` and `setup.py`
2. Update `CHANGELOG.md` with new features/fixes
3. Create release branch: `release/v0.2.0`
4. Tag with git: `git tag -a v0.2.0 -m "Release 0.2.0"`
5. Build and publish to PyPI (when ready)

### Getting Help

- **Questions:** Open a Discussion (GitHub)
- **Bugs:** Open an Issue with reproduction steps
- **Ideas:** Start a Discussion or open an Issue marked `enhancement`
- **Security Issues:** Email maintainers privately (don't open public issues)

### Resources

- [GitHub Flow Guide](https://guides.github.com/introduction/flow/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Google Docstring Format](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- [Type Hints in Python](https://docs.python.org/3/library/typing.html)

### Maintainers

- **Joshua** - Project lead, architecture decisions, releases

### Thank You!

Every contribution helps improve IAM security. Whether it's code, documentation, bug reports, or ideas—we appreciate your efforts!

---

**Happy coding! 🚀**
