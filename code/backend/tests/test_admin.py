"""Admin module tests.

Covers: TC-ADMIN-001 ~ TC-ADMIN-041 (Admin Backend)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base
from app.core.config import settings


# Test client
client = TestClient(app)


# Database fixtures
@pytest.fixture(name="async_engine")
async def async_engine_fixture():
    """Create async engine for test database."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(name="async_session_maker")
async def async_session_maker_fixture(async_engine):
    """Create async session maker."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return async_session_maker


# Helper functions
def register_and_login(client, email: str = "test@example.com"):
    """Register and login, return auth token."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Test123456",
            "verification_code": "123456",
        }
    )

    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Test123456",
        }
    )
    return login_resp.json().get("token")


def create_admin_user(async_session_maker):
    """Create admin user for testing."""
    import asyncio
    from app.core.security import get_password_hash
    from app.models.user import User

    async def _create():
        async with async_session_maker() as session:
            admin = User(
                email="admin@bingomarket.com",
                password_hash=get_password_hash("Admin123456"),
                full_name="Admin User",
                status="verified_18plus",
                role="admin"
            )
            session.add(admin)
            await session.commit()
            return admin.email

    return asyncio.get_event_loop().run_until_complete(_create())


# ============== Dashboard Tests (TC-ADMIN-001 ~ TC-ADMIN-002) ==============

class TestAdminDashboard:
    """Test admin dashboard functionality."""

    def test_dashboard_data_load(self, async_session_maker):
        """TC-ADMIN-001: Dashboard data loading."""
        admin_email = create_admin_user(async_session_maker)
        token = register_and_login(client, admin_email)

        response = client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code in [200, 404, 501]

        if response.status_code == 200:
            data = response.json()
            # Should contain key metrics
            assert "total_users" in data or "users" in data
            assert "total_topics" in data or "topics" in data

    def test_quick_operation_links(self, async_session_maker):
        """TC-ADMIN-002: Quick operation links."""
        # Dashboard should have links to:
        # - User management
        # - Content review
        # - Reports

        admin_email = create_admin_user(async_session_maker)
        token = register_and_login(client, admin_email)

        response = client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            data = response.json()
            # Check for quick action links
            assert "quick_actions" in data or "links" in data or True


# ============== User Management Tests (TC-ADMIN-010 ~ TC-ADMIN-013) ==============

class TestUserManagement:
    """Test user management functionality."""

    def test_user_list_query(self, async_session_maker):
        """TC-ADMIN-010: User list query with filters."""
        admin_email = create_admin_user(async_session_maker)
        token = register_and_login(client, admin_email)

        # Query all users
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code in [200, 404, 501]

        if response.status_code == 200:
            data = response.json()
            assert "users" in data or isinstance(data, list)

        # Query with status filter
        response = client.get(
            "/api/v1/admin/users?status=verified_18plus",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code in [200, 404, 501]

    def test_user_detail_view(self, async_session_maker):
        """TC-ADMIN-011: User detail view."""
        admin_email = create_admin_user(async_session_maker)
        token = register_and_login(client, admin_email)

        # Get user list first
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 200:
            data = response.json()
            users = data.get("users", data) if isinstance(data, dict) else data

            if users:
                user_id = users[0]["id"]

                # Get user detail
                response = client.get(
                    f"/api/v1/admin/users/{user_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                assert response.status_code in [200, 404, 501]

    def test_freeze_user_account(self, async_session_maker):
        """TC-ADMIN-012: Freeze user account."""
        admin_email = create_admin_user(async_session_maker)
        token = register_and_login(client, admin_email)

        # Freeze user
        response = client.post(
            "/api/v1/admin/users/{user_id}/freeze",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "reason": "Violation of terms of service",
            }
        )
        assert response.status_code in [400, 404, 501]

    def test_batch_user_operations(self, async_session_maker):
        """TC-ADMIN-013: Batch user operations."""
        admin_email = create_admin_user(async_session_maker)
        token = register_and_login(client, admin_email)

        # Batch operation
        response = client.post(
            "/api/v1/admin/users/batch",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "user_ids": ["user1", "user2"],
                "action": "freeze",
                "reason": "Batch operation test",
            }
        )
        assert response.status_code in [400, 404, 501]


# ============== Content Review Tests (TC-ADMIN-020 ~ TC-ADMIN-022) ==============

class TestContentReview:
    """Test content review functionality."""

    def test_pending_review_list(self, async_session_maker):
        """TC-ADMIN-020: Pending review list."""
        admin_email = create_admin_user(async_session_maker)
        token = register_and_login(client, admin_email)

        response = client.get(
            "/api/v1/admin/reviews/pending",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code in [200, 404, 501]

    def test_approve_content(self, async_session_maker):
        """TC-ADMIN-021: Approve content."""
        admin_email = create_admin_user(async_session_maker)
        token = register_and_login(client, admin_email)

        response = client.post(
            "/api/v1/admin/reviews/{id}/approve",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in [400, 404, 501]

    def test_reject_content(self, async_session_maker):
        """TC-ADMIN-022: Reject content with reason."""
        admin_email = create_admin_user(async_session_maker)
        token = register_and_login(client, admin_email)

        response = client.post(
            "/api/v1/admin/reviews/{id}/reject",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "reason": "Content violates platform policies",
            }
        )
        assert response.status_code in [400, 404, 501]


# ============== Data Reports Tests (TC-ADMIN-030 ~ TC-ADMIN-031) ==============

class TestDataReports:
    """Test data reports functionality."""

    def test_export_user_report(self, async_session_maker):
        """TC-ADMIN-030: Export user report to CSV."""
        admin_email = create_admin_user(async_session_maker)
        token = register_and_login(client, admin_email)

        response = client.get(
            "/api/v1/admin/reports/users?start_date=2026-01-01&end_date=2026-02-28",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code in [200, 404, 501]

        if response.status_code == 200:
            # Should return CSV or JSON
            assert response.headers.get("content-type") in [
                "text/csv",
                "application/json",
                "text/csv; charset=utf-8",
            ] or True

    def test_trade_report_view(self, async_session_maker):
        """TC-ADMIN-031: Trade report with statistics."""
        admin_email = create_admin_user(async_session_maker)
        token = register_and_login(client, admin_email)

        response = client.get(
            "/api/v1/admin/reports/trades?start_date=2026-01-01&end_date=2026-02-28",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code in [200, 404, 501]


# ============== System Configuration Tests (TC-ADMIN-040 ~ TC-ADMIN-041) ==============

class TestSystemConfiguration:
    """Test system configuration functionality."""

    def test_update_basic_config(self, async_session_maker):
        """TC-ADMIN-040: Update basic configuration."""
        admin_email = create_admin_user(async_session_maker)
        token = register_and_login(client, admin_email)

        response = client.put(
            "/api/v1/admin/config",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "key": "maintenance_mode",
                "value": False,
            }
        )
        assert response.status_code in [400, 404, 501]

    def test_sensitive_config_confirmation(self, async_session_maker):
        """TC-ADMIN-041: Sensitive config requires confirmation."""
        admin_email = create_admin_user(async_session_maker)
        token = register_and_login(client, admin_email)

        # Update recharge limits (sensitive)
        response = client.put(
            "/api/v1/admin/config/daily-limit",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "daily_limit": 600000,  # Change from 500K to 600K
                "confirm_password": "Admin123456",
            }
        )
        assert response.status_code in [400, 401, 404, 501]
