"""Pytest configuration and fixtures for Bingo Market tests.

Provides:
- Async database engine and session fixtures
- Test client setup
- Database cleanup utilities
- Mock services for external dependencies
"""

import asyncio
import pytest
from typing import AsyncGenerator, Generator

import pytest_asyncio
from pytest_asyncio import is_async_test
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy import pool

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings


# Test database URL (use same as dev for integration tests)
TEST_DATABASE_URL = settings.database_url


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create async engine for test database.

    Creates all tables before tests and drops them after.
    Uses the same database URL as the main app for integration tests.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=pool.NullPool,  # Use NullPool to avoid connection cleanup issues
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session_maker(
    async_engine: AsyncEngine,
) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    """Create async session maker."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    yield async_session_maker


@pytest_asyncio.fixture(scope="function")
async def db_session(
    async_session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing.

    Yields an async session and rolls back all changes after the test.
    This ensures test isolation.
    """
    async with async_session_maker() as session:
        yield session
        # Rollback all changes after test
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client.

    Uses httpx.AsyncClient with ASGITransport for proper async testing.
    Overrides database dependency to use test session.
    """
    from app.main import app
    from app.core.database import get_db

    def override():
        yield db_session

    app.dependency_overrides[get_db] = override

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sync_client() -> Generator:
    """Create sync test client for backward compatibility.

    Note: Using sync client with async database may cause event loop issues.
    Prefer using the async client fixture instead.
    """
    from fastapi.testclient import TestClient
    client = TestClient(app)
    yield client
    client.close()


def override_get_db(session: AsyncSession):
    """Create a database dependency override for the given session."""
    async def _override():
        yield session
    return _override


# Helper functions for tests
async def create_test_user(
    session: AsyncSession,
    email: str = "test@example.com",
    phone: str = None,
    password: str = "Test123456",
    role: str = "user",
    status: str = "verified_18plus",
    full_name: str = "Test User",
) -> str:
    """Create a test user and return email."""
    from app.models.user import User
    from app.core.security import get_password_hash

    user = User(
        email=email,
        phone=phone,
        password_hash=get_password_hash(password),
        role=role,
        status=status,
        full_name=full_name,
    )
    session.add(user)
    await session.commit()
    return email


async def create_admin_user_in_db(
    session: AsyncSession,
    email: str = "admin@bingomarket.com",
) -> str:
    """Create an admin user for testing."""
    from app.core.security import get_password_hash
    from app.models.user import User

    # Check if user exists
    from sqlalchemy import select
    result = await session.execute(
        select(User).where(User.email == email)
    )
    if result.scalar_one_or_none():
        return email

    admin = User(
        email=email,
        password_hash=get_password_hash("Admin123456"),
        full_name="Admin User",
        status="verified_18plus",
        role="admin",
    )
    session.add(admin)
    await session.commit()
    return email


async def register_and_login_async(
    client: AsyncClient,
    email: str = "test@example.com",
    password: str = "Test123456",
) -> str:
    """Register and login asynchronously, return access token."""
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "verification_code": "123456",
        }
    )

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        }
    )

    data = response.json()
    return data.get("token", "")
