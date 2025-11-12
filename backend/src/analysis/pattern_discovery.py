"""Pattern discovery analysis for intent signal detection."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.code_violation import CodeViolation
from ..models.property import Property
from ..models.service_request import ServiceRequest
from ..utils.logging import get_logger

_logger = get_logger(component="pattern_discovery")


async def discover_roofing_patterns(session: AsyncSession) -> dict[str, Any]:
    """Discover patterns specific to roofing intent."""
    _logger.info("Discovering roofing patterns")
    
    # Roofing-related violations
    roofing_violations = await session.execute(
        select(func.count(CodeViolation.violation_id)).where(
            CodeViolation.prop_id.isnot(None),
            (
                CodeViolation.violation_type.ilike("%roof%") |
                CodeViolation.violation_description.ilike("%roof%")
            )
        )
    )
    roofing_violation_count = roofing_violations.scalar() or 0
    
    # Properties with roofing violations
    roofing_properties = await session.execute(
        select(func.count(func.distinct(CodeViolation.prop_id))).where(
            CodeViolation.prop_id.isnot(None),
            (
                CodeViolation.violation_type.ilike("%roof%") |
                CodeViolation.violation_description.ilike("%roof%")
            )
        )
    )
    roofing_property_count = roofing_properties.scalar() or 0
    
    # Properties aged 15-25 years (peak roofing replacement window)
    peak_age_properties = await session.execute(
        select(func.count(Property.prop_id)).where(
            Property.first_improvement_year.isnot(None),
            func.extract("year", func.current_date()) - Property.first_improvement_year.between(15, 25)
        )
    )
    peak_age_count = peak_age_properties.scalar() or 0
    
    patterns = {
        "roofing_violation_count": roofing_violation_count,
        "roofing_property_count": roofing_property_count,
        "peak_age_property_count": peak_age_count,
    }
    
    _logger.info("Roofing patterns discovered", **patterns)
    return patterns


async def discover_hvac_patterns(session: AsyncSession) -> dict[str, Any]:
    """Discover patterns specific to HVAC intent."""
    _logger.info("Discovering HVAC patterns")
    
    # HVAC-related 311 requests
    hvac_requests = await session.execute(
        select(func.count(ServiceRequest.request_id)).where(
            ServiceRequest.prop_id.isnot(None),
            (
                ServiceRequest.request_type.ilike("%hvac%") |
                ServiceRequest.request_type.ilike("%air%") |
                ServiceRequest.request_type.ilike("%heating%") |
                ServiceRequest.request_type.ilike("%cooling%")
            )
        )
    )
    hvac_request_count = hvac_requests.scalar() or 0
    
    # Properties with HVAC requests
    hvac_properties = await session.execute(
        select(func.count(func.distinct(ServiceRequest.prop_id))).where(
            ServiceRequest.prop_id.isnot(None),
            (
                ServiceRequest.request_type.ilike("%hvac%") |
                ServiceRequest.request_type.ilike("%air%") |
                ServiceRequest.request_type.ilike("%heating%") |
                ServiceRequest.request_type.ilike("%cooling%")
            )
        )
    )
    hvac_property_count = hvac_properties.scalar() or 0
    
    patterns = {
        "hvac_request_count": hvac_request_count,
        "hvac_property_count": hvac_property_count,
    }
    
    _logger.info("HVAC patterns discovered", **patterns)
    return patterns


async def discover_siding_patterns(session: AsyncSession) -> dict[str, Any]:
    """Discover patterns specific to siding intent."""
    _logger.info("Discovering siding patterns")
    
    # Siding-related violations
    siding_violations = await session.execute(
        select(func.count(CodeViolation.violation_id)).where(
            CodeViolation.prop_id.isnot(None),
            (
                CodeViolation.violation_type.ilike("%siding%") |
                CodeViolation.violation_description.ilike("%siding%") |
                CodeViolation.violation_type.ilike("%exterior%")
            )
        )
    )
    siding_violation_count = siding_violations.scalar() or 0
    
    patterns = {
        "siding_violation_count": siding_violation_count,
    }
    
    _logger.info("Siding patterns discovered", **patterns)
    return patterns


async def discover_all_patterns(session: AsyncSession) -> dict[str, Any]:
    """Discover all patterns across all trades."""
    _logger.info("Discovering all intent patterns")
    
    patterns = {
        "roofing": await discover_roofing_patterns(session),
        "hvac": await discover_hvac_patterns(session),
        "siding": await discover_siding_patterns(session),
    }
    
    _logger.success("All patterns discovered", patterns=patterns)
    return patterns

