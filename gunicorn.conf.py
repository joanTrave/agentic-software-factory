"""Gunicorn configuration for `src.app:app` (`entrypoint.sh`)."""

import multiprocessing
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
worker_class = "uvicorn.workers.UvicornWorker"

_MAX_WORKERS = 8
workers = int(os.environ.get("GUNICORN_WORKERS") or min((2 * multiprocessing.cpu_count()) + 1, _MAX_WORKERS))

timeout = int(os.environ.get("GUNICORN_TIMEOUT", "60"))
graceful_timeout = 30
keepalive = 5

# Each worker must build its own engine and session factory. Preloading forks a parent process
# that has already opened TCP sockets/pooled connections, and the forked children sharing those
# pooled connections corrupts them.
preload_app = False

accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s "%(r)s" %(s)s %(D)sus rid=%({x-request-id}i)s'
