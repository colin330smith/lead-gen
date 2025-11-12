"""Interaction feature generation for multi-signal correlation."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.code_violation import CodeViolation
from ..models.property import Property
from ..models.service_request import ServiceRequest
from ..models.storm_event import StormEvent
from ..utils.logging import get_logger

_logger = get_logger(component="interaction_features")

# High-value signal combinations
HIGH_VALUE_COMBINATIONS = {
    "storm_violation": {
        "description": "Storm event + Code violation (roofing/siding)",
        "weight": 1.5,
    },
    "violation_request": {
        "description": "Code violation + 311 request (active problem)",
        "weight": 1.3,
    },
    "multiple_violations": {
        "description": "Multiple violations (ongoing issues)",
        "weight": 1.2,
    },
    "recent_signals": {
        "description": "Multiple recent signals (urgent need)",
        "weight": 1.4,
    },
}


async def calculate_interaction_features(
    session: AsyncSession,
    prop_id: int,
) -> dict[str, Any]:
    """
    Calculate interaction features for a property.
    
    Returns features that combine multiple signals for better prediction.
    """
    features = {}
    
    # Get all signals for this property
    violations = await session.execute(
        select(CodeViolation).where(CodeViolation.prop_id == prop_id)
    )
    violation_list = violations.scalars().all()
    
    requests = await session.execute(
        select(ServiceRequest).where(ServiceRequest.prop_id == prop_id)
    )
    request_list = requests.scalars().all()
    
    # Get property details
    property = await session.get(Property, prop_id)
    if not property:
        return features
    
    # Basic counts
    violation_count = len(violation_list)
    request_count = len(request_list)
    total_signals = violation_count + request_count
    
    features["violation_count"] = violation_count
    features["request_count"] = request_count
    features["total_signal_count"] = total_signals
    
    # Interaction: Storm + Violation (roofing/siding)
    # Check if property has recent violations and is in ZIP with recent storms
    if violation_count > 0:
        # Get ZIP code
        zip_code = property.situs_zip
        if zip_code:
            # Check for recent storms in this ZIP (last 90 days)
            recent_date = (datetime.now().date() - timedelta(days=90)).isoformat()
            storms = await session.execute(
                select(StormEvent).where(
                    StormEvent.zip_code == zip_code,
                    StormEvent.event_date >= recent_date
                )
            )
            storm_count = len(storms.scalars().all())
            features["storm_violation_interaction"] = 1.0 if (storm_count > 0 and violation_count > 0) else 0.0
            features["recent_storm_count"] = storm_count
        else:
            features["storm_violation_interaction"] = 0.0
            features["recent_storm_count"] = 0
    
    # Interaction: Violation + 311 Request (active problem)
    features["violation_request_interaction"] = 1.0 if (violation_count > 0 and request_count > 0) else 0.0
    
    # Interaction: Multiple violations (ongoing issues)
    features["multiple_violations"] = 1.0 if violation_count >= 2 else 0.0
    
    # Interaction: Recent signals (last 30 days)
    recent_date = (datetime.now().date() - timedelta(days=30)).isoformat()
    recent_violations = sum(1 for v in violation_list if v.violation_date and str(v.violation_date) >= recent_date)
    recent_requests = sum(1 for r in request_list if r.requested_date and str(r.requested_date) >= recent_date)
    features["recent_signal_count"] = recent_violations + recent_requests
    features["recent_signals_interaction"] = 1.0 if (recent_violations + recent_requests) >= 2 else 0.0
    
    # Property age interactions
    if property.first_improvement_year:
        current_year = datetime.now().year
        property_age = current_year - property.first_improvement_year
        features["property_age"] = property_age
        features["age_violation_interaction"] = property_age * violation_count
        features["age_request_interaction"] = property_age * request_count
    
    # Value interactions
    if property.market_value:
        features["value_violation_interaction"] = property.market_value * violation_count
        features["value_request_interaction"] = property.market_value * request_count
    
    return features


async def calculate_interaction_score(
    session: AsyncSession,
    prop_id: int,
) -> float:
    """
    Calculate overall interaction score for a property.
    
    Combines multiple signals with weights for high-value combinations.
    """
    features = await calculate_interaction_features(session, prop_id)
    
    score = 0.0
    
    # Base signal count
    score += features.get("total_signal_count", 0) * 0.1
    
    # High-value combinations
    if features.get("storm_violation_interaction", 0) > 0:
        score += HIGH_VALUE_COMBINATIONS["storm_violation"]["weight"]
    
    if features.get("violation_request_interaction", 0) > 0:
        score += HIGH_VALUE_COMBINATIONS["violation_request"]["weight"]
    
    if features.get("multiple_violations", 0) > 0:
        score += HIGH_VALUE_COMBINATIONS["multiple_violations"]["weight"]
    
    if features.get("recent_signals_interaction", 0) > 0:
        score += HIGH_VALUE_COMBINATIONS["recent_signals"]["weight"]
    
    return score

