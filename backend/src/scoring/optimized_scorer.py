"""Optimized scoring engine for production performance."""

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.lead_score import LeadScore
from ..models.property import Property
from ..scoring.scoring_service import score_property
from ..utils.logging import get_logger

_logger = get_logger(component="optimized_scorer")

# Batch size for optimized scoring
BATCH_SIZE = 1000
CONCURRENT_BATCHES = 4


async def batch_score_optimized(
    session: AsyncSession,
    prop_ids: list[int],
    trade: str | None = None,
) -> list[dict[str, Any]]:
    """
    Optimized batch scoring with concurrent processing.
    
    Target: 1,000+ properties/sec
    """
    _logger.info("Starting optimized batch scoring", count=len(prop_ids), trade=trade)
    
    # Split into batches
    batches = [prop_ids[i : i + BATCH_SIZE] for i in range(0, len(prop_ids), BATCH_SIZE)]
    
    # Process batches concurrently
    semaphore = asyncio.Semaphore(CONCURRENT_BATCHES)
    
    async def score_batch(batch: list[int]) -> list[dict[str, Any]]:
        async with semaphore:
            results = []
            for prop_id in batch:
                try:
                    result = await score_property(session, prop_id, trade=trade)
                    if "error" not in result:
                        results.append(result)
                except Exception as e:
                    _logger.warning("Error scoring property", prop_id=prop_id, error=str(e))
            return results
    
    # Process all batches
    batch_tasks = [score_batch(batch) for batch in batches]
    batch_results = await asyncio.gather(*batch_tasks)
    
    # Flatten results
    all_results = [result for batch_result in batch_results for result in batch_result]
    
    _logger.success("Optimized batch scoring complete", scored=len(all_results), total=len(prop_ids))
    return all_results


async def score_properties_with_signals(
    session: AsyncSession,
    trade: str | None = None,
    min_score: float = 0.0,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Score properties that have signals (violations or 311 requests).
    Optimized query to only score relevant properties.
    """
    from ..models.code_violation import CodeViolation
    from ..models.service_request import ServiceRequest
    
    # Get properties with signals
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
    
    _logger.info("Scoring properties with signals", count=len(prop_ids))
    
    # Use optimized batch scoring
    results = await batch_score_optimized(session, prop_ids, trade=trade)
    
    # Filter by min_score
    filtered = [r for r in results if r.get("score", 0) >= min_score]
    
    return filtered

