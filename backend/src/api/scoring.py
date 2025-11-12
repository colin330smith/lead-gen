"""FastAPI endpoints for scoring system."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..scoring.scoring_service import batch_score_properties, score_property
from ..utils.logging import get_logger

_logger = get_logger(component="scoring_api")

router = APIRouter(prefix="/api/v1/scoring", tags=["scoring"])


@router.get("/property/{prop_id}")
async def get_property_score(
    prop_id: int,
    trade: str | None = Query(None, description="Trade-specific scoring (roofing, hvac, siding, electrical)"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get intent score for a single property."""
    try:
        result = await score_property(session, prop_id, trade=trade)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except Exception as e:
        _logger.exception("Error getting property score", prop_id=prop_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_score(
    prop_ids: list[int],
    trade: str | None = Query(None, description="Trade-specific scoring"),
    limit: int | None = Query(None, description="Maximum properties to score"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Score multiple properties in batch."""
    try:
        results = await batch_score_properties(session, prop_ids, trade=trade, limit=limit)
        return {
            "results": results,
            "total": len(results),
        }
    except Exception as e:
        _logger.exception("Error in batch scoring", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/high-intent")
async def get_high_intent_properties(
    min_score: float = Query(0.6, ge=0.0, le=1.0, description="Minimum intent score"),
    trade: str | None = Query(None, description="Trade filter"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get properties with high intent scores."""
    try:
        from ..models.lead_score import LeadScore
        
        query = select(LeadScore).where(LeadScore.intent_score >= min_score)
        
        if trade:
            query = query.where(LeadScore.trade == trade)
        
        query = query.order_by(LeadScore.intent_score.desc()).limit(limit)
        
        result = await session.execute(query)
        scores = result.scalars().all()
        
        return {
            "properties": [
                {
                    "prop_id": score.prop_id,
                    "trade": score.trade,
                    "intent_score": score.intent_score,
                    "signal_count": score.signal_count,
                    "calculated_at": score.calculated_at.isoformat(),
                }
                for score in scores
            ],
            "total": len(scores),
        }
    except Exception as e:
        _logger.exception("Error getting high intent properties", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

