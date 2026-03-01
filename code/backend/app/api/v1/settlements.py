"""Settlements API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import get_db
from app.core.security import verify_token
from app.services.settlement import SettlementService
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel


router = APIRouter()
security = HTTPBearer()


class SubmitResultRequest(BaseModel):
    """Submit settlement result request."""

    winning_outcome_index: int


class ExecuteSettlementResponse(BaseModel):
    """Execute settlement response."""

    settlement_id: str
    status: str
    users_paid: int
    total_payout: int


class DisputeRequest(BaseModel):
    """Create dispute request."""

    reason: str
    evidence: dict | None = None


class ResolveDisputeRequest(BaseModel):
    """Resolve dispute request."""

    action: str  # upheld, rejected
    resolution: str


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Get current user ID from token."""
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload["sub"]


async def get_settlement_service(db: AsyncSession = Depends(get_db)) -> SettlementService:
    """Get settlement service dependency."""
    return SettlementService(db)


@router.get("/pending")
async def list_pending_settlements(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    settlement_service: SettlementService = Depends(get_settlement_service),
):
    """List pending settlements."""
    from app.models.settlement import MarketSettlement
    from sqlalchemy import select

    stmt = select(MarketSettlement).where(MarketSettlement.status == "pending")
    result = await db.execute(stmt)
    settlements = list(result.scalars().all())

    return {
        "settlements": [
            {
                "settlement_id": s.id,
                "market_id": s.market_id,
                "status": s.status,
                "total_pool": s.total_pool,
            }
            for s in settlements
        ],
        "total": len(settlements),
        "page": page,
        "limit": limit,
    }


@router.post("/{settlement_id}/result")
async def submit_result(
    settlement_id: str,
    data: SubmitResultRequest,
    user_id: str = Depends(get_current_user_id),
    settlement_service: SettlementService = Depends(get_settlement_service),
):
    """Submit settlement result."""
    try:
        settlement = await settlement_service.submit_result(
            settlement_id, data.winning_outcome_index, user_id
        )
        return {"settlement_id": settlement.id, "status": settlement.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{settlement_id}/execute", response_model=ExecuteSettlementResponse)
async def execute_settlement(
    settlement_id: str,
    user_id: str = Depends(get_current_user_id),
    settlement_service: SettlementService = Depends(get_settlement_service),
):
    """Execute settlement and pay out users."""
    from sqlalchemy import select, func
    from app.models.settlement import MarketSettlement, UserSettlement

    # Get settlement
    stmt = select(MarketSettlement).where(MarketSettlement.id == settlement_id)
    result = await settlement_service.db.execute(stmt)
    settlement = result.scalar_one_or_none()

    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")

    if settlement.status != "settling":
        raise HTTPException(status_code=400, detail="Settlement not ready for execution")

    # Calculate payouts if not done
    if not settlement.total_shares_winning:
        await settlement_service.calculate_payouts(settlement)

    # Execute payouts
    paid_count = await settlement_service.execute_payouts(settlement)

    # Calculate total payout
    payout_stmt = select(func.sum(UserSettlement.payout)).where(
        UserSettlement.settlement_id == settlement_id
    )
    payout_result = await settlement_service.db.execute(payout_stmt)
    total_payout = payout_result.scalar() or 0

    return ExecuteSettlementResponse(
        settlement_id=settlement_id,
        status=settlement.status,
        users_paid=paid_count,
        total_payout=total_payout,
    )


@router.get("/user")
async def get_user_settlements(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    settlement_service: SettlementService = Depends(get_settlement_service),
):
    """Get user's settlement history."""
    settlements, total = await settlement_service.get_user_settlements(user_id, page, limit)

    return {
        "settlements": [
            {
                "settlement_id": s.settlement_id,
                "payout": s.payout,
                "status": s.status,
                "paid_at": s.paid_at,
            }
            for s in settlements
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.post("/{settlement_id}/dispute")
async def create_dispute(
    settlement_id: str,
    data: DisputeRequest,
    user_id: str = Depends(get_current_user_id),
    settlement_service: SettlementService = Depends(get_settlement_service),
):
    """Create settlement dispute."""
    try:
        dispute = await settlement_service.create_dispute(
            settlement_id, user_id, data.reason, data.evidence
        )
        return {"dispute_id": dispute.id, "status": dispute.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/disputes/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: str,
    data: ResolveDisputeRequest,
    user_id: str = Depends(get_current_user_id),
    settlement_service: SettlementService = Depends(get_settlement_service),
):
    """Resolve settlement dispute."""
    try:
        dispute = await settlement_service.resolve_dispute(
            dispute_id, user_id, data.action, data.resolution
        )
        return {"dispute_id": dispute.id, "status": dispute.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
