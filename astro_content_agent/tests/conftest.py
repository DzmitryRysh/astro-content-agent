from __future__ import annotations

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from astro_content_agent.db.base import Base
from astro_content_agent.db.models import BrandProfile
from astro_content_agent.db.session import get_db
from astro_content_agent.main import create_app


@pytest.fixture()
def test_engine():
    # Use StaticPool so the in-memory DB is shared across connections/threads.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture()
def db_session(test_engine) -> Generator[Session, None, None]:
    TestingSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False, class_=Session)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    app = create_app()

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    return TestClient(app)


@pytest.fixture()
def brand_profile(db_session: Session) -> BrandProfile:
    bp = BrandProfile(id=str(uuid.uuid4()), name="Test Brand")
    db_session.add(bp)
    db_session.commit()
    db_session.refresh(bp)
    return bp

