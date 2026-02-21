# Notes for Claude

## Tooling

* `uv` for dependency management (`uv add`, `uv run`, `uv sync`)
* `ruff` for formatting/linting (`ruff format`, `ruff check --fix`)
* `pytest` for testing (`uv run pytest`)
* Always format before committing

## Code Style

* Double quotes for strings
* Type hints on function signatures
* PEP 8, simple and readable, no over-engineering

## Project Structure

* `nimc/` — Main module (empty)
* `nimc/core/` — Core functionality (hcloud integration, server models)
* `nimc/web/` — FastAPI web UI
* `nimc/cli/` — CLI interface
* `servers/` — Server config directories (each has `server.toml`, `cloud-config.yaml`, `files/`)
* `server_skeleton/` — A skeleton for a server config directory. If server is missing a file, it will be fetched from here.
* `tests/` — pytest tests (`test_*.py`)
