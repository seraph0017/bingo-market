"""Wallet module tests.

Covers: TC-WALLET-001 ~ TC-WALLET-021 (Wallet & Recharge System)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models.user import User
from app.models.wallet import UserWallet, RechargeOrder, WalletTransaction


# Test client
client = TestClient(app)


# Database fixtures
@pytest.fixture(name="async_engine")
async def async_engine_fixture():
    """Create async engine for test database."""
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


# ============== Wallet Info Tests (TC-WALLET-001 ~ TC-WALLET-003) ==============

class TestWalletInfo:
    """Test wallet info retrieval."""

    def test_get_wallet_balance(self, async_session_maker):
        """TC-WALLET-001: Get wallet balance."""
        # Register and login
        token = register_and_login(client, "wallet1@example.com")

        # Get wallet info
        response = client.get(
            "/api/v1/wallet/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "daily_limit_remaining" in data
        assert "monthly_limit_remaining" in data
        # Vietnam limits: 500K daily, 5M monthly
        assert data["daily_limit_remaining"] == 500000
        assert data["monthly_limit_remaining"] == 5000000

    def test_wallet_privacy_toggle(self):
        """TC-WALLET-002: Privacy toggle (frontend feature)."""
        # This is primarily a frontend feature
        # Backend always returns actual balance
        token = register_and_login(client, "wallet2@example.com")
        response = client.get(
            "/api/v1/wallet/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        # Backend returns actual value, frontend handles display
        assert isinstance(response.json()["balance"], int)

    def test_limit_progress_display(self, async_session_maker):
        """TC-WALLET-003: Limit progress display."""
        token = register_and_login(client, "wallet3@example.com")

        response = client.get(
            "/api/v1/wallet/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Should include remaining limits
        assert "daily_limit_remaining" in data
        assert "monthly_limit_remaining" in data


# ============== Recharge Functionality Tests (TC-WALLET-010 ~ TC-WALLET-016) ==============

class TestRecharge:
    """Test recharge functionality."""

    def test_create_recharge_order_success(self, async_session_maker):
        """TC-WALLET-010: Normal recharge flow."""
        token = register_and_login(client, "recharge1@example.com")

        # Create recharge order
        response = client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount_vnd": 100000,  # 100K VND
                "payment_method": "momo",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "order_id" in data
        assert data["amount_vnd"] == 100000
        assert data["status"] == "pending"
        # Should have redirect URL for payment
        assert "redirect_url" in data

    def test_recharge_daily_limit_exceeded(self, async_session_maker):
        """TC-WALLET-011: Daily limit exceeded."""
        token = register_and_login(client, "recharge2@example.com")

        # Try to exceed daily limit (500K VND)
        response = client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount_vnd": 600000,  # Exceeds 500K daily limit
                "payment_method": "momo",
            }
        )
        assert response.status_code == 400
        assert "limit" in response.json().get("detail", "").lower()

    def test_recharge_monthly_limit_exceeded(self, async_session_maker):
        """TC-WALLET-012: Monthly limit exceeded."""
        token = register_and_login(client, "recharge3@example.com")

        # Try to exceed monthly limit (5M VND)
        # First, max out daily limit
        client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount_vnd": 500000,
                "payment_method": "momo",
            }
        )

        # Try another large recharge that would exceed monthly
        response = client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount_vnd": 4600000,  # Would exceed 5M monthly
                "payment_method": "momo",
            }
        )
        assert response.status_code == 400
        assert "limit" in response.json().get("detail", "").lower()

    def test_recharge_unverified_user_rejected(self, async_session_maker):
        """TC-WALLET-013: Unverified user recharge rejected."""
        # Register but don't verify
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "unverified@example.com",
                "password": "Test123456",
                "verification_code": "123456",
            }
        )

        login_resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "unverified@example.com",
                "password": "Test123456",
            }
        )
        token = login_resp.json().get("token")

        # Try to recharge
        response = client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount_vnd": 100000,
                "payment_method": "momo",
            }
        )
        assert response.status_code == 400
        assert "verification" in response.json().get("detail", "").lower() or \
               "verified" in response.json().get("detail", "").lower()

    def test_recharge_amount_boundaries(self, async_session_maker):
        """TC-WALLET-014: Recharge amount boundary values."""
        token = register_and_login(client, "recharge4@example.com")

        # Below minimum (10K VND)
        response = client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount_vnd": 9999,
                "payment_method": "momo",
            }
        )
        assert response.status_code == 400

        # Minimum (10K VND)
        response = client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount_vnd": 10000,
                "payment_method": "momo",
            }
        )
        assert response.status_code == 200

        # Maximum (500K VND per transaction due to daily limit)
        response = client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount_vnd": 500000,
                "payment_method": "momo",
            }
        )
        assert response.status_code == 200

        # Above maximum
        response = client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount_vnd": 500001,
                "payment_method": "momo",
            }
        )
        assert response.status_code == 400

    def test_recharge_idempotency(self, async_session_maker):
        """TC-WALLET-016: Recharge idempotency - prevent duplicate submissions."""
        token = register_and_login(client, "recharge5@example.com")

        # Rapid duplicate requests
        order_ids = set()
        for i in range(5):
            response = client.post(
                "/api/v1/wallet/recharge/orders",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "amount_vnd": 50000,
                    "payment_method": "momo",
                }
            )
            if response.status_code == 200:
                order_ids.add(response.json().get("order_id"))

        # Should only create one unique order (or be rate limited)
        # This depends on implementation
        assert len(order_ids) <= 1 or response.status_code == 429


# ============== Transaction Records Tests (TC-WALLET-020 ~ TC-WALLET-021) ==============

class TestTransactionRecords:
    """Test transaction record queries."""

    def test_get_recharge_records(self, async_session_maker):
        """TC-WALLET-020: Query recharge records."""
        token = register_and_login(client, "records1@example.com")

        # Create a recharge order first
        client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount_vnd": 100000,
                "payment_method": "momo",
            }
        )

        # Get recharge records
        response = client.get(
            "/api/v1/wallet/recharge/records",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert len(data["records"]) >= 1

    def test_get_transaction_history(self, async_session_maker):
        """TC-WALLET-021: Query transaction history."""
        token = register_and_login(client, "records2@example.com")

        # Get transaction history
        response = client.get(
            "/api/v1/wallet/transactions",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        # Should be a list
        assert isinstance(data["transactions"], list)

    def test_transaction_pagination(self, async_session_maker):
        """TC-WALLET-021: Transaction history pagination."""
        token = register_and_login(client, "records3@example.com")

        # Get first page
        response1 = client.get(
            "/api/v1/wallet/transactions?page=1&limit=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["page"] == 1
        assert data1["limit"] == 10

        # Get second page
        response2 = client.get(
            "/api/v1/wallet/transactions?page=2&limit=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["page"] == 2
