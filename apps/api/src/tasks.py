"""Background tasks exposed via Celery.

Each task is also runnable in-process: when ``REDIS_URL`` is not configured,
``celery_app`` is created with ``task_always_eager=True`` so ``.delay()`` and
``.apply_async()`` calls run synchronously without a worker.

Tasks own their own database session (opened with ``SessionLocal``) because
they may run inside a Celery worker process where FastAPI's request-scoped
``get_db`` dependency isn't available.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from .celery_app import celery_app
from .database import SessionLocal


@celery_app.task(name="applymap.generate_report")
def generate_report_task(report_id: str) -> dict:
    """Run optimization + rewrite generation for a single report.

    Returns ``{"report_id": ..., "status": "completed" | "failed"}``.
    Errors are caught and persisted on the report row; the caller polls the
    report's ``status`` field rather than the task result.
    """
    from .routes.reports import _run_report_generation

    db = SessionLocal()
    try:
        _run_report_generation(db, UUID(report_id))
        db.refresh_all = None  # type: ignore[attr-defined]
        return {"report_id": report_id, "status": "completed"}
    except Exception as exc:  # noqa: BLE001
        return {"report_id": report_id, "status": "failed", "error": str(exc)}
    finally:
        db.close()


@celery_app.task(name="applymap.seed_scholarships")
def seed_scholarships_task() -> dict:
    """Re-run the idempotent scholarship seed loader from a worker."""
    from .seeds.seed_scholarships import seed_scholarships

    db = SessionLocal()
    try:
        inserted = seed_scholarships(db)
        return {"status": "completed", "inserted": int(inserted)}
    finally:
        db.close()


@celery_app.task(name="applymap.ocr_file")
def ocr_file_task(file_path: str, language: Optional[str] = None) -> dict:
    """Run OCR on a file already saved to disk by the request handler.

    The OCR module itself is optional — if ``pytesseract`` is missing in the
    worker image we surface a ``needs_manual_entry`` payload so the caller
    can fall back to the manual-input form.
    """
    try:
        from .services.ocr_service import ocr_image_file  # type: ignore[import-not-found]

        result = ocr_image_file(file_path, language=language)
        return {"status": "completed", **result}
    except ImportError:
        return {
            "status": "completed",
            "needs_manual_entry": True,
            "reason": "ocr_dependencies_missing",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "completed",
            "needs_manual_entry": True,
            "reason": "ocr_runtime_error",
            "error": str(exc),
        }
