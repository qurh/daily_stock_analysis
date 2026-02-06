from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from backend.app.config import get_config

Base = declarative_base()

_engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def _build_engine() -> Engine:
    db_url = get_config().get_db_url()
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(db_url, pool_pre_ping=True, connect_args=connect_args)


def get_engine() -> Engine:
    global _engine, SessionLocal
    if _engine is None:
        _engine = _build_engine()
        SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    return _engine


def get_session_local() -> sessionmaker[Session]:
    get_engine()
    if SessionLocal is None:
        raise RuntimeError("Session factory is not initialized")
    return SessionLocal


def get_db() -> Generator[Session, None, None]:
    session = get_session_local()()
    try:
        yield session
    finally:
        session.close()


def init_database() -> None:
    # Ensure models are imported before create_all.
    from backend.app.models import api_models  # noqa: F401

    Base.metadata.create_all(bind=get_engine())


def reset_database() -> None:
    global _engine, SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    SessionLocal = None
