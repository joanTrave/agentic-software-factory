#!/bin/sh
set -eu

alembic upgrade head
exec gunicorn "src.app:app" --config gunicorn.conf.py
