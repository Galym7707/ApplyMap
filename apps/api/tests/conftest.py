"""Shared pytest fixtures.

Tests run against an in-memory SQLite database so CI does not need Postgres
to verify the deterministic backend logic. Anything that requires Postgres
features (UUID type, JSONB) must be marked and skipped accordingly.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure relative imports work the same way as in production.
_REPO_API_DIR = Path(__file__).resolve().parents[1]
if str(_REPO_API_DIR) not in sys.path:
    sys.path.insert(0, str(_REPO_API_DIR))

# Set env vars *before* importing the app so settings see them.
# A Postgres-style URL keeps src.database happy because it passes Postgres-only
# pool kwargs to create_engine. The engine is lazy, so no real connection is made.
# Tests run their own SQLite engine via the `sqlite_engine` fixture below.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from src import database  # noqa: E402
from src.database import Base  # noqa: E402
import src.models  # noqa: F401,E402  - register model metadata


@pytest.fixture(scope="session")
def sqlite_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture()
def db_session(sqlite_engine):
    Session = sessionmaker(bind=sqlite_engine, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
