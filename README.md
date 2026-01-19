# Syntasa Function Template

A template repository for building, testing, and deploying custom Syntasa functions.

---

## 🎯 Purpose

This template provides a structured starting point for developing custom data processing functions. It includes:

- Pre-configured project structure
- Example function implementation
- Unit and integration test templates
- CI/CD workflow for automated testing
- Dependency management with Poetry

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11
- Poetry

### 1. Clone and Setup

```bash
# Clone the template repository
git clone <your-repo-url>
cd syntasa-template-repo

# Install Poetry (if not already installed)
pip install poetry

# Install dependencies
poetry install
```

### 2. Authenticate to Syntasa Package Repository

**Option 1: Using pip (for local development)**
```bash
pip install keyrings.google-artifactregistry-auth

```

**Option 2: Using Poetry (recommended)**
```bash
# Poetry is configured to use syntasa-lib ^1.1.8 (latest compatible)
poetry install
```

### 3. Configure Your Function

The template supports two configuration methods:

**Option 1: Environment Variables (.env file)**

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your configuration:
   ```bash
   GCP_PROJECT_ID=your-project-id
   DATASET_ID=your_dataset
   TABLE_ID=your_table
   BATCH_SIZE=100
   ```

3. Load in your code:
   ```python
   from my_function.config import FunctionConfig
   config = FunctionConfig.from_env()
   ```

**Option 2: YAML Configuration (config.yaml)**

1. Copy the example file:
   ```bash
   cp config.example.yaml config.yaml
   ```

2. Edit `config.yaml`:
   ```yaml
   gcp:
     project_id: your-project-id
     dataset_id: your_dataset
     table_id: your_table
   processing:
     batch_size: 100
   ```

3. Load in your code:
   ```python
   from my_function.config import FunctionConfig
   config = FunctionConfig.from_yaml("config.yaml")
   ```

### 4. Build Your Function

The template includes a sample function in `functions/my_function/`. Replace this with your own implementation:

1. **Update `functions/my_function/main.py`** with your data processing logic
2. **Update `functions/my_function/config.py`** with your configuration parameters
3. **Update tests** in `functions/tests/`

---

## 🧪 Testing

### Run All Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=functions/my_function --cov-report=term-missing
```

### Run Specific Test Suites

```bash
# Unit tests only
poetry run pytest functions/tests/unit/

# Integration tests only
poetry run pytest functions/tests/integration/
```

### Linting and Type Checking

```bash
# Lint code
poetry run ruff check functions/

# Format code
poetry run black functions/

# Type check
poetry run mypy functions/my_function
```

---

## 📦 Project Structure

```
syntasa-template-repo/
├── functions/
│   ├── my_function/          # Your function implementation
│   │   ├── __init__.py
│   │   ├── main.py          # Main function logic
│   │   └── config.py        # Configuration handling
│   └── tests/
│       ├── unit/            # Unit tests
│       │   └── test_my_function.py
│       ├── integration/     # Integration tests
│       │   └── test_integration.py
│       └── conftest.py      # Pytest configuration
├── .github/
│   └── workflows/
│       └── ci.yml           # CI/CD pipeline
├── pyproject.toml           # Poetry dependencies
├── poetry.lock              # Locked dependencies
└── README.md                # This file
```

---

## 🔄 CI/CD Workflow

The repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that automatically:

1. **Installs Dependencies** - Sets up Python 3.11 and installs all dependencies including latest syntasa-lib
2. **Runs Linting** - Checks code quality with ruff and black
3. **Type Checks** - Validates types with mypy
4. **Runs Tests** - Executes both unit and integration tests with coverage reporting
5. **Generates Documentation** - Creates function documentation from code
6. **Publishes to Confluence** - Updates Confluence documentation (main branch only)

### Triggering CI

CI runs automatically on:
- Pull requests to any branch
- Pushes to the `main` branch

---

## �️ Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/my-new-feature
```

### 2. Implement Your Changes

- Update function code in `functions/my_function/`
- Add/update tests in `functions/tests/`
- Run tests locally to verify

### 3. Run CI Locally (Before Push)

```bash
# Install dependencies
poetry install

# Run linting
poetry run ruff check functions/
poetry run black --check functions/

# Run type checking
cd functions && poetry run mypy my_function && cd ..

# Run tests
poetry run pytest functions/tests/ -v
```

### 4. Commit and Push

```bash
git add .
git commit -m "Add: description of changes"
git push origin feature/my-new-feature
```

### 5. Create Pull Request

- Open a PR to `main` branch
- CI will run automatically
- Merge when CI passes ✅

---

## 🔧 Configuration

### Environment Variables

Configure your function using environment variables or the `config.py` module:

```python
from my_function.config import FunctionConfig

# Load from environment
config = FunctionConfig.from_env()
```

### Example `.env` File

```bash
GCP_PROJECT_ID=my-project
DATASET_ID=my_dataset
TABLE_ID=my_table
BATCH_SIZE=100
```

---

## � Adding Dependencies

To add new dependencies to your function:

```bash
# Add a runtime dependency
poetry add <package-name>

# Add a development dependency
poetry add --group dev <package-name>

# Update lock file
poetry lock
```

---

## � Deployment

**Note**: This template is for function development. Deployment strategies depend on your Syntasa platform setup:

- Cloud Functions
- Cloud Run
- Kubernetes Jobs
- Airflow DAGs

Consult your platform documentation for specific deployment instructions.

---

## 📖 Additional Resources

- [Poetry Documentation](https://python-poetry.org/docs/)
- [pytest Documentation](https://docs.pytest.org/)

---

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Ensure all tests pass locally
4. Submit a pull request
5. Wait for CI to pass

---

## 📄 License

Copyright © Syntasa Data Platform
