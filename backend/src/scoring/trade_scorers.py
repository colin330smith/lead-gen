"""Trade-specific scoring algorithms."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.code_violation import CodeViolation
from ..models.property import Property
from ..models.service_request import ServiceRequest
from ..models.storm_event import StormEvent
from ..scoring.baseline_scorer import calculate_baseline_score
from ..services.property_lifecycle import get_trade_specific_lifecycle_score
from ..services.signal_decay import calculate_signal_strength
from ..utils.logging import get_logger

_logger = get_logger(component="trade_scorers")


async def calculate_roofing_score(
    session: AsyncSession,
    prop_id: int,
) -> dict[str, Any]:
    """Calculate roofing-specific intent score."""
    base_score = await calculate_baseline_score(session, prop_id, trade="roofing")
    
    # Roofing-specific adjustments
    property = await session.get(Property, prop_id)
    if not property:
        return base_score
    
    roofing_score = base_score["score"]
    components = base_score["components"].copy()
    
    # Check for roof-related violations
    roof_violations = await session.execute(
        select(CodeViolation).where(
            CodeViolation.prop_id == prop_id,
            (
                CodeViolation.violation_type.ilike("%roof%") |
                CodeViolation.violation_description.ilike("%roof%")
            )
        )
    )
    roof_violation_list = roof_violations.scalars().all()
    
    if roof_violation_list:
        # Boost for roof-specific violations
        for violation in roof_violation_list:
            if violation.violation_date:
                strength = calculate_signal_strength(0.3, violation.violation_date)
                roofing_score = min(1.0, roofing_score + strength)
        components["roof_violation_boost"] = min(0.3, len(roof_violation_list) * 0.1)
    
    # Check for hail events in ZIP (roofing trigger)
    if property.situs_zip:
        recent_storms = await session.execute(
            select(StormEvent).where(
                StormEvent.zip_code == property.situs_zip,
                StormEvent.event_type.ilike("%hail%"),
                StormEvent.event_date >= (datetime.now().date() - timedelta(days=90))
            )
        )
        storm_list = recent_storms.scalars().all()
        
        if storm_list:
            # Boost for recent hail
            max_magnitude = max((s.magnitude or 0) for s in storm_list)
            if max_magnitude > 1.0:  # Hail > 1 inch
                roofing_score = min(1.0, roofing_score + 0.4)
                components["hail_boost"] = 0.4
            elif max_magnitude > 0.5:
                roofing_score = min(1.0, roofing_score + 0.2)
                components["hail_boost"] = 0.2
    
    # Property age boost (15-25 years = peak roofing window)
    if property.first_improvement_year:
        age = datetime.now().year - property.first_improvement_year
        if 15 <= age <= 25:
            roofing_score = min(1.0, roofing_score + 0.2)
            components["age_window_boost"] = 0.2
    
    roofing_score = min(1.0, max(0.0, roofing_score))
    
    return {
        "score": round(roofing_score, 4),
        "components": components,
        "trade": "roofing",
    }


async def calculate_hvac_score(
    session: AsyncSession,
    prop_id: int,
) -> dict[str, Any]:
    """Calculate HVAC-specific intent score."""
    base_score = await calculate_baseline_score(session, prop_id, trade="hvac")
    
    hvac_score = base_score["score"]
    components = base_score["components"].copy()
    
    # Check for HVAC-related 311 requests
    hvac_requests = await session.execute(
        select(ServiceRequest).where(
            ServiceRequest.prop_id == prop_id,
            (
                ServiceRequest.request_type.ilike("%hvac%") |
                ServiceRequest.request_type.ilike("%air%") |
                ServiceRequest.request_type.ilike("%heating%") |
                ServiceRequest.request_type.ilike("%cooling%")
            )
        )
    )
    hvac_request_list = hvac_requests.scalars().all()
    
    if hvac_request_list:
        # Boost for HVAC-specific requests
        for request in hvac_request_list:
            if request.requested_date:
                strength = calculate_signal_strength(0.3, request.requested_date)
                hvac_score = min(1.0, hvac_score + strength)
        components["hvac_request_boost"] = min(0.3, len(hvac_request_list) * 0.1)
    
    # Property age boost (10-20 years = peak HVAC window)
    property = await session.get(Property, prop_id)
    if property and property.first_improvement_year:
        age = datetime.now().year - property.first_improvement_year
        if 10 <= age <= 20:
            hvac_score = min(1.0, hvac_score + 0.2)
            components["age_window_boost"] = 0.2
    
    # Seasonal boost (pre-summer/winter)
    from datetime import datetime
    month = datetime.now().month
    if month in [4, 5, 10, 11]:  # Pre-summer and pre-winter
        hvac_score = min(1.0, hvac_score + 0.1)
        components["seasonal_boost"] = 0.1
    
    hvac_score = min(1.0, max(0.0, hvac_score))
    
    return {
        "score": round(hvac_score, 4),
        "components": components,
        "trade": "hvac",
    }


async def calculate_siding_score(
    session: AsyncSession,
    prop_id: int,
) -> dict[str, Any]:
    """Calculate siding-specific intent score."""
    base_score = await calculate_baseline_score(session, prop_id, trade="siding")
    
    siding_score = base_score["score"]
    components = base_score["components"].copy()
    
    # Check for siding-related violations
    siding_violations = await session.execute(
        select(CodeViolation).where(
            CodeViolation.prop_id == prop_id,
            (
                CodeViolation.violation_type.ilike("%siding%") |
                CodeViolation.violation_description.ilike("%siding%") |
                CodeViolation.violation_type.ilike("%exterior%")
            )
        )
    )
    siding_violation_list = siding_violations.scalars().all()
    
    if siding_violation_list:
        for violation in siding_violation_list:
            if violation.violation_date:
                strength = calculate_signal_strength(0.3, violation.violation_date)
                siding_score = min(1.0, siding_score + strength)
        components["siding_violation_boost"] = min(0.3, len(siding_violation_list) * 0.1)
    
    # Check for wind events (siding trigger)
    property = await session.get(Property, prop_id)
    if property and property.situs_zip:
        recent_storms = await session.execute(
            select(StormEvent).where(
                StormEvent.zip_code == property.situs_zip,
                StormEvent.event_type.ilike("%wind%"),
                StormEvent.event_date >= (datetime.now().date() - timedelta(days=90))
            )
        )
        storm_list = recent_storms.scalars().all()
        
        if storm_list:
            max_wind = max((s.magnitude or 0) for s in storm_list)
            if max_wind > 60:  # Wind > 60 mph
                siding_score = min(1.0, siding_score + 0.3)
                components["wind_boost"] = 0.3
    
    siding_score = min(1.0, max(0.0, siding_score))
    
    return {
        "score": round(siding_score, 4),
        "components": components,
        "trade": "siding",
    }


async def calculate_electrical_score(
    session: AsyncSession,
    prop_id: int,
) -> dict[str, Any]:
    """Calculate electrical-specific intent score."""
    base_score = await calculate_baseline_score(session, prop_id, trade="electrical")
    
    electrical_score = base_score["score"]
    components = base_score["components"].copy()
    
    # Check for electrical-related 311 requests
    electrical_requests = await session.execute(
        select(ServiceRequest).where(
            ServiceRequest.prop_id == prop_id,
            (
                ServiceRequest.request_type.ilike("%electrical%") |
                ServiceRequest.request_type.ilike("%electric%") |
                ServiceRequest.request_type.ilike("%wiring%")
            )
        )
    )
    electrical_request_list = electrical_requests.scalars().all()
    
    if electrical_request_list:
        for request in electrical_request_list:
            if request.requested_date:
                strength = calculate_signal_strength(0.3, request.requested_date)
                electrical_score = min(1.0, electrical_score + strength)
        components["electrical_request_boost"] = min(0.3, len(electrical_request_list) * 0.1)
    
    # Property age boost (20-30 years = peak electrical window)
    property = await session.get(Property, prop_id)
    if property and property.first_improvement_year:
        age = datetime.now().year - property.first_improvement_year
        if 20 <= age <= 30:
            electrical_score = min(1.0, electrical_score + 0.2)
            components["age_window_boost"] = 0.2
    
    electrical_score = min(1.0, max(0.0, electrical_score))
    
    return {
        "score": round(electrical_score, 4),
        "components": components,
        "trade": "electrical",
    }

