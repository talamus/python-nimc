# Python Project Rules

## Project Setup
- Use `uv` for all dependency management, Python version control and virtual environments
- `uv` is already installed and available
- Use `ruff` for linting and formatting
- Use `pytest` for unit testing

## Code Style
- Use double quotes for strings
- Follow PEP 8 conventions
- Prefer simple, readable solutions over complex ones
- Avoid premature optimization and "future proofing"
- Write code that solves the current problem, not hypothetical future problems

## Dependency Management
- Add dependencies with `uv add <package>`
- Add dev dependencies with `uv add --dev <package>`
- Pin dependencies in `pyproject.toml`
- Use `uv sync` to install dependencies
- Use `uv run <command>` to run commands in the project environment

## Code Formatting and Linting
- Use `ruff format` for code formatting
- Use `ruff check` for linting
- Fix auto-fixable issues with `ruff check --fix`
- Configure ruff in `pyproject.toml`
- Always format code before committing

## Testing
- Write tests using `pytest`
- Place tests in `tests/` directory
- Name test files as `test_*.py`
- Name test functions as `test_*`
- Run tests with `uv run pytest`
- Aim for clear, focused test cases
- Use fixtures when appropriate
- Mock external dependencies

## Python Conventions
- Use type hints for function signatures
- Use descriptive variable and function names
- Keep functions small and focused
- Prefer composition over inheritance
- Use list/dict comprehensions when they improve readability
- Avoid nested comprehensions that reduce clarity

## File Organization
- Keep modules focused and cohesive
- Use `__init__.py` to expose public APIs
- Place configuration in `pyproject.toml`
- Use `.env` files for environment-specific settings (never commit secrets)

## Documentation
- Write docstrings for public functions and classes
- Use clear, concise comments for complex logic
- Keep README.md up to date with setup and usage instructions
- Document the "why" not the "what" in comments

## General Principles
- Explicit is better than implicit
- Simple is better than complex
- Readability counts
- If the implementation is hard to explain, it's a bad idea
- Errors should never pass silently
- Don't repeat yourself (DRY) - but prefer clarity over extreme DRY
- Write code for humans first, computers second
