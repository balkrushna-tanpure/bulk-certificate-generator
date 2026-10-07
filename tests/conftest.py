import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
import app.database as app_db
import app.services.job_service as job_svc_module
from app.main import app

# Create a dedicated SQLite database for testing
TEST_DB_PATH = Path("./test_certificates.db")
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH}"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    # Setup temporary directory for generated PDFs
    temp_dir = tempfile.TemporaryDirectory()
    settings.STORAGE_DIR = Path(temp_dir.name)
    
    # Point application database references to test engine & sessionmaker
    app_db.engine = test_engine
    app_db.SessionLocal = TestingSessionLocal
    job_svc_module.SessionLocal = TestingSessionLocal

    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    yield
    
    # Teardown
    Base.metadata.drop_all(bind=test_engine)
    temp_dir.cleanup()
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass

@pytest.fixture
def db_session():
    """Provides a transactional session for a test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
