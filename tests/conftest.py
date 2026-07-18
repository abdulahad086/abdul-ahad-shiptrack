import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup a default API_KEY env var if it's missing or empty before settings is loaded
if not os.environ.get("API_KEY") or os.environ.get("API_KEY").strip() == "":
    os.environ["API_KEY"] = "test-key"

# Setup a default AUDIT_LOG_PATH env var if missing
if not os.environ.get("AUDIT_LOG_PATH"):
    os.environ["AUDIT_LOG_PATH"] = "/tmp/test_audit.log"

from app.config import settings
from app.database import Base, get_db
from app.main import app


@pytest.fixture(scope="function")
def db_session():
    # Use the database URL from settings
    engine = create_engine(settings.DATABASE_URL)

    # Recreate tables to have a clean environment for each test
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="function")
def client(db_session):
    # Apply dependency override
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_headers():
    return {"X-API-Key": settings.API_KEY}


@pytest.fixture(scope="function")
def audit_log_path(tmp_path, monkeypatch):
    log_file = tmp_path / "audit.log"
    monkeypatch.setenv("AUDIT_LOG_PATH", str(log_file))
    # Override settings directly to make sure in-memory settings uses the path
    settings.AUDIT_LOG_PATH = str(log_file)
    yield log_file
