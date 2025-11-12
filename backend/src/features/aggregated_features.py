"""Aggregated feature generation for properties."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.code_violation import CodeViolation
from ..models.property import Property
from ..models.service_request import ServiceRequest
from ..utils.logging import get_logger

_logger = get_logger(component="aggregated_features")


async def calculate_aggregated_features(
    session: AsyncSession,
    prop_id: int,
) -> dict[str, Any]:
    """
    Calculate aggregated features for a property.
    
    Features include:
    - ZIP code statistics
    - Property value percentiles
    - Property age percentiles
    - Signal frequency compared to ZIP average
    """
    features = {}
    
    # Get property
    property = await session.get(Property, prop_id)
    if not property:
        return features
    
    zip_code = property.situs_zip
    if not zip_code:
        return features
    
    # ZIP code statistics
    zip_stats = await session.execute(
        select(
            func.count(Property.prop_id).label("total_properties"),
            func.avg(Property.market_value).label("avg_value"),
            func.percentile_cont(0.5).within_group(Property.market_value).label("median_value"),
            func.min(Property.market_value).label("min_value"),
            func.max(Property.market_value).label("max_value"),
        ).where(Property.situs_zip == zip_code, Property.market_value.isnot(None))
    )
    stats = zip_stats.first()
    
    if stats and stats.total_properties:
        features["zip_total_properties"] = stats.total_properties
        features["zip_avg_market_value"] = float(stats.avg_value) if stats.avg_value else None
        features["zip_median_market_value"] = float(stats.median_value) if stats.median_value else None
        
        # Property value percentile
        if property.market_value and stats.median_value:
            if property.market_value >= stats.median_value:
                features["value_percentile"] = 0.5 + ((property.market_value - stats.median_value) / (stats.max_value - stats.median_value) * 0.5) if (stats.max_value - stats.median_value) > 0 else 0.5
            else:
                features["value_percentile"] = ((property.market_value - stats.min_value) / (stats.median_value - stats.min_value) * 0.5) if (stats.median_value - stats.min_value) > 0 else 0.0
        else:
            features["value_percentile"] = None
    
    # Property age statistics
    if property.first_improvement_year:
        current_year = datetime.now().year
        property_age = current_year - property.first_improvement_year
        
        age_stats = await session.execute(
            select(
                func.avg(func.extract("year", func.current_date()) - Property.first_improvement_year).label("avg_age"),
                func.percentile_cont(0.5).within_group(
                    func.extract("year", func.current_date()) - Property.first_improvement_year
                ).label("median_age"),
            ).where(
                Property.situs_zip == zip_code,
                Property.first_improvement_year.isnot(None)
            )
        )
        age_stat = age_stats.first()
        
        if age_stat and age_stat.avg_age:
            features["property_age"] = property_age
            features["zip_avg_property_age"] = float(age_stat.avg_age)
            features["zip_median_property_age"] = float(age_stat.median_age) if age_stat.median_age else None
            
            # Age percentile
            if age_stat.median_age:
                if property_age >= age_stat.median_age:
                    features["age_percentile"] = 0.5 + min(0.5, (property_age - age_stat.median_age) / (100 - age_stat.median_age))
                else:
                    features["age_percentile"] = max(0.0, property_age / age_stat.median_age * 0.5)
    
    # Signal frequency in ZIP
    zip_violations = await session.scalar(
        select(func.count(CodeViolation.violation_id)).where(
            CodeViolation.prop_id.in_(
                select(Property.prop_id).where(Property.situs_zip == zip_code)
            )
        )
    ) or 0
    
    zip_requests = await session.scalar(
        select(func.count(ServiceRequest.request_id)).where(
            ServiceRequest.prop_id.in_(
                select(Property.prop_id).where(Property.situs_zip == zip_code)
            )
        )
    ) or 0
    
    # Property's signals
    prop_violations = await session.scalar(
        select(func.count(CodeViolation.violation_id)).where(CodeViolation.prop_id == prop_id)
    ) or 0
    
    prop_requests = await session.scalar(
        select(func.count(ServiceRequest.request_id)).where(ServiceRequest.prop_id == prop_id)
    ) or 0
    
    # Signal frequency ratio
    zip_total_signals = zip_violations + zip_requests
    prop_total_signals = prop_violations + prop_requests
    
    if zip_total_signals > 0 and stats and stats.total_properties:
        zip_avg_signals = zip_total_signals / stats.total_properties
        features["zip_avg_signal_count"] = zip_avg_signals
        features["signal_frequency_ratio"] = prop_total_signals / zip_avg_signals if zip_avg_signals > 0 else 0.0
    else:
        features["zip_avg_signal_count"] = 0.0
        features["signal_frequency_ratio"] = 0.0
    
    return features

