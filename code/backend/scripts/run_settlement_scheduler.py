"""
Settlement Scheduler - Automatic settlement execution.

This script is designed to run as a Celery periodic task or cron job.
It scans for expired markets and automatically executes settlement.

Usage:
    python scripts/run_settlement_scheduler.py

Or as Celery beat task:
    @celery beat -c 1 --loglevel=info
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, update

from app.core.database import Base
from app.core.config import settings
from app.models.topic import Topic
from app.models.settlement import MarketSettlement, UserSettlement
from app.services.settlement import SettlementService
from app.services.wallet import WalletService


async def run_settlement_scheduler():
    """Run settlement scheduler."""

    print("=" * 60)
    print("SETTLEMENT SCHEDULER")
    print(f"Started at: {datetime.now().isoformat()}")
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

    async with async_session_maker() as session:
        # Step 1: Find expired markets that haven't been settled
        now = datetime.utcnow()
        stmt = select(Topic).where(
            Topic.status == "active",
            Topic.expires_at <= now,
        )
        result = await session.execute(stmt)
        expired_topics = list(result.scalars().all())

        print(f"\n[1/5] Found {len(expired_topics)} expired markets")

        # Step 2: Create settlement records for expired markets
        settlements_created = 0
        for topic in expired_topics:
            # Check if settlement already exists
            check_stmt = select(MarketSettlement).where(
                MarketSettlement.market_id == topic.id
            )
            check_result = await session.execute(check_stmt)
            existing = check_result.scalar_one_or_none()

            if not existing:
                settlement = MarketSettlement(
                    market_id=topic.id,
                    winning_outcome_index=-1,
                    total_pool=topic.trade_volume,
                    total_shares_winning=0,
                    status="pending",
                )
                session.add(settlement)
                settlements_created += 1
                print(f"  Created settlement for: {topic.title[:50]}...")

        await session.commit()
        print(f"  Created {settlements_created} new settlement records")

        # Step 3: Process settlements with submitted results
        stmt = select(MarketSettlement).where(
            MarketSettlement.status == "settling",
            MarketSettlement.winning_outcome_index >= 0,
        )
        result = await session.execute(stmt)
        ready_settlements = list(result.scalars().all())

        print(f"\n[2/5] Found {len(ready_settlements)} settlements ready for execution")

        # Step 4: Execute settlements
        settlement_service = SettlementService(session)
        executed_count = 0
        total_payout = 0

        for settlement in ready_settlements:
            try:
                print(f"  Processing settlement: {settlement.market_id}")

                # Calculate payouts if not done
                if not settlement.total_shares_winning:
                    await settlement_service.calculate_payouts(settlement)
                    await session.commit()
                    print(f"    Calculated payouts")

                # Execute payouts
                paid_count = await settlement_service.execute_payouts(settlement)
                await session.commit()

                executed_count += 1
                print(f"    Paid {paid_count} users")

            except Exception as e:
                print(f"    ERROR: {e}")
                await session.rollback()

        print(f"\n[3/5] Executed {executed_count} settlements")

        # Step 5: Summary
        print("\n" + "=" * 60)
        print("SETTLEMENT SCHEDULER SUMMARY")
        print("=" * 60)
        print(f"Expired markets found: {len(expired_topics)}")
        print(f"Settlements created: {settlements_created}")
        print(f"Settlements executed: {executed_count}")
        print(f"Total payouts: {total_payout}")
        print(f"Completed at: {datetime.now().isoformat()}")
        print("=" * 60)

    await engine.dispose()

    return {
        "expired_markets": len(expired_topics),
        "settlements_created": settlements_created,
        "settlements_executed": executed_count,
    }


if __name__ == "__main__":
    result = asyncio.run(run_settlement_scheduler())

    # Exit with appropriate code
    if result["settlements_executed"] > 0:
        print("\n✅ Settlement scheduler completed successfully")
        sys.exit(0)
    else:
        print("\nℹ️  No settlements to process")
        sys.exit(0)
