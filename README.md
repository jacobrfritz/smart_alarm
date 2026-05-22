# base_python_project

A robust default Python project template using `uv`.

## Setup

This project uses `uv` for dependency management and includes a bootstrapping script to quickly get you started.

To bootstrap the project, run:

```bash
python bootstrap.py
```

The bootstrap script will:
- **Check for `uv`**: Automatically installs [uv](https://github.com/astral-sh/uv) if it's not already on your system.
- **Rename Project**: Guides you through renaming the project and its Python package from the default `base_python_project`.
- **Sync Dependencies**: Installs project dependencies and allows you to select optional extras (e.g., `data`, `ml`, `api`).
- **Reset Git**: Optionally clears the template's git history and initializes a new repository for your project.

## Usage

Common development tasks are managed via the `Makefile`. You can run these commands using `make <command>`.

| Command | Description |
| :--- | :--- |
| `make install` | Sync dependencies using `uv`. |
| `make run` | Run the application CLI. |
| `make test` | Run the test suite with `pytest`. |
| `make test-watch` | Run tests in watch mode using `pytest-watch`. |
| `make test-cov` | Run tests and generate a coverage report. |
| `make lint` | Check code style and quality with `ruff`. |
| `make format` | Format code using `ruff`. |
| `make typecheck` | Run static type analysis with `mypy`. |

Alternatively, you can run these directly via `uv`, for example: `uv run pytest`.

## Project Structure

```text
.
├── .editorconfig
├── .gitignore
├── .pre-commit-config.yaml
├── Makefile
├── README.md
├── bootstrap.py
├── pyproject.toml
├── uv.lock
├── src/
│   └── base_python_project/
│       ├── __init__.py
│       ├── cli.py
│       └── main.py
└── tests/
    ├── __init__.py
    └── test_main.py
```

- `src/`: Core application logic.
- `tests/`: Project tests.
- `pyproject.toml`: Project metadata and dependencies.
- `bootstrap.py`: Interactive setup script.
- `Makefile`: Shortcuts for common tasks.
