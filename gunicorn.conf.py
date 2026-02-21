"""Gunicorn configuration for production deployment."""

import multiprocessing
from web.logging import LOG_CONFIG
from web.settings import settings

bind = f"{settings.host}:{settings.port}"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

accesslog = "-"
errorlog = "-"
logconfig_dict = LOG_CONFIG
