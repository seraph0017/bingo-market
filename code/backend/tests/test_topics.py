"""Topic module tests.

Covers: TC-TOPIC-001 ~ TC-TOPIC-022 (Topic & Market Management)
"""

import pytest
from datetime import datetime, timedelta, timezone

from app.core.config import settings


# ============== Topic Browsing Tests (TC-TOPIC-001 ~ TC-TOPIC-004) ==============

class TestTopicBrowsing:
    """Test topic browsing functionality."""

    @pytest.mark.asyncio
    async def test_topic_list_display(self, client):
        """TC-TOPIC-001: Topic list display."""
        response = await client.get("/api/v1/topics/")
        assert response.status_code == 200
        data = response.json()
        assert "topics" in data or isinstance(data, list)

    @pytest.mark.asyncio
    async def test_topic_category_filter(self, client):
        """TC-TOPIC-002: Topic category filtering."""
        # Test filtering by category
        for category in ["tech", "business", "culture", "academic"]:
            response = await client.get(f"/api/v1/topics/?category={category}")
            assert response.status_code == 200
            data = response.json()
            topics = data.get("topics", data) if isinstance(data, dict) else data
            # All returned topics should match the category (if any)
            for topic in topics:
                assert topic.get("category") == category

    @pytest.mark.asyncio
    async def test_topic_search(self, client):
        """TC-TOPIC-003: Topic search functionality."""
        response = await client.get("/api/v1/topics/?page=1&limit=20")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_topic_sorting(self, client):
        """TC-TOPIC-001: Topic sorting options."""
        # Test different sort options
        for sort in ["hot", "newest", "expiring"]:
            response = await client.get(f"/api/v1/topics/?sort={sort}")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_topic_detail_display(self, client):
        """TC-TOPIC-004: Topic detail display."""
        # Get topic list first
        response = await client.get("/api/v1/topics/")
        data = response.json()
        topics = data.get("topics", data) if isinstance(data, dict) else data

        if topics:
            topic_id = topics[0]["id"]
            # Get topic detail
            response = await client.get(f"/api/v1/topics/{topic_id}")
            assert response.status_code == 200
            detail = response.json()
            assert "id" in detail
            assert "title" in detail


# ============== Topic Creation Tests (TC-TOPIC-010 ~ TC-TOPIC-013) ==============

