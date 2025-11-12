"""Feature pipeline to calculate all features for a property."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.logging import get_logger
from .aggregated_features import calculate_aggregated_features
from .temporal_features import calculate_temporal_features
from ..services.interaction_features import calculate_interaction_features

_logger = get_logger(component="feature_pipeline")


async def calculate_all_features(
    session: AsyncSession,
    prop_id: int,
    reference_date: date | None = None,
) -> dict[str, Any]:
    """
    Calculate all features for a property.
    
    Combines:
    - Temporal features
    - Aggregated features
    - Interaction features
    """
    _logger.debug("Calculating all features", prop_id=prop_id)
    
    features = {}
    
    # Temporal features
    temporal = await calculate_temporal_features(session, prop_id, reference_date)
    features.update(temporal)
    
    # Aggregated features
    aggregated = await calculate_aggregated_features(session, prop_id)
    features.update(aggregated)
    
    # Interaction features
    interaction = await calculate_interaction_features(session, prop_id)
    features.update(interaction)
    
    return features

