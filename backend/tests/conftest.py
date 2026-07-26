"""
Shared test fixtures for Colab.ai backend tests.

Provides:
- In-memory SQLite test database
- FastAPI TestClient
- Mock user fixtures
- Auth token generation
"""

import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test env BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./test_colab.db"
os.environ["REDIS_URL"] = "none"
os.environ["ORCHESTRATOR_TYPE"] = "docker"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["GEMINI_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""

from app.database.database import Base, get_db, engine
from app.models.models import User, Session, Participant, Snapshot
from app.models.rbac import Organization, Team, Role, Permission, UserOrganization, UserTeam
from app.auth.security import get_password_hash, create_access_token
from app.main import app


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///:memory:"

from sqlalchemy.pool import StaticPool

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Provide a test database session."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


def override_get_db():
    """Override dependency for test database."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


# ---------------------------------------------------------------------------
# Client fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_user(db_session):
    """Create a test user in the database."""
    user = User(
        id=str(uuid.uuid4()),
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user2(db_session):
    """Create a second test user."""
    user = User(
        id=str(uuid.uuid4()),
        username="testuser2",
        email="test2@example.com",
        hashed_password=get_password_hash("password456"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user):
    """Generate a valid JWT token for test_user."""
    return create_access_token(subject=test_user.id)


@pytest.fixture
def auth_headers(auth_token):
    """Authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def test_session(db_session, test_user):
    """Create a test session in the database."""
    session = Session(
        id=str(uuid.uuid4()),
        os_type="alpine",
    )
    db_session.add(session)

    participant = Participant(
        session_id=session.id,
        user_id=test_user.id,
        username=test_user.username,
    )
    db_session.add(participant)
    db_session.commit()
    db_session.refresh(session)
    return session