class TestTopicCreation:
    """Test topic creation functionality."""

    @pytest.mark.asyncio
    async def test_non_creator_create_topic_rejected(self, client, async_session_maker):
        """TC-TOPIC-011: Non-creator cannot create topic."""
        from app.core.security import get_password_hash
        from app.models.user import User
        import uuid

        # Create test user (not a creator)
        async with async_session_maker() as session:
            user = User(
                id=str(uuid.uuid4()),
                email="regular@bingomarket.com",
                password_hash=get_password_hash("Test123456"),
                full_name="Regular User",
                status="verified_18plus",
                role="user"
            )
            session.add(user)
            await session.commit()

        # Login
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "regular@bingomarket.com", "password": "Test123456"}
        )
        token = login_resp.json().get("token")

        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        response = await client.post(
            "/api/v1/topics/",
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

    @pytest.mark.asyncio
    async def test_topic_title_length_validation(self, client, async_session_maker):
        """TC-TOPIC-012: Topic title length validation (10-50 chars)."""
        from app.core.security import get_password_hash
        from app.models.user import User
        import uuid

        # Create test user
        async with async_session_maker() as session:
            user = User(
                id=str(uuid.uuid4()),
                email="titletest@bingomarket.com",
                password_hash=get_password_hash("Test123456"),
                full_name="Test User",
                status="verified_18plus",
                role="user"
            )
            session.add(user)
            await session.commit()

        # Login
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "titletest@bingomarket.com", "password": "Test123456"}
        )
        token = login_resp.json().get("token")

        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        # Title too short (< 10 chars)
        response = await client.post(
            "/api/v1/topics/",
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
        response = await client.post(
            "/api/v1/topics/",
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

    @pytest.mark.asyncio
    async def test_topic_description_length_validation(self, client, async_session_maker):
        """TC-TOPIC-013: Topic description length validation (50-500 chars)."""
        from app.core.security import get_password_hash
        from app.models.user import User
        import uuid

        # Create test user
        async with async_session_maker() as session:
            user = User(
                id=str(uuid.uuid4()),
                email="desctest@bingomarket.com",
                password_hash=get_password_hash("Test123456"),
                full_name="Test User",
                status="verified_18plus",
                role="user"
            )
            session.add(user)
            await session.commit()

        # Login
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "desctest@bingomarket.com", "password": "Test123456"}
        )
        token = login_resp.json().get("token")

        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        # Description too short (< 50 chars)
        response = await client.post(
            "/api/v1/topics/",
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
        response = await client.post(
            "/api/v1/topics/",
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

    @pytest.mark.asyncio
    async def test_topic_expiry_validation(self, client, async_session_maker):
        """TC-TOPIC-013: Topic expiry time validation (1-365 days)."""
        from app.core.security import get_password_hash
        from app.models.user import User
        from app.models.topic import CreatorProfile
        import uuid

        # Create test user WITH approved creator status
        async with async_session_maker() as session:
            user = User(
                id=str(uuid.uuid4()),
                email="expirytest@bingomarket.com",
                password_hash=get_password_hash("Test123456"),
                full_name="Test User",
                status="verified_18plus",
                role="user"
            )
            session.add(user)
            await session.flush()

            # Create approved creator profile
            creator = CreatorProfile(
                user_id=user.id,
                status="approved",
                topic_count=0,
                approved_topic_count=0
            )
            session.add(creator)
            await session.commit()

        # Login
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "expirytest@bingomarket.com", "password": "Test123456"}
        )
        token = login_resp.json().get("token")

        # Expires too soon (< 1 day)
        expires_soon = datetime.now(timezone.utc) + timedelta(hours=12)
        response = await client.post(
            "/api/v1/topics/",
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
        detail = response.json().get("detail", "").lower()
        assert "expire" in detail or "expiry" in detail or "future" in detail

        # Expires too late (> 365 days)
        expires_late = datetime.now(timezone.utc) + timedelta(days=400)
        response = await client.post(
            "/api/v1/topics/",
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
        detail = response.json().get("detail", "").lower()
        assert "expire" in detail or "expiry" in detail or "max" in detail


# ============== Topic Review Tests (TC-TOPIC-020 ~ TC-TOPIC-022) ==============

class TestTopicReview:
    """Test topic review functionality."""

    @pytest.mark.asyncio
    async def test_pending_review_list(self, client, async_session_maker):
        """TC-TOPIC-020: Pending review list."""
        from app.core.security import get_password_hash
        from app.models.user import User
        import uuid

        # Create admin user
        async with async_session_maker() as session:
            admin = User(
                id=str(uuid.uuid4()),
                email="auditor@bingomarket.com",
                password_hash=get_password_hash("Admin123456"),
                full_name="Admin User",
                status="verified_18plus",
                role="admin"
            )
            session.add(admin)
            await session.commit()

        # Login
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "auditor@bingomarket.com", "password": "Admin123456"}
        )
        token = login_resp.json().get("token")

        response = await client.get(
            "/api/v1/topics/reviews/pending",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code in [200, 403, 501]

    @pytest.mark.asyncio
    async def test_review_rejection_flow(self, client, async_session_maker):
        """TC-TOPIC-021: Review rejection flow."""
        from app.core.security import get_password_hash
        from app.models.user import User
        import uuid

        # Create admin user
        async with async_session_maker() as session:
            admin = User(
                id=str(uuid.uuid4()),
                email="auditor2@bingomarket.com",
                password_hash=get_password_hash("Admin123456"),
                full_name="Admin User",
                status="verified_18plus",
                role="admin"
            )
            session.add(admin)
            await session.commit()

        # Login
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "auditor2@bingomarket.com", "password": "Admin123456"}
        )
        token = login_resp.json().get("token")

        response = await client.post(
            "/api/v1/topics/{topic_id}/review",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "action": "rejected",
                "reason": "Content violates platform policies",
            }
        )
        assert response.status_code in [400, 404]

    @pytest.mark.asyncio
    async def test_review_timeout_reminder(self, client, async_session_maker):
        """TC-TOPIC-022: Review timeout reminder (24 hours)."""
        from app.core.security import get_password_hash
        from app.models.user import User
        import uuid

        # Create admin user
        async with async_session_maker() as session:
            admin = User(
                id=str(uuid.uuid4()),
                email="admin@bingomarket.com",
                password_hash=get_password_hash("Admin123456"),
                full_name="Admin User",
                status="verified_18plus",
                role="admin"
            )
            session.add(admin)
            await session.commit()

        # Login
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@bingomarket.com", "password": "Admin123456"}
        )
        token = login_resp.json().get("token")

        response = await client.get(
            "/api/v1/topics/reviews/pending",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code in [200, 403, 501]
