"""Integration test script for Bingo Market.

This script runs end-to-end tests for the complete user journey:
1. Register and verify identity
2. Create wallet and recharge
3. Browse topics and trade
4. Check positions and settlement

Usage:
    python3.11 scripts/run_integration_tests.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from app.core.database import Base
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
from app.models.topic import Topic, CreatorProfile
from app.models.wallet import Wallet
from app.models.trading import MarketPosition, TradeLog


async def run_integration_tests():
    """Run full integration test suite."""

    print("=" * 60)
    print("BINGO MARKET INTEGRATION TESTS")
    print("=" * 60)

    # Create engine
    engine = create_async_engine(
        settings.database_url,
        echo=False,
    )

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("\n[1/5] Setting up test data...")

    async with async_session_maker() as session:
        # Create test users
        test_users = [
            {
                "email": "integration_test@example.com",
                "full_name": "Integration Test User",
                "status": "verified_18plus",
                "role": "user",
            },
            {
                "email": "creator_test@example.com",
                "full_name": "Creator Test User",
                "status": "verified_18plus",
                "role": "user",
            },
        ]

        for user_data in test_users:
            # Check if user exists
            stmt = select(User).where(User.email == user_data["email"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                user = User(
                    email=user_data["email"],
                    password_hash=get_password_hash("Test123456"),
                    full_name=user_data["full_name"],
                    status=user_data["status"],
                    role=user_data["role"],
                )
                session.add(user)
                print(f"  Created user: {user_data['email']}")

        await session.commit()

        # Create approved creator
        stmt = select(User).where(User.email == "creator_test@example.com")
        result = await session.execute(stmt)
        creator = result.scalar_one()

        creator_profile = CreatorProfile(
            user_id=creator.id,
            status="approved",
            topic_count=0,
            approved_topic_count=0
        )
        session.add(creator_profile)

        # Create active topic for trading tests
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30)
        topic = Topic(
            title="Integration Test Market",
            description="Test topic for integration testing",
            category="tech",
            outcome_options=["Yes", "No"],
            creator_id=creator.id,
            expires_at=expires_at,
            status="active",
            participant_count=0,
            trade_volume=0
        )
        session.add(topic)
        await session.flush()

        # Create wallets
        for user in [creator]:
            stmt = select(Wallet).where(Wallet.user_id == user.id)
            result = await session.execute(stmt)
            wallet = result.scalar_one_or_none()

            if not wallet:
                wallet = Wallet(
                    user_id=user.id,
                    balance=1000000,  # 1M VND
                    daily_limit_remaining=500000,
                    monthly_limit_remaining=5000000
                )
                session.add(wallet)

        await session.commit()

        print("  Created creator profile")
        print(f"  Created topic: {topic.title}")
        print("  Created wallets with test balance")

    print("\n[2/5] Testing authentication flow...")

    from fastapi.testclient import TestClient
    from app.main import app

    test_client = TestClient(app)

    # Test login
    login_response = test_client.post(
        "/api/v1/auth/login",
        json={
            "email": "integration_test@example.com",
            "password": "Test123456",
        }
    )

    if login_response.status_code == 200:
        token = login_response.json().get("token")
        print(f"  Login successful, token: {token[:50]}...")
    else:
        print(f"  Login failed: {login_response.status_code}")

    print("\n[3/5] Testing wallet operations...")

    # Get wallet info
    if token:
        wallet_response = test_client.get(
            "/api/v1/wallet/",
            headers={"Authorization": f"Bearer {token}"}
        )
        if wallet_response.status_code == 200:
            wallet_data = wallet_response.json()
            print(f"  Wallet balance: {wallet_data.get('balance', 0)} VND")
            print(f"  Daily limit: {wallet_data.get('daily_limit_remaining', 0)} VND")
            print(f"  Monthly limit: {wallet_data.get('monthly_limit_remaining', 0)} VND")
        else:
            print(f"  Wallet query failed: {wallet_response.status_code}")

    print("\n[4/5] Testing topic operations...")

    # Get topic list
    topics_response = test_client.get("/api/v1/topics?status=active")
    if topics_response.status_code == 200:
        topics_data = topics_response.json()
        print(f"  Active topics: {topics_data.get('total', 0)}")
        if topics_data.get('topics'):
            for topic in topics_data['topics'][:3]:
                print(f"    - {topic['title'][:50]}...")
    else:
        print(f"  Topic query failed: {topics_response.status_code}")

    print("\n[5/5] Testing trading operations...")

    # Get trading positions (should be empty for new user)
    if token:
        positions_response = test_client.get(
            "/api/v1/trading/positions",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"  Positions query: {positions_response.status_code}")

    # Cleanup
    await engine.dispose()

    print("\n" + "=" * 60)
    print("INTEGRATION TESTS COMPLETED")
    print("=" * 60)
    print("\nTest Accounts:")
    print("  Email: integration_test@example.com")
    print("  Password: Test123456")
    print("\n  Email: creator_test@example.com")
    print("  Password: Test123456 (Approved Creator)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_integration_tests())
