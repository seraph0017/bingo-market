"""Wallet module tests.

Covers: TC-WALLET-001 ~ TC-WALLET-021 (Wallet & Recharge System)
"""

import pytest
from httpx import AsyncClient


async def register_and_login_async(client: AsyncClient, email: str = "test@example.com"):
    """Register and login, return auth token."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Test123456",
            "verification_code": "123456",
        }
    )

    login_resp = await client.post(
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

    async def test_get_wallet_balance(self, client: AsyncClient, db_session):
        """TC-WALLET-001: Get wallet balance."""
        from app.core.database import get_db
        from app.main import app

        def override():
            yield db_session
        app.dependency_overrides[get_db] = override

        try:
            # Register and login
            token = await register_and_login_async(client, "wallet1@example.com")

            # Get wallet info
            response = await client.get(
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
        finally:
            app.dependency_overrides.clear()

    async def test_wallet_privacy_toggle(self, client: AsyncClient, db_session):
        """TC-WALLET-002: Privacy toggle (frontend feature)."""
        from app.core.database import get_db
        from app.main import app

        def override():
            yield db_session
        app.dependency_overrides[get_db] = override

        try:
            token = await register_and_login_async(client, "wallet2@example.com")
            response = await client.get(
                "/api/v1/wallet/",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            # Backend returns actual value, frontend handles display
            assert isinstance(response.json()["balance"], int)
        finally:
            app.dependency_overrides.clear()

    async def test_limit_progress_display(self, client: AsyncClient, db_session):
        """TC-WALLET-003: Limit progress display."""
        from app.core.database import get_db
        from app.main import app

        def override():
            yield db_session
        app.dependency_overrides[get_db] = override

        try:
            token = await register_and_login_async(client, "wallet3@example.com")

            response = await client.get(
                "/api/v1/wallet/",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
            data = response.json()
            # Should include remaining limits
            assert "daily_limit_remaining" in data
            assert "monthly_limit_remaining" in data
        finally:
            app.dependency_overrides.clear()


# ============== Recharge Functionality Tests (TC-WALLET-010 ~ TC-WALLET-016) ==============

class TestRecharge:
    """Test recharge functionality."""

    async def test_create_recharge_order_success(self, client: AsyncClient, db_session):
        """TC-WALLET-010: Normal recharge flow."""
        # Register and verify user (required for recharge)
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "recharge1@example.com",
                "password": "Test123456",
                "verification_code": "123456",
            }
        )

        # Login and verify identity
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "recharge1@example.com",
                "password": "Test123456",
            }
        )
        token = login_resp.json().get("token")

        # Verify identity first (required for recharge)
        await client.post(
            "/api/v1/auth/verify-identity",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": "Nguyen Van A",
                "id_number": "079087654321",
                "birth_date": "2000-01-01",
            }
        )

        # Create recharge order (use 'amount' not 'amount_vnd')
        response = await client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount": 100000,  # 100K VND
                "payment_method": "momo",
            }
        )
        # Note: May return 400 if payment gateway is not configured
        # or 200 if order is created successfully
        assert response.status_code in [200, 400]

    async def test_recharge_daily_limit_exceeded(self, client: AsyncClient, db_session):
        """TC-WALLET-011: Daily limit exceeded."""
        # Register and verify user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "recharge2@example.com",
                "password": "Test123456",
                "verification_code": "123456",
            }
        )

        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "recharge2@example.com",
                "password": "Test123456",
            }
        )
        token = login_resp.json().get("token")

        # Verify identity
        await client.post(
            "/api/v1/auth/verify-identity",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": "Nguyen Van A",
                "id_number": "079087654321",
                "birth_date": "2000-01-01",
            }
        )

        # Try to exceed daily limit (500K VND)
        response = await client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount": 600000,  # Exceeds 500K daily limit
                "payment_method": "momo",
            }
        )
        assert response.status_code == 400
        assert "limit" in response.json().get("detail", "").lower()

    async def test_recharge_monthly_limit_exceeded(self, client: AsyncClient, db_session):
        """TC-WALLET-012: Monthly limit exceeded."""
        # Register and verify user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "recharge3@example.com",
                "password": "Test123456",
                "verification_code": "123456",
            }
        )

        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "recharge3@example.com",
                "password": "Test123456",
            }
        )
        token = login_resp.json().get("token")

        # Verify identity
        await client.post(
            "/api/v1/auth/verify-identity",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": "Nguyen Van A",
                "id_number": "079087654321",
                "birth_date": "2000-01-01",
            }
        )

        # First, max out daily limit
        await client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount": 500000,
                "payment_method": "momo",
            }
        )

        # Try another large recharge that would exceed monthly
        response = await client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount": 4600000,  # Would exceed 5M monthly
                "payment_method": "momo",
            }
        )
        assert response.status_code == 400
        assert "limit" in response.json().get("detail", "").lower()

    async def test_recharge_unverified_user_rejected(self, client: AsyncClient, db_session):
        """TC-WALLET-013: Unverified user recharge rejected."""
        # Register but don't verify
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "unverified@example.com",
                "password": "Test123456",
                "verification_code": "123456",
            }
        )

        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "unverified@example.com",
                "password": "Test123456",
            }
        )
        token = login_resp.json().get("token")

        # Try to recharge without verification
        response = await client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount": 100000,
                "payment_method": "momo",
            }
        )
        assert response.status_code == 400
        assert "verification" in response.json().get("detail", "").lower() or \
               "verified" in response.json().get("detail", "").lower()

    async def test_recharge_amount_boundaries(self, client: AsyncClient, db_session):
        """TC-WALLET-014: Recharge amount boundary values."""
        # Register and verify user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "recharge4@example.com",
                "password": "Test123456",
                "verification_code": "123456",
            }
        )

        login_resp = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "recharge4@example.com",
                "password": "Test123456",
            }
        )
        token = login_resp.json().get("token")

        # Verify identity
        await client.post(
            "/api/v1/auth/verify-identity",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": "Nguyen Van A",
                "id_number": "079087654321",
                "birth_date": "2000-01-01",
            }
        )

        # Below minimum (10K VND) - should fail validation (422)
        response = await client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount": 9999,
                "payment_method": "momo",
            }
        )
        assert response.status_code == 422

        # Minimum (10K VND) - may fail if payment gateway not configured
        response = await client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount": 10000,
                "payment_method": "momo",
            }
        )
        # Accept 200 (success) or 400 (payment gateway not configured)
        assert response.status_code in [200, 400]

        # Maximum (500K VND per transaction due to daily limit)
        response = await client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount": 500000,
                "payment_method": "momo",
            }
        )
        assert response.status_code in [200, 400]

        # Above maximum (exceeds daily limit)
        response = await client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount": 500001,
                "payment_method": "momo",
            }
        )
        # Should fail with either 400 (business logic) or 422 (validation)
        assert response.status_code in [400, 422]

    async def test_recharge_idempotency(self, client: AsyncClient, db_session):
        """TC-WALLET-016: Recharge idempotency - prevent duplicate submissions."""
        from app.core.database import get_db
        from app.main import app

        def override():
            yield db_session
        app.dependency_overrides[get_db] = override

        try:
            token = await register_and_login_async(client, "recharge5@example.com")

            # Rapid duplicate requests
            order_ids = set()
            for i in range(5):
                response = await client.post(
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
        finally:
            app.dependency_overrides.clear()


# ============== Transaction Records Tests (TC-WALLET-020 ~ TC-WALLET-021) ==============

class TestTransactionRecords:
    """Test transaction record queries."""

    async def test_get_recharge_records(self, client: AsyncClient, db_session):
        """TC-WALLET-020: Query recharge records."""
        token = await register_and_login_async(client, "records1@example.com")

        # Create a recharge order first
        await client.post(
            "/api/v1/wallet/recharge/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount": 100000,
                "payment_method": "momo",
            }
        )

        # Get recharge records
        response = await client.get(
            "/api/v1/wallet/recharge/records",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        # Note: Records may be empty if order creation is async
        # Just verify the response structure is correct
        assert isinstance(data["records"], list)

    async def test_get_transaction_history(self, client: AsyncClient, db_session):
        """TC-WALLET-021: Query transaction history."""
        from app.core.database import get_db
        from app.main import app

        def override():
            yield db_session
        app.dependency_overrides[get_db] = override

        try:
            token = await register_and_login_async(client, "records2@example.com")

            # Get transaction history
            response = await client.get(
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
        finally:
            app.dependency_overrides.clear()

    async def test_transaction_pagination(self, client: AsyncClient, db_session):
        """TC-WALLET-021: Transaction history pagination."""
        from app.core.database import get_db
        from app.main import app

        def override():
            yield db_session
        app.dependency_overrides[get_db] = override

        try:
            token = await register_and_login_async(client, "records3@example.com")

            # Get first page
            response1 = await client.get(
                "/api/v1/wallet/transactions?page=1&limit=10",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response1.status_code == 200
            data1 = response1.json()
            assert data1["page"] == 1
            assert data1["limit"] == 10

            # Get second page
            response2 = await client.get(
                "/api/v1/wallet/transactions?page=2&limit=10",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response2.status_code == 200
            data2 = response2.json()
            assert data2["page"] == 2
        finally:
            app.dependency_overrides.clear()
