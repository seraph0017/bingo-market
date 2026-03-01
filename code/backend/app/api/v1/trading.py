"""Trading API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas.topic import MarketPositionInfo
from app.services.trading import TradingService
from app.services.topic import TopicService
from app.core.database import get_db
from app.core.security import verify_token
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel


router = APIRouter()
security = HTTPBearer()


class BuySharesRequest(BaseModel):
    """Buy shares request."""

    outcome_index: int
    quantity: int


class SellSharesRequest(BaseModel):
    """Sell shares request."""

    outcome_index: int
    quantity: int


class TradeResponse(BaseModel):
    """Trade response."""

    topic_id: str
    outcome_index: int
    shares: int
    cost_or_payout: int
    action: str  # buy or sell


class QuoteResponse(BaseModel):
    """Quote response for buy preview."""

    cost: int
    current_price: float
    new_price: float
    slippage_percent: float
    quantity: int
    outcome_index: int


class SellQuoteResponse(BaseModel):
    """Quote response for sell preview."""

    proceeds: int
    current_price: float
    new_price: float
    slippage_percent: float
    quantity: int
    outcome_index: int


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Get current user ID from token."""
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload["sub"]


async def get_trading_service(db: AsyncSession = Depends(get_db)) -> TradingService:
    """Get trading service dependency."""
    return TradingService(db)


async def get_topic_service(db: AsyncSession = Depends(get_db)) -> TopicService:
    """Get topic service dependency."""
    return TopicService(db)


@router.post("/{topic_id}/buy", response_model=TradeResponse)
async def buy_shares(
    topic_id: str,
    data: BuySharesRequest,
    user_id: str = Depends(get_current_user_id),
    trading_service: TradingService = Depends(get_trading_service),
):
    """Buy shares in a prediction market."""
    try:
        cost, position = await trading_service.buy_shares(
            user_id=user_id,
            topic_id=topic_id,
            outcome_index=data.outcome_index,
            quantity=data.quantity,
        )

        return TradeResponse(
            topic_id=topic_id,
            outcome_index=data.outcome_index,
            shares=position.shares,
            cost_or_payout=cost,
            action="buy",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{topic_id}/sell", response_model=TradeResponse)
async def sell_shares(
    topic_id: str,
    data: SellSharesRequest,
    user_id: str = Depends(get_current_user_id),
    trading_service: TradingService = Depends(get_trading_service),
):
    """Sell shares in a prediction market."""
    try:
        payout, position = await trading_service.sell_shares(
            user_id=user_id,
            topic_id=topic_id,
            outcome_index=data.outcome_index,
            quantity=data.quantity,
        )

        return TradeResponse(
            topic_id=topic_id,
            outcome_index=data.outcome_index,
            shares=position.shares if position else 0,
            cost_or_payout=payout,
            action="sell",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{topic_id}/positions")
async def get_positions(
    topic_id: str,
    user_id: str = Depends(get_current_user_id),
    trading_service: TradingService = Depends(get_trading_service),
    topic_service: TopicService = Depends(get_topic_service),
):
    """Get user's positions in a topic."""
    topic = await topic_service.get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    positions = await trading_service.get_all_user_positions(user_id, topic_id)

    return {
        "positions": [
            {
                "outcome_index": p.outcome_index,
                "outcome_option": topic.outcome_options[p.outcome_index],
                "shares": p.shares,
                "avg_price": p.avg_price,
            }
            for p in positions
        ],
        "topic_title": topic.title,
    }


@router.get("/my-positions")
async def get_all_positions(
    user_id: str = Depends(get_current_user_id),
    trading_service: TradingService = Depends(get_trading_service),
    topic_service: TopicService = Depends(get_topic_service),
):
    """Get all user positions across all topics."""
    positions = await trading_service._get_all_positions(user_id)

    result = []
    for p in positions:
        topic = await topic_service.get_topic(p.topic_id)
        if topic:
            result.append(
                MarketPositionInfo(
                    topic_id=p.topic_id,
                    topic_title=topic.title,
                    outcome_index=p.outcome_index,
                    outcome_option=topic.outcome_options[p.outcome_index],
                    shares=p.shares,
                    avg_price=p.avg_price,
                )
            )

    return {"positions": result, "total": len(result)}


@router.get("/{topic_id}/quote")
async def get_quote(
    topic_id: str,
    outcome_index: int = Query(..., ge=0),
    quantity: int = Query(..., ge=1),
    user_id: str = Depends(get_current_user_id),
    trading_service: TradingService = Depends(get_trading_service),
):
    """Get price quote for buying shares."""
    try:
        quote = await trading_service.get_quote(topic_id, outcome_index, quantity)
        return QuoteResponse(
            cost=quote["cost"],
            current_price=quote["current_price"],
            new_price=quote["new_price"],
            slippage_percent=quote["slippage_percent"],
            quantity=quote["quantity"],
            outcome_index=quote["outcome_index"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{topic_id}/sell-quote")
async def get_sell_quote(
    topic_id: str,
    outcome_index: int = Query(..., ge=0),
    quantity: int = Query(..., ge=1),
    user_id: str = Depends(get_current_user_id),
    trading_service: TradingService = Depends(get_trading_service),
):
    """Get price quote for selling shares."""
    try:
        quote = await trading_service.get_sell_quote(topic_id, user_id, outcome_index, quantity)
        return SellQuoteResponse(
            proceeds=quote["proceeds"],
            current_price=quote["current_price"],
            new_price=quote["new_price"],
            slippage_percent=quote["slippage_percent"],
            quantity=quote["quantity"],
            outcome_index=quote["outcome_index"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
