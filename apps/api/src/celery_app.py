"""Optional Celery + Redis background-task layer.

If REDIS_URL is set, tasks are dispatched to a Celery worker (deploy with
``celery -A src.celery_app worker``). If REDIS_URL is *not* set (e.g. the
single-container Hugging Face Space deployment), task functions still run
synchronously inside the request handler — the FastAPI routes call
``task.run()`` directly so the product works without any broker.

The point of this module is to give heavier endpoints (report generation,
OCR on large PDFs, scholarship/university seeding) a path to async execution
without forcing every deployment to run Redis.
"""
from __future__ import annotations

import os
from typing import Optional

from celery import Celery


def _broker_url() -> Optional[str]:
    """Return the Redis broker URL, or None to mean ``run inline``."""
    url = os.environ.get("REDIS_URL") or os.environ.get("CELERY_BROKER_URL")
    return url or None


broker = _broker_url()

celery_app = Celery(
    "applymap",
    broker=broker or "memory://",
    backend=broker or "cache+memory://",
    include=["src.tasks"],
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # When no Redis is configured, run tasks in-process. This makes every
    # ``.delay()`` call equivalent to a normal function call so the API works
    # the same whether or not a worker is running.
    task_always_eager=broker is None,
    task_eager_propagates=broker is None,
)


def broker_configured() -> bool:
    """True when a real broker is configured (i.e. async dispatch is active)."""
    return broker is not None
