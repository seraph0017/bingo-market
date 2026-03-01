"""Seed data script for creating test users."""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set correct env file path
os.environ['ENV_FILE'] = str(Path(__file__).parent.parent / '.env')

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.database import Base
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User


async def seed_test_users():
    """Create test users for development."""

    # Create engine
    engine = create_async_engine(
        settings.database_url,
        echo=True,
    )

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Test users data
    test_users = [
        {
            "email": "test@example.com",
            "phone": None,
            "password": "Test123456",
            "full_name": "Test User",
            "status": "verified_18plus",
            "role": "user",
        },
        {
            "email": "admin@bingomarket.com",
            "phone": None,
            "password": "Admin123456",
            "full_name": "Admin User",
            "status": "verified_18plus",
            "role": "admin",
        },
        {
            "email": None,
            "phone": "0901234567",
            "password": "Phone123456",
            "full_name": "Phone User",
            "status": "verified_18plus",
            "role": "user",
        },
    ]

    # Force recreate admin user
    force_recreate_admin = True

    async with async_session_maker() as session:
        for user_data in test_users:
            # Check if user already exists
            skip_check = force_recreate_admin and user_data["email"] == "admin@bingomarket.com"

            if not skip_check:
                stmt = select(User).where(
                    (User.email == user_data["email"]) |
                    (User.phone == user_data["phone"])
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    print(f"User {user_data['email'] or user_data['phone']} already exists - skipping")
                    continue

            # Create new user
            user = User(
                email=user_data["email"],
                phone=user_data["phone"],
                password_hash=get_password_hash(user_data["password"]),
                full_name=user_data["full_name"],
                status=user_data["status"],
                role=user_data["role"],
            )

            session.add(user)
            print(f"Created user: {user_data['email'] or user_data['phone']} (password: {user_data['password']})")

        await session.commit()

    await engine.dispose()
    print("\n✅ Seed data completed!")
    print("\n" + "=" * 50)
    print("TEST ACCOUNTS:")
    print("=" * 50)
    print("1. Email: test@example.com | Password: Test123456")
    print("2. Email: admin@bingomarket.com | Password: Admin123456 (Admin)")
    print("3. Phone: 0901234567 | Password: Phone123456")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed_test_users())
