"""Main application module for NIMC Web UI"""

import re
import time
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette_csrf.middleware import CSRFMiddleware

from nimc import __version__
from .settings import settings
from .database import init_db
from .routes import auth, pages

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""

    # Startup:
    logger.info(f"Starting up worker for {settings.app_name} (version {__version__})")
    app.state.startup_time = time.time()
    init_db()

    yield

    # Shutdown:
    logger.info(
        f"Shutting down worker, uptime: {int(time.time() - app.state.startup_time)}s"
    )


if settings.secret_key.get_secret_value() == "Don't use this in production!":
    logger.warning(
        "Using default secret key! Please change the 'secret_key' in your settings for production use."
    )

# Initialize FastAPI app
app = FastAPI(title=settings.app_name, version=__version__, lifespan=lifespan)

# Add CSRF protection middleware
app.add_middleware(
    CSRFMiddleware,
    secret=settings.csrf_secret_key.get_secret_value(),
    cookie_name="csrf_token",
    cookie_samesite="lax",
    cookie_httponly=False,  # Must be False so JavaScript can read it
    header_name="X-CSRF-Token",
    exempt_urls=[re.compile(r"^/health$")],  # Exempt health check from CSRF
)

# Get the app directory path
APP_DIR = Path(__file__).parent

# Mount static files if required
if settings.serve_static_files:
    app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

# Configure Jinja2 templates
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))
templates.env.globals.update(
    {
        "app_name": settings.app_name,
        "app_version": __version__,
    }
)
pages.set_templates(templates)

# Include routers
app.include_router(auth.router)
app.include_router(pages.router)


# Define health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "OK", "uptime": int(time.time() - app.state.startup_time)}
