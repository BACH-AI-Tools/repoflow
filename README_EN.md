# RepoFlow

An automation tool to simplify the complete workflow from local project to GitHub publishing.

[中文文档](README.md) | English

## ✨ Features

**Automated Workflow**
- 🚀 Automatically create new repositories under GitHub organizations
- 📝 Intelligently scan and remove sensitive information (API keys, passwords, etc.)
- 🔄 Automatically commit and push code
- 🏗️ Automatically generate CI/CD Pipeline configurations
- 📦 Support publishing to DockerHub, NPM, PyPI

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Configure GitHub Token on first use:

```bash
python repoflow.py config
```

### Usage

Run in your project directory:

```bash
# Complete workflow
python /path/to/repoflow.py init --org BACH-AI-Tools --repo your-repo-name

# Scan sensitive information only
python /path/to/repoflow.py scan

# Generate Pipeline configuration only
python /path/to/repoflow.py pipeline --type docker
```

## 📚 Commands

### `repoflow config`
Configure RepoFlow (GitHub Token, etc.)

### `repoflow init`
Complete automated publishing workflow

Options:
- `--org` - GitHub organization name
- `--repo` - Repository name (required)
- `--private/--public` - Create private repository (default: public)
- `--pipeline` - Pipeline type (docker, npm, pypi, all)
- `--skip-scan` - Skip sensitive information scanning

### `repoflow scan`
Scan project for sensitive information

### `repoflow pipeline`
Generate CI/CD Pipeline configuration files

## 🔐 Pipeline Support

### Docker
- Auto-build and push to DockerHub
- Required Secrets:
  - `DOCKERHUB_USERNAME`
  - `DOCKERHUB_TOKEN`

### NPM
- Auto-publish Node.js packages
- Required Secrets:
  - `NPM_TOKEN`

### PyPI
- Auto-publish Python packages
- Required Secrets:
  - `PYPI_TOKEN`

## 🔍 Sensitive Information Detection

Automatically detects and warns about:
- API Keys (AWS, GitHub, Generic)
- Passwords
- Tokens
- Private Keys
- Database Credentials
- JWT Tokens

## 📖 Documentation

- [Quick Start Guide (CN)](QUICKSTART_CN.md)
- [Detailed Usage (CN)](USAGE_CN.md)
- [Examples](examples/example_usage.md)
- [Project Templates](examples/project_templates.md)
- [Contributing Guide](CONTRIBUTING.md)

## 🛠️ Development

### Setup Development Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install black flake8 pytest mypy

# Run tests
pytest tests/ -v

# Code formatting
black .

# Linting
flake8 src/ repoflow.py
```

### Project Structure

```
RepoFlow/
├── src/                    # Core modules
│   ├── config_manager.py   # Configuration management
│   ├── github_manager.py   # GitHub API
│   ├── git_manager.py      # Git operations
│   ├── secret_scanner.py   # Secret scanning
│   └── pipeline_generator.py  # Pipeline generation
├── examples/               # Examples and templates
├── tests/                  # Test files
├── repoflow.py            # Main entry point
└── README.md              # Documentation
```

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## 📝 License

[MIT License](LICENSE)

## 🔗 Links

- [GitHub Repository](https://github.com/BACH-AI-Tools/RepoFlow)
- [Report Issues](https://github.com/BACH-AI-Tools/RepoFlow/issues)
- [Changelog](CHANGELOG.md)

---

Made with ❤️ by BACH-AI-Tools

