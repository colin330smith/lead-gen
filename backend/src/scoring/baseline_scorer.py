"""Baseline rule-based scoring algorithm."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.property import Property
from ..features.feature_pipeline import calculate_all_features
from ..services.interaction_features import calculate_interaction_score
from ..services.property_lifecycle import (
    calculate_maintenance_urgency,
    get_trade_specific_lifecycle_score,
)
from ..services.signal_decay import calculate_signal_strength
from ..utils.logging import get_logger

_logger = get_logger(component="baseline_scorer")

# Scoring weights
SIGNAL_WEIGHTS = {
    "violation": 0.3,
    "311_request": 0.25,
    "storm_event": 0.2,
    "lifecycle": 0.15,
    "interaction": 0.1,
}


async def calculate_baseline_score(
    session: AsyncSession,
    prop_id: int,
    trade: str | None = None,
) -> dict[str, Any]:
    """
    Calculate baseline intent score for a property.
    
    Returns:
        Dictionary with score and component breakdown
    """
    # Get property
    property = await session.get(Property, prop_id)
    if not property:
        return {"score": 0.0, "components": {}}
    
    # Get all features
    features = await calculate_all_features(session, prop_id)
    
    score = 0.0
    components = {}
    
    # Signal-based scoring
    violation_score = 0.0
    if features.get("violation_count", 0) > 0:
        # Get recent violations with decay
        from ..models.code_violation import CodeViolation
        from sqlalchemy import select
        
        violations = await session.execute(
            select(CodeViolation).where(CodeViolation.prop_id == prop_id)
        )
        violation_list = violations.scalars().all()
        
        for violation in violation_list:
            if violation.violation_date:
                strength = calculate_signal_strength(1.0, violation.violation_date)
                violation_score += strength
        
        violation_score = min(1.0, violation_score / 3.0)  # Cap at 1.0, normalize
    
    request_score = 0.0
    if features.get("request_count", 0) > 0:
        from ..models.service_request import ServiceRequest
        from sqlalchemy import select
        
        requests = await session.execute(
            select(ServiceRequest).where(ServiceRequest.prop_id == prop_id)
        )
        request_list = requests.scalars().all()
        
        for request in request_list:
            if request.requested_date:
                strength = calculate_signal_strength(1.0, request.requested_date)
                request_score += strength
        
        request_score = min(1.0, request_score / 3.0)  # Cap at 1.0, normalize
    
    # Apply weights
    components["violation_score"] = violation_score
    components["request_score"] = request_score
    score += violation_score * SIGNAL_WEIGHTS["violation"]
    score += request_score * SIGNAL_WEIGHTS["311_request"]
    
    # Lifecycle scoring
    property_age = features.get("property_age")
    if property_age is not None:
        if trade:
            lifecycle_score = get_trade_specific_lifecycle_score(property_age, trade)
        else:
            lifecycle_score = calculate_maintenance_urgency(property_age)
        components["lifecycle_score"] = lifecycle_score
        score += lifecycle_score * SIGNAL_WEIGHTS["lifecycle"]
    else:
        components["lifecycle_score"] = 0.0
    
    # Interaction scoring
    interaction_score = await calculate_interaction_score(session, prop_id)
    interaction_score = min(1.0, interaction_score / 5.0)  # Normalize
    components["interaction_score"] = interaction_score
    score += interaction_score * SIGNAL_WEIGHTS["interaction"]
    
    # Recency boost
    if features.get("has_recent_violation", 0) or features.get("has_recent_request", 0):
        recency_boost = 0.1
        score = min(1.0, score + recency_boost)
        components["recency_boost"] = recency_boost
    else:
        components["recency_boost"] = 0.0
    
    # Normalize final score
    score = min(1.0, max(0.0, score))
    
    return {
        "score": round(score, 4),
        "components": components,
        "features": features,
    }

