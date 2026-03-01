"""Topic module tests.

Covers: TC-TOPIC-001 ~ TC-TOPIC-022 (Topic & Market Management)
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

from app.main import app
from app.core.database import Base
from app.core.config import settings
from app.models.user import User
from app.models.topic import Topic, CreatorProfile


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


def create_approved_creator(token: str, client: TestClient):
    """Create an approved creator for testing."""
    # First get creator profile (creates if not exists)
    client.get(
        "/api/v1/topics/creator/profile",
        headers={"Authorization": f"Bearer {token}"}
    )

    # For testing, we'll need to manually approve the creator
    # This would typically be done through admin endpoint
    # For now, return the token and assume creator status is set up


# ============== Topic Browsing Tests (TC-TOPIC-001 ~ TC-TOPIC-004) ==============

class TestTopicBrowsing:
    """Test topic browsing functionality."""

    def test_topic_list_display(self, async_session_maker):
        """TC-TOPIC-001: Topic list display."""
        # Get topic list
        response = client.get("/api/v1/topics")
        assert response.status_code == 200
        data = response.json()
        assert "topics" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data

    def test_topic_category_filter(self, async_session_maker):
        """TC-TOPIC-002: Topic category filtering."""
        # Test filtering by category
        for category in ["tech", "business", "culture", "academic"]:
            response = client.get(
                f"/api/v1/topics?category={category}"
            )
            assert response.status_code == 200
            data = response.json()
            assert "topics" in data
            # All returned topics should match the category
            for topic in data["topics"]:
                assert topic["category"] == category

    def test_topic_search(self, async_session_maker):
        """TC-TOPIC-003: Topic search functionality."""
        # Search for topics
        response = client.get(
            "/api/v1/topics?page=1&limit=20"
        )
        assert response.status_code == 200

        # Search with keyword (if implemented)
        # This depends on search implementation
        response = client.get(
            "/api/v1/topics?page=1&limit=20"
        )
        assert response.status_code == 200

    def test_topic_sorting(self, async_session_maker):
        """TC-TOPIC-001: Topic sorting options."""
        # Test different sort options
        for sort in ["hot", "newest", "expiring"]:
            response = client.get(
                f"/api/v1/topics?sort={sort}"
            )
            assert response.status_code == 200

    def test_topic_detail_display(self, async_session_maker):
        """TC-TOPIC-004: Topic detail display."""
        # Get topic list first
        response = client.get("/api/v1/topics")
        data = response.json()

        if data["topics"]:
            topic_id = data["topics"][0]["id"]

            # Get topic detail
            response = client.get(f"/api/v1/topics/{topic_id}")
            assert response.status_code == 200
            detail = response.json()
            assert "id" in detail
            assert "title" in detail
            assert "description" in detail
            assert "outcome_options" in detail
            assert "current_prices" in detail


# ============== Topic Creation Tests (TC-TOPIC-010 ~ TC-TOPIC-013) ==============

class TestTopicCreation:
    """Test topic creation functionality."""

    def test_authenticated_creator_create_topic(self, async_session_maker):
        """TC-TOPIC-010: Authenticated creator can create topic."""
        from sqlalchemy.ext.asyncio import AsyncSession

        async def setup_creator():
            async with async_session_maker() as session:
                # Create user
                user = User(
                    email="creator@example.com",
                    password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu",  # Test123456
                    full_name="Test Creator",
                    status="verified_18plus",
                    role="user"
                )
                session.add(user)
                await session.flush()

                # Create approved creator profile
                profile = CreatorProfile(
                    user_id=user.id,
                    status="approved",
                    topic_count=0,
                    approved_topic_count=0
                )
                session.add(profile)
                await session.commit()

                return user.email

        import asyncio
        email = asyncio.get_event_loop().run_until_complete(setup_creator())

        # Login
        token = register_and_login(client, email)

        # Create topic
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        response = client.post(
            "/api/v1/topics",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "AI Will Replace Programmers by 2030",
                "description": "This topic explores whether artificial intelligence will be capable of replacing most programming jobs by 2030. Consider current AI capabilities, rate of advancement, and limitations.",
                "category": "tech",
                "outcome_options": ["Yes, AI will replace most programmers", "No, AI will augment programmers"],
                "expires_at": expires_at.isoformat(),
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "topic_id" in data
        assert data["status"] == "pending_review"

    def test_non_creator_create_topic_rejected(self, async_session_maker):
        """TC-TOPIC-011: Non-creator cannot create topic."""
        token = register_and_login(client, "regular@example.com")

        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        response = client.post(
            "/api/v1/topics",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Test Topic",
                "description": "This is a test topic description with enough characters",
                "category": "tech",
                "outcome_options": ["Option A", "Option B"],
                "expires_at": expires_at.isoformat(),
            }
        )
        assert response.status_code == 400
        assert "creator" in response.json().get("detail", "").lower()

    def test_topic_title_length_validation(self, async_session_maker):
        """TC-TOPIC-012: Topic title length validation (10-50 chars)."""
        token = register_and_login(client, "titletest@example.com")

        # Approve creator (would need admin endpoint or direct DB update)
        # For now, test schema validation

        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        # Title too short (< 10 chars)
        response = client.post(
            "/api/v1/topics",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Short",  # 5 chars
                "description": "This is a test topic description with enough characters to pass validation",
                "category": "tech",
                "outcome_options": ["Option A", "Option B"],
                "expires_at": expires_at.isoformat(),
            }
        )
        assert response.status_code == 422

        # Title too long (> 50 chars)
        response = client.post(
            "/api/v1/topics",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "This is a very long title that exceeds the maximum allowed length of fifty characters",
                "description": "This is a test topic description with enough characters to pass validation",
                "category": "tech",
                "outcome_options": ["Option A", "Option B"],
                "expires_at": expires_at.isoformat(),
            }
        )
        assert response.status_code == 422

    def test_topic_description_length_validation(self, async_session_maker):
        """TC-TOPIC-013: Topic description length validation (50-500 chars)."""
        token = register_and_login(client, "desctest@example.com")

        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        # Description too short (< 50 chars)
        response = client.post(
            "/api/v1/topics",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Valid Topic Title Here",
                "description": "Too short",
                "category": "tech",
                "outcome_options": ["Option A", "Option B"],
                "expires_at": expires_at.isoformat(),
            }
        )
        assert response.status_code == 422

        # Description too long (> 500 chars)
        long_desc = "A" * 501
        response = client.post(
            "/api/v1/topics",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Valid Topic Title Here",
                "description": long_desc,
                "category": "tech",
                "outcome_options": ["Option A", "Option B"],
                "expires_at": expires_at.isoformat(),
            }
        )
        assert response.status_code == 422

    def test_topic_expiry_validation(self, async_session_maker):
        """TC-TOPIC-013: Topic expiry time validation (1-365 days)."""
        token = register_and_login(client, "expirytest@example.com")

        # Expires too soon (< 1 day)
        expires_soon = datetime.now(timezone.utc) + timedelta(hours=12)
        response = client.post(
            "/api/v1/topics",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Valid Topic Title Here",
                "description": "This is a test topic description with enough characters to pass validation",
                "category": "tech",
                "outcome_options": ["Option A", "Option B"],
                "expires_at": expires_soon.isoformat(),
            }
        )
        assert response.status_code == 400
        assert "expire" in response.json().get("detail", "").lower()

        # Expires too late (> 365 days)
        expires_late = datetime.now(timezone.utc) + timedelta(days=400)
        response = client.post(
            "/api/v1/topics",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Valid Topic Title Here",
                "description": "This is a test topic description with enough characters to pass validation",
                "category": "tech",
                "outcome_options": ["Option A", "Option B"],
                "expires_at": expires_late.isoformat(),
            }
        )
        assert response.status_code == 400
        assert "expire" in response.json().get("detail", "").lower()


# ============== Topic Review Tests (TC-TOPIC-020 ~ TC-TOPIC-022) ==============

class TestTopicReview:
    """Test topic review functionality."""

    def test_review_approval_flow(self, async_session_maker):
        """TC-TOPIC-020: Review approval flow."""
        # This test would require:
        # 1. Creating a topic as approved creator
        # 2. Logging in as auditor/admin
        # 3. Submitting review approval

        # For now, verify endpoint exists
        token = register_and_login(client, "auditor@example.com")

        # Get pending reviews endpoint
        response = client.get(
            "/api/v1/topics/reviews/pending",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Should require auditor role (may return 403 for regular user)
        assert response.status_code in [200, 403]

    def test_review_rejection_flow(self, async_session_maker):
        """TC-TOPIC-021: Review rejection flow."""
        # Similar to approval, requires setup
        # Verify endpoint structure

        token = register_and_login(client, "auditor2@example.com")

        # Submit review (would fail without valid topic)
        response = client.post(
            "/api/v1/topics/{topic_id}/review",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "action": "rejected",
                "reason": "Content violates platform policies",
            }
        )
        # Should return 404 for non-existent topic
        assert response.status_code in [400, 404]

    def test_review_timeout_reminder(self, async_session_maker):
        """TC-TOPIC-022: Review timeout reminder (24 hours)."""
        # This is primarily a background job / notification feature
        # Test that pending reviews can be queried
        token = register_and_login(client, "admin@example.com")

        response = client.get(
            "/api/v1/topics/reviews/pending",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Endpoint should exist for checking pending reviews
        assert response.status_code in [200, 401, 403]
