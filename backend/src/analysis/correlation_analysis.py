"""Multi-signal correlation analysis for intent detection."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.code_violation import CodeViolation
from ..models.property import Property
from ..models.service_request import ServiceRequest
from ..models.storm_event import StormEvent
from ..utils.logging import get_logger

_logger = get_logger(component="correlation_analysis")


async def calculate_signal_correlations(session: AsyncSession) -> dict[str, Any]:
    """Calculate correlations between different signal types."""
    _logger.info("Calculating signal correlations")
    
    # Count properties with each signal type
    violation_count = await session.scalar(
        select(func.count(func.distinct(CodeViolation.prop_id))).where(
            CodeViolation.prop_id.isnot(None)
        )
    ) or 0
    
    request_count = await session.scalar(
        select(func.count(func.distinct(ServiceRequest.prop_id))).where(
            ServiceRequest.prop_id.isnot(None)
        )
    ) or 0
    
    # Count properties with multiple signal types
    violation_and_request = await session.scalar(
        select(func.count(func.distinct(CodeViolation.prop_id))).select_from(
            CodeViolation
        ).join(
            ServiceRequest,
            CodeViolation.prop_id == ServiceRequest.prop_id
        ).where(
            CodeViolation.prop_id.isnot(None),
            ServiceRequest.prop_id.isnot(None)
        )
    ) or 0
    
    # Calculate correlation metrics
    total_properties = await session.scalar(select(func.count(Property.prop_id))) or 1
    
    correlations = {
        "violation_count": violation_count,
        "request_count": request_count,
        "violation_and_request": violation_and_request,
        "violation_rate": violation_count / total_properties if total_properties > 0 else 0,
        "request_rate": request_count / total_properties if total_properties > 0 else 0,
        "multi_signal_rate": violation_and_request / total_properties if total_properties > 0 else 0,
    }
    
    # Calculate conditional probabilities
    if violation_count > 0:
        correlations["request_given_violation"] = violation_and_request / violation_count
    else:
        correlations["request_given_violation"] = 0.0
    
    if request_count > 0:
        correlations["violation_given_request"] = violation_and_request / request_count
    else:
        correlations["violation_given_request"] = 0.0
    
    _logger.info("Signal correlations calculated", **correlations)
    return correlations


async def find_high_correlation_properties(
    session: AsyncSession,
    min_signals: int = 2,
) -> list[dict[str, Any]]:
    """Find properties with multiple signal types (high correlation)."""
    _logger.info("Finding high correlation properties", min_signals=min_signals)
    
    # Properties with violations
    violation_props = select(CodeViolation.prop_id).where(
        CodeViolation.prop_id.isnot(None)
    ).distinct()
    
    # Properties with 311 requests
    request_props = select(ServiceRequest.prop_id).where(
        ServiceRequest.prop_id.isnot(None)
    ).distinct()
    
    # Properties with both
    query = select(
        Property.prop_id,
        Property.situs_address,
        Property.situs_zip,
        Property.market_value,
        func.count(func.distinct(CodeViolation.violation_id)).label("violation_count"),
        func.count(func.distinct(ServiceRequest.request_id)).label("request_count"),
    ).select_from(
        Property
    ).outerjoin(
        CodeViolation, Property.prop_id == CodeViolation.prop_id
    ).outerjoin(
        ServiceRequest, Property.prop_id == ServiceRequest.prop_id
    ).group_by(
        Property.prop_id
    ).having(
        func.count(func.distinct(CodeViolation.violation_id)) +
        func.count(func.distinct(ServiceRequest.request_id)) >= min_signals
    ).limit(1000)
    
    result = await session.execute(query)
    properties = []
    
    for row in result.fetchall():
        properties.append({
            "prop_id": row.prop_id,
            "address": row.situs_address,
            "zip_code": row.situs_zip,
            "market_value": row.market_value,
            "violation_count": row.violation_count or 0,
            "request_count": row.request_count or 0,
            "total_signals": (row.violation_count or 0) + (row.request_count or 0),
        })
    
    _logger.info("High correlation properties found", count=len(properties))
    return properties

