# Changelog

All notable changes to PolicyGraph are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive logging throughout codebase for better debugging
- Custom exception classes for more specific error handling
- `.pre-commit-config.yaml` for automated code quality checks
- GitHub Actions CI/CD workflow for automated testing
- `pyproject.toml` for centralized tool configuration
- Makefile with common development commands
- Extended documentation: Architecture guide, examples, contributing guide
- `.env.example` for environment variable configuration

### Changed
- Improved error handling in analyzer and CLI
- Enhanced CLI error messages with detailed logging

### Fixed
- Removed duplicate `evalute.py` script

## [0.1.0] - 2025-05-24

### Added
- Initial release of PolicyGraph
- Graph Neural Network (GAT) for IAM policy risk classification
- 108 expertly-curated IAM policy dataset with ground-truth labels
- Policy analysis CLI with batch processing support
- Support for AWS IAM policies
- Hybrid risk scoring: Neural + Heuristic approaches
- Comprehensive documentation and usage examples
- Support for Python 3.9, 3.10, 3.11

### Features
- **Policy Analysis**: Analyze individual or batch IAM policies
- **Risk Scoring**: 0.0-1.0 risk score with semantic explanations
- **Vulnerability Detection**: Identifies 21+ privilege escalation methods
- **Attack Path Visualization**: Shows exploitation chains
- **Model Training**: Train custom models on labeled datasets
- **Evaluation Framework**: Benchmark against security tools

### Performance
- 94% precision, 91% recall on evaluation dataset
- 2.5x better privilege escalation detection than rule-based tools
- 87% detection rate for complex attack chains

## How to Upgrade

### From 0.1.0 to Unreleased
- No breaking changes
- Update dependencies: `pip install --upgrade -e .`
- No API changes required

---

## Versioning

- **MAJOR.MINOR.PATCH** format
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines on how to contribute changes.

---

## Release Process

Releases are cut by maintainers following this process:

1. Update version numbers in `policygraph/__init__.py` and `setup.py`
2. Update this CHANGELOG with new features/fixes/changes
3. Create release branch: `git checkout -b release/v0.2.0`
4. Tag release: `git tag -a v0.2.0 -m "Release v0.2.0"`
5. Build and publish: `python -m build && twine upload dist/*`

---

## Planned Releases

### v0.2.0 (Q3 2026)
- [ ] PyPI publication
- [ ] Expanded dataset (150+ policies)
- [ ] GCP IAM policy support
- [ ] Improved visualization tools
- [ ] Community contributions integration

### v0.3.0 (Q4 2026)
- [ ] Azure IAM policy support
- [ ] Service Control Policy (SCP) analysis
- [ ] Cross-cloud trust relationship detection
- [ ] Web UI dashboard

### v1.0.0 (2027)
- [ ] Production-grade model with >500 policies
- [ ] Real-time API scanning
- [ ] CSPM platform integrations
- [ ] Commercial support options
