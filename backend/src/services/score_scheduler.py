"""Scheduler for recalculating property scores."""

from __future__ import annotations

import asyncio
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.lead_score import LeadScore
from ..models.property import Property
from ..scoring.scoring_service import score_property
from ..utils.logging import get_logger

_logger = get_logger(component="score_scheduler")


async def recalculate_scores(
    session: AsyncSession,
    trade: str | None = None,
    limit: int | None = None,
    min_signals: int = 1,
) -> dict[str, int]:
    """
    Recalculate scores for properties with signals.
    
    Args:
        session: Database session
        trade: Optional trade-specific scoring
        limit: Maximum properties to score
        min_signals: Minimum signal count to include
    
    Returns:
        Statistics about recalculation
    """
    _logger.info("Starting score recalculation", trade=trade, limit=limit)
    
    # Find properties with signals
    from ..models.code_violation import CodeViolation
    from ..models.service_request import ServiceRequest
    from sqlalchemy import func
    
    # Properties with violations or requests
    query = select(Property.prop_id).where(
        Property.prop_id.in_(
            select(CodeViolation.prop_id).where(CodeViolation.prop_id.isnot(None))
        ) | Property.prop_id.in_(
            select(ServiceRequest.prop_id).where(ServiceRequest.prop_id.isnot(None))
        )
    )
    
    if limit:
        query = query.limit(limit)
    
    result = await session.execute(query)
    prop_ids = [row[0] for row in result.fetchall()]
    
    _logger.info("Properties to score", count=len(prop_ids))
    
    stats = {
        "total": len(prop_ids),
        "scored": 0,
        "failed": 0,
    }
    
    for prop_id in prop_ids:
        try:
            # Score the property
            score_result = await score_property(session, prop_id, trade=trade)
            
            if "error" in score_result:
                stats["failed"] += 1
                continue
            
            # Store score
            score_data = {
                "prop_id": prop_id,
                "trade": trade,
                "intent_score": score_result["score"],
                "baseline_score": score_result.get("components", {}).get("baseline_score"),
                "score_components": score_result.get("components", {}),
                "signal_count": score_result.get("features", {}).get("total_signal_count"),
                "violation_count": score_result.get("features", {}).get("violation_count", 0),
                "request_count": score_result.get("features", {}).get("request_count", 0),
                "calculated_at": datetime.utcnow(),
                "score_version": "v1.0",
            }
            
            stmt = insert(LeadScore).values(**score_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=["prop_id", "trade"] if trade else ["prop_id"],
                set_={
                    "intent_score": stmt.excluded.intent_score,
                    "baseline_score": stmt.excluded.baseline_score,
                    "score_components": stmt.excluded.score_components,
                    "signal_count": stmt.excluded.signal_count,
                    "violation_count": stmt.excluded.violation_count,
                    "request_count": stmt.excluded.request_count,
                    "calculated_at": stmt.excluded.calculated_at,
                }
            )
            await session.execute(stmt)
            
            stats["scored"] += 1
            
            if stats["scored"] % 100 == 0:
                await session.commit()
                _logger.info("Score recalculation progress", **stats)
        
        except Exception as e:
            _logger.exception("Error scoring property", prop_id=prop_id, error=str(e))
            stats["failed"] += 1
    
    await session.commit()
    _logger.success("Score recalculation complete", **stats)
    return stats

