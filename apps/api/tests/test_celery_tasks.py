"""Tests for the optional Celery task layer.

These tests run without a real Redis broker — ``celery_app`` is configured
with ``task_always_eager=True`` whenever ``REDIS_URL`` is not set, so
``.delay()`` calls execute the task body inline.
"""
from __future__ import annotations

import os
from unittest import mock

import pytest


@pytest.fixture(autouse=True)
def _clear_redis_env(monkeypatch):
    """Make sure ``REDIS_URL`` is unset so eager mode is on."""
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("CELERY_BROKER_URL", raising=False)
    yield


def test_broker_not_configured_when_redis_env_missing():
    # Re-import so module-level config sees the cleared env vars.
    import importlib

    from src import celery_app

    importlib.reload(celery_app)
    assert celery_app.broker_configured() is False
    assert celery_app.celery_app.conf.task_always_eager is True


def test_seed_scholarships_task_calls_loader():
    """``seed_scholarships_task`` should invoke the idempotent loader."""
    import importlib

    from src import celery_app, tasks

    importlib.reload(celery_app)
    importlib.reload(tasks)

    fake_session = mock.MagicMock(name="session")
    SessionLocal = mock.MagicMock(return_value=fake_session)
    seed = mock.MagicMock(return_value=7)

    with mock.patch.object(tasks, "SessionLocal", SessionLocal), mock.patch(
        "src.seeds.seed_scholarships.seed_scholarships", seed
    ):
        result = tasks.seed_scholarships_task.run()  # type: ignore[attr-defined]

    SessionLocal.assert_called_once_with()
    seed.assert_called_once_with(fake_session)
    fake_session.close.assert_called_once()
    assert result == {"status": "completed", "inserted": 7}


def test_generate_report_task_delegates_to_run_report_generation():
    import importlib
    from uuid import uuid4

    from src import celery_app, tasks

    importlib.reload(celery_app)
    importlib.reload(tasks)

    fake_session = mock.MagicMock(name="session")
    SessionLocal = mock.MagicMock(return_value=fake_session)
    run_fn = mock.MagicMock()

    rid = uuid4()
    with mock.patch.object(tasks, "SessionLocal", SessionLocal), mock.patch(
        "src.routes.reports._run_report_generation", run_fn
    ):
        result = tasks.generate_report_task.run(str(rid))  # type: ignore[attr-defined]

    SessionLocal.assert_called_once_with()
    args, _ = run_fn.call_args
    assert args[0] is fake_session
    assert str(args[1]) == str(rid)
    fake_session.close.assert_called_once()
    assert result == {"report_id": str(rid), "status": "completed"}


def test_generate_report_task_reports_failure():
    import importlib
    from uuid import uuid4

    from src import celery_app, tasks

    importlib.reload(celery_app)
    importlib.reload(tasks)

    fake_session = mock.MagicMock(name="session")
    SessionLocal = mock.MagicMock(return_value=fake_session)
    run_fn = mock.MagicMock(side_effect=RuntimeError("boom"))

    rid = uuid4()
    with mock.patch.object(tasks, "SessionLocal", SessionLocal), mock.patch(
        "src.routes.reports._run_report_generation", run_fn
    ):
        result = tasks.generate_report_task.run(str(rid))  # type: ignore[attr-defined]

    assert result["status"] == "failed"
    assert "boom" in result["error"]
    fake_session.close.assert_called_once()


def test_ocr_task_returns_manual_entry_fallback_when_ocr_missing():
    """If pytesseract or opencv are unavailable, the task surfaces a
    structured fallback instead of crashing the worker."""
    import importlib

    from src import celery_app, tasks

    importlib.reload(celery_app)
    importlib.reload(tasks)

    # Force the lazy import to raise ImportError.
    with mock.patch.dict(
        "sys.modules", {"src.services.ocr_service": None}
    ):
        result = tasks.ocr_file_task.run("/tmp/does-not-exist.png")  # type: ignore[attr-defined]

    assert result["status"] == "completed"
    assert result["needs_manual_entry"] is True
    assert result["reason"] in {
        "ocr_dependencies_missing",
        "ocr_runtime_error",
    }


def test_broker_configured_when_redis_url_set(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://example:6379/0")
    import importlib
    from src import celery_app

    importlib.reload(celery_app)
    try:
        assert celery_app.broker_configured() is True
        assert celery_app.celery_app.conf.task_always_eager is False
    finally:
        monkeypatch.delenv("REDIS_URL", raising=False)
        importlib.reload(celery_app)


def test_celery_app_module_imports_without_error():
    """Sanity check — module-level import should never explode at import time
    regardless of env state (used by the API process at startup)."""
    import importlib

    from src import celery_app

    importlib.reload(celery_app)
    assert celery_app.celery_app.main == "applymap"
