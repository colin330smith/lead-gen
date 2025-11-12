"""Scoring service to calculate and manage property intent scores."""

from __future__ import annotations

from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.property import Property
from ..utils.logging import get_logger
from .baseline_scorer import calculate_baseline_score
from .trade_scorers import (
    calculate_electrical_score,
    calculate_hvac_score,
    calculate_roofing_score,
    calculate_siding_score,
)

_logger = get_logger(component="scoring_service")

TRADE_OPTIONS: list[str] = ["roofing", "hvac", "siding", "electrical"]


async def score_property(
    session: AsyncSession,
    prop_id: int,
    trade: str | None = None,
) -> dict[str, Any]:
    """
    Score a property for intent.
    
    Args:
        session: Database session
        prop_id: Property ID
        trade: Optional trade-specific scoring (roofing, hvac, siding, electrical)
    
    Returns:
        Dictionary with score, components, and metadata
    """
    # Validate property exists
    property = await session.get(Property, prop_id)
    if not property:
        return {
            "prop_id": prop_id,
            "score": 0.0,
            "error": "Property not found",
        }
    
    # Trade-specific scoring
    if trade and trade.lower() in TRADE_OPTIONS:
        trade_lower = trade.lower()
        if trade_lower == "roofing":
            result = await calculate_roofing_score(session, prop_id)
        elif trade_lower == "hvac":
            result = await calculate_hvac_score(session, prop_id)
        elif trade_lower == "siding":
            result = await calculate_siding_score(session, prop_id)
        elif trade_lower == "electrical":
            result = await calculate_electrical_score(session, prop_id)
        else:
            result = await calculate_baseline_score(session, prop_id)
    else:
        # Baseline scoring
        result = await calculate_baseline_score(session, prop_id)
    
    result["prop_id"] = prop_id
    result["address"] = property.situs_address
    result["zip_code"] = property.situs_zip
    result["market_value"] = property.market_value
    
    return result


async def batch_score_properties(
    session: AsyncSession,
    prop_ids: list[int],
    trade: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Score multiple properties in batch.
    
    Args:
        session: Database session
        prop_ids: List of property IDs
        trade: Optional trade-specific scoring
        limit: Maximum number of properties to score
    
    Returns:
        List of scoring results
    """
    if limit:
        prop_ids = prop_ids[:limit]
    
    _logger.info("Batch scoring properties", count=len(prop_ids), trade=trade)
    
    results = []
    for i, prop_id in enumerate(prop_ids):
        try:
            result = await score_property(session, prop_id, trade=trade)
            results.append(result)
            
            if (i + 1) % 100 == 0:
                _logger.info("Batch scoring progress", processed=i + 1, total=len(prop_ids))
        except Exception as e:
            _logger.exception("Error scoring property", prop_id=prop_id, error=str(e))
            results.append({
                "prop_id": prop_id,
                "score": 0.0,
                "error": str(e),
            })
    
    _logger.success("Batch scoring complete", total=len(results))
    return results

