"""Model validation and performance testing framework."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.lead_score import LeadScore
from ..models.property import Property
from ..scoring.scoring_service import score_property
from ..utils.logging import get_logger

_logger = get_logger(component="model_validation")


async def validate_scoring_performance(
    session: AsyncSession,
    sample_size: int = 1000,
) -> dict[str, Any]:
    """
    Validate scoring system performance.
    
    Tests:
    - Scoring speed (target: 1k/sec)
    - Score distribution
    - Trade-specific scoring
    """
    _logger.info("Validating scoring performance", sample_size=sample_size)
    
    import time
    
    # Get sample properties with signals
    from ..models.code_violation import CodeViolation
    from sqlalchemy import select
    
    query = select(Property.prop_id).where(
        Property.prop_id.in_(
            select(CodeViolation.prop_id).where(CodeViolation.prop_id.isnot(None))
        )
    ).limit(sample_size)
    
    result = await session.execute(query)
    prop_ids = [row[0] for row in result.fetchall()]
    
    # Time scoring
    start_time = time.time()
    scores = []
    
    for prop_id in prop_ids:
        try:
            result = await score_property(session, prop_id)
            if "score" in result:
                scores.append(result["score"])
        except Exception as e:
            _logger.warning("Error scoring property", prop_id=prop_id, error=str(e))
    
    elapsed = time.time() - start_time
    rate = len(scores) / elapsed if elapsed > 0 else 0
    
    # Score distribution
    if scores:
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)
        
        # Count by score ranges
        high_intent = sum(1 for s in scores if s >= 0.7)
        medium_intent = sum(1 for s in scores if 0.4 <= s < 0.7)
        low_intent = sum(1 for s in scores if s < 0.4)
    else:
        avg_score = 0.0
        min_score = 0.0
        max_score = 0.0
        high_intent = 0
        medium_intent = 0
        low_intent = 0
    
    metrics = {
        "sample_size": len(prop_ids),
        "scored": len(scores),
        "elapsed_seconds": round(elapsed, 2),
        "scoring_rate": round(rate, 2),
        "target_rate": 1000.0,
        "meets_target": rate >= 1000.0,
        "avg_score": round(avg_score, 4),
        "min_score": round(min_score, 4),
        "max_score": round(max_score, 4),
        "high_intent_count": high_intent,
        "medium_intent_count": medium_intent,
        "low_intent_count": low_intent,
        "high_intent_pct": round((high_intent / len(scores) * 100) if scores else 0, 1),
    }
    
    _logger.success("Scoring performance validation complete", **metrics)
    return metrics


async def validate_score_distribution(session: AsyncSession) -> dict[str, Any]:
    """Validate score distribution across all scored properties."""
    _logger.info("Validating score distribution")
    
    # Get all scores
    query = select(
        func.count(LeadScore.prop_id).label("total"),
        func.avg(LeadScore.intent_score).label("avg_score"),
        func.min(LeadScore.intent_score).label("min_score"),
        func.max(LeadScore.intent_score).label("max_score"),
        func.percentile_cont(0.5).within_group(LeadScore.intent_score).label("median_score"),
        func.count(LeadScore.prop_id).filter(LeadScore.intent_score >= 0.7).label("high_intent"),
        func.count(LeadScore.prop_id).filter(LeadScore.intent_score >= 0.4).label("medium_intent"),
    )
    
    result = await session.execute(query)
    row = result.first()
    
    if row and row.total:
        distribution = {
            "total_scored": row.total,
            "avg_score": float(row.avg_score) if row.avg_score else 0.0,
            "median_score": float(row.median_score) if row.median_score else 0.0,
            "min_score": float(row.min_score) if row.min_score else 0.0,
            "max_score": float(row.max_score) if row.max_score else 0.0,
            "high_intent_count": row.high_intent or 0,
            "medium_intent_count": row.medium_intent or 0,
            "high_intent_pct": round((row.high_intent / row.total * 100) if row.total > 0 else 0, 1),
            "medium_intent_pct": round((row.medium_intent / row.total * 100) if row.total > 0 else 0, 1),
        }
    else:
        distribution = {
            "total_scored": 0,
            "message": "No scores found",
        }
    
    _logger.info("Score distribution", **distribution)
    return distribution

