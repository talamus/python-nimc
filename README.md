# NIMC - On Demand Server Creation and Destruction in Hetzner Cloud

## Project Structure

The project has three components, each with its own set of dependencies:

- **`nimc/`** — Base module
- **`nimc/core/`** — Main functionality
- **`nimc/web/`** — Web UI built with FastAPI / Gunicorn
- **`nimc/cli/`** — Command line interface built with Click

Dependencies are managed as optional extras in `pyproject.toml`.

## Quick Start

```bash
# Install dependencies for the web UI
uv sync --extra web

# Install dependencies for the command line interface
uv sync --extra cli

# Install both cli and web UI
uv sync --all-extras

# Create a user (interactive)
./scripts/create_user

# Create an admin user
./scripts/create_user --username admin --password yourpassword --name "Admin" --admin

# Start the application
./scripts/start_dev
```

Then visit <http://localhost:8000> and log in with your credentials.

## Dependency Management

```bash
# Add a dependency to the main project
uv add <package>

# Add a dependency to a specific user interface
uv add --optional web <package>
uv add --optional cli <package>

# Add a dev dependency (shared across all components)
uv add --dev <package>

# Upgrade all dependencies (Can break things...)
uv sync --all-extras --upgrade
```

## Linting and Formatting

This project uses `ruff` for linting and formatting.

```bash
# Format the codebase
ruff format

# Check for linting issues
ruff check

# Auto-fix linting issues
ruff check --fix

# Remove unnecessary files, but preserve environment
./scripts/clean_up
```

## Persistent Volume Structure

The persistent volume is expected to be mounted at `/persistent/`.

It is expected to have the following structure:

```
/persistent/     — Mounted volume
 │
 ├── bin/
 │   ├── start_server  — Scripts for server management
 │   ├── stop_server
 │   ├── check_inactivity
 │   │
 │   ├── hcloud  — Symlinks to executables
 │   ├── java
 │   ├── rcon
 │   └── ...
 │
 ├── opt/
 │   ├── hcloud  — Actual optional software lives here
 │   ├── java
 │   ├── rcon
 │   └── ...
 │
 └── server/
     └── ...     — Server content lives here
```

## Locations of Other Files on the Server

`start_server` will read the following file if it exists:
```
/etc/nimc/server.arguments  — Optional arguments for server executable
```

`start_server`, `stop_server` and `check_inactivity` scripts
are maintaining the following files:

```
/run/nimc/server.pid       — PID file that exists when server is running
/run/nimc/server.inactive  — This timestamp file will be created when the server
                             has been inactive for 15 minutes.
```

Logs will be written into:

```
/tmp/check_inactivity.log   — Written by `check_inactivity` run by service user cronjob
/var/log/self_destruct.log  — Written by `self_destruct` run by root user cronjob
```
