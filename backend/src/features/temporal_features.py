"""Temporal feature generation for properties."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.code_violation import CodeViolation
from ..models.property import Property
from ..models.service_request import ServiceRequest
from ..utils.logging import get_logger

_logger = get_logger(component="temporal_features")


async def calculate_temporal_features(
    session: AsyncSession,
    prop_id: int,
    reference_date: date | None = None,
) -> dict[str, Any]:
    """
    Calculate temporal features for a property.
    
    Features include:
    - Days since last signal
    - Signal counts in time windows (30/60/90 days)
    - Signal recency scores
    """
    if reference_date is None:
        reference_date = date.today()
    
    features = {}
    
    # Get all signals for this property
    violations = await session.execute(
        select(CodeViolation).where(
            CodeViolation.prop_id == prop_id,
            CodeViolation.violation_date.isnot(None)
        )
    )
    violation_list = violations.scalars().all()
    
    requests = await session.execute(
        select(ServiceRequest).where(
            ServiceRequest.prop_id == prop_id,
            ServiceRequest.requested_date.isnot(None)
        )
    )
    request_list = requests.scalars().all()
    
    # Days since last violation
    if violation_list:
        last_violation = max(v.violation_date for v in violation_list if v.violation_date)
        if last_violation:
            days_since_violation = (reference_date - last_violation).days
            features["days_since_last_violation"] = days_since_violation
            features["has_recent_violation"] = 1.0 if days_since_violation <= 30 else 0.0
    else:
        features["days_since_last_violation"] = None
        features["has_recent_violation"] = 0.0
    
    # Days since last 311 request
    if request_list:
        last_request = max(r.requested_date for r in request_list if r.requested_date)
        if last_request:
            days_since_request = (reference_date - last_request).days
            features["days_since_last_request"] = days_since_request
            features["has_recent_request"] = 1.0 if days_since_request <= 30 else 0.0
    else:
        features["days_since_last_request"] = None
        features["has_recent_request"] = 0.0
    
    # Signal counts in time windows
    date_30 = reference_date - timedelta(days=30)
    date_60 = reference_date - timedelta(days=60)
    date_90 = reference_date - timedelta(days=90)
    
    violations_30 = sum(1 for v in violation_list if v.violation_date and v.violation_date >= date_30)
    violations_60 = sum(1 for v in violation_list if v.violation_date and v.violation_date >= date_60)
    violations_90 = sum(1 for v in violation_list if v.violation_date and v.violation_date >= date_90)
    
    requests_30 = sum(1 for r in request_list if r.requested_date and r.requested_date >= date_30)
    requests_60 = sum(1 for r in request_list if r.requested_date and r.requested_date >= date_60)
    requests_90 = sum(1 for r in request_list if r.requested_date and r.requested_date >= date_90)
    
    features["violations_last_30_days"] = violations_30
    features["violations_last_60_days"] = violations_60
    features["violations_last_90_days"] = violations_90
    
    features["requests_last_30_days"] = requests_30
    features["requests_last_60_days"] = requests_60
    features["requests_last_90_days"] = requests_90
    
    features["total_signals_last_30_days"] = violations_30 + requests_30
    features["total_signals_last_60_days"] = violations_60 + requests_60
    features["total_signals_last_90_days"] = violations_90 + requests_90
    
    # Seasonal indicators
    month = reference_date.month
    features["month"] = month
    features["quarter"] = (month - 1) // 3 + 1
    features["is_summer"] = 1.0 if month in [6, 7, 8] else 0.0
    features["is_winter"] = 1.0 if month in [12, 1, 2] else 0.0
    features["is_spring"] = 1.0 if month in [3, 4, 5] else 0.0
    features["is_fall"] = 1.0 if month in [9, 10, 11] else 0.0
    
    return features

